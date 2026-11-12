from __future__ import annotations

import asyncio
import json
from collections.abc import Callable
from typing import Any

import httpx
import pytest

import iaai_api

KEY = "test-key-1234567890"


def car(car_id: str) -> dict[str, Any]:
    source = car_id.split(":", 1)[0]
    return {"id": car_id, "market": "us", "source": source, "title": "car", "price": {"amount": "1.00"}}


def page(ids: list[str], next_cursor: str | None = None, count: int | None = None) -> dict[str, Any]:
    return {"items": [car(i) for i in ids], "next_cursor": next_cursor, "count": count}


class Recorder:
    """Replays queued JSON bodies and records the requests."""

    def __init__(self, *bodies: Any) -> None:
        self.bodies = list(bodies)
        self.requests: list[httpx.Request] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        return httpx.Response(200, json=self.bodies.pop(0))

    def params(self, index: int = -1) -> dict[str, str]:
        return dict(self.requests[index].url.params)


def client(recorder: Callable[[httpx.Request], httpx.Response]) -> iaai_api.Client:
    http = httpx.Client(transport=httpx.MockTransport(recorder))
    return iaai_api.Client(KEY, http_client=http, max_retries=0)


def test_constants() -> None:
    assert iaai_api.MARKET == "us"
    assert iaai_api.SOURCE == "iaai"
    assert iaai_api.SHARED_MARKET is True
    assert iaai_api.__version__ == "0.1.1"


def test_cars_presets_the_market() -> None:
    rec = Recorder(page(["iaai:1", "iaai:2"], count=2))
    with client(rec) as api:
        result = api.cars(brand="Toyota", year_min=2020, limit=2)
    assert [c["id"] for c in result["items"]] == ["iaai:1", "iaai:2"]
    assert rec.requests[0].url.path == "/v1/cars"
    assert rec.params() == {"market": "us", "brand": "Toyota", "year_min": "2020", "limit": "2"}
    assert rec.requests[0].headers["x-api-key"] == KEY


def test_unknown_filter_is_rejected() -> None:
    with client(Recorder()) as api, pytest.raises(TypeError):
        api.cars(market="kr")  # type: ignore[call-arg]


@pytest.mark.parametrize(
    ("listing", "path"),
    [
        ("45551597", "/v1/cars/iaai:45551597"),
        (45551597, "/v1/cars/iaai:45551597"),
        ("iaai:45551597", "/v1/cars/iaai:45551597"),
    ],
)
def test_car_accepts_number_or_id(listing: str | int, path: str) -> None:
    rec = Recorder(car("iaai:45551597"))
    with client(rec) as api:
        assert api.car(listing)["id"] == "iaai:45551597"
    assert rec.requests[0].url.path == path


@pytest.mark.parametrize("bad", ["", "  ", "other:123", "iaai:"])
def test_car_id_rejects_foreign_ids(bad: str) -> None:
    with pytest.raises(ValueError, match=r"\S"):
        iaai_api.car_id(bad)


def test_brands_models_and_status() -> None:
    markets = {
        "items": [
            {"market": "kr", "source": "encar", "active_cars": 1},
            {"market": "cn", "source": "che168", "active_cars": 2},
            {"market": "us", "source": "copart+iaai", "active_cars": 3},
        ]
    }
    rec = Recorder([{"name": "Toyota", "count": 5}], [{"name": "Camry", "count": 2}], markets)
    with client(rec) as api:
        assert api.brands()[0]["name"] == "Toyota"
        assert rec.params(0) == {"market": "us"}
        assert api.models("Toyota")[0]["count"] == 2
        assert rec.params(1) == {"market": "us", "brand": "Toyota"}
        assert api.status()["market"] == "us"


def test_raw_is_typed_view() -> None:
    record: Any = {"id": "iaai:45551597", "raw": {"source_values": {"brand": "x"}}}
    assert iaai_api.raw(record).get("source_values") == {"brand": "x"}
    assert iaai_api.raw({"id": "iaai:45551597"}) == {}  # type: ignore[typeddict-item]


def test_cars_keeps_only_this_auction() -> None:
    rec = Recorder(page(["iaai:1", "other:2", "iaai:3"], next_cursor="c2", count=3))
    with client(rec) as api:
        result = api.cars(limit=3)
    assert [c["id"] for c in result["items"]] == ["iaai:1", "iaai:3"]
    assert result["next_cursor"] == "c2"
    assert result["count"] is None


def test_iter_cars_collects_max_items_across_pages() -> None:
    rec = Recorder(
        page(["other:1", "iaai:2"], next_cursor="c2"),
        page(["other:3", "other:4"], next_cursor="c3"),
        page(["iaai:5", "iaai:6"], next_cursor="c4"),
    )
    with client(rec) as api:
        ids = [c["id"] for c in api.iter_cars(max_items=2, limit=2)]
    assert ids == ["iaai:2", "iaai:5"]
    assert len(rec.requests) == 3
    assert all(r.url.params["market"] == "us" for r in rec.requests)


def test_iter_cars_zero_items_makes_no_request() -> None:
    rec = Recorder()
    with client(rec) as api:
        assert list(api.iter_cars(max_items=0)) == []
    assert rec.requests == []


def test_changes_keep_only_this_auction() -> None:
    feed = {
        "items": [
            {"id": 1, "car_id": "iaai:1", "type": "added"},
            {"id": 2, "car_id": "other:2", "type": "added"},
        ],
        "next_cursor": None,
    }
    rec = Recorder(feed, feed)
    with client(rec) as api:
        assert [c["car_id"] for c in api.changes("2026-11-01T00:00:00Z")["items"]] == ["iaai:1"]
        assert [c["id"] for c in api.iter_changes("2026-11-01T00:00:00Z", max_items=5)] == [1]


def test_live_keeps_only_this_auction() -> None:
    rec = Recorder([car("iaai:1"), car("other:2")])
    with client(rec) as api:
        lots = api.live(make="Toyota", page=1)
    assert [c["id"] for c in lots] == ["iaai:1"]
    assert rec.requests[0].url.path == "/v1/us/live"
    assert rec.params() == {"make": "Toyota", "page": "1"}


def test_async_client() -> None:
    rec = Recorder(page(["iaai:1"]), car("iaai:45551597"), page(["iaai:1"]))

    async def run() -> list[str]:
        http = httpx.AsyncClient(transport=httpx.MockTransport(rec))
        async with iaai_api.AsyncClient(KEY, http_client=http, max_retries=0) as api:
            first = await api.cars(limit=1)
            one = await api.car("45551597")
            more = [c["id"] async for c in api.iter_cars(max_items=1, limit=1)]
        await http.aclose()
        return [first["items"][0]["id"], one["id"], *more]

    assert asyncio.run(run()) == ["iaai:1", "iaai:45551597", "iaai:1"]
    assert all(r.url.params.get("market") in (None, "us") for r in rec.requests)


def test_errors_are_the_apiauto_ones() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        body = {"error": {"code": "not_found", "message": "no such car"}}
        return httpx.Response(404, content=json.dumps(body), headers={"content-type": "application/json"})

    with client(handler) as api, pytest.raises(iaai_api.NotFoundError):
        api.car("1")
