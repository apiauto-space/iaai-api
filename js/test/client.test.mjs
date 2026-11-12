// Unit tests against the compiled package (run `npm run build` first). fetch is mocked.
import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { IaaiApi, MARKET, NotFoundError, SHARED_MARKET, SOURCE, VERSION, carId, raw } from "../dist/index.js";

const KEY = "test-key-0123456789abcdef";

/** A fetch that answers from a queue of JSON bodies (or `{ status, body }`) and records URLs. */
function mockFetch(queue) {
  const urls = [];
  const fetch = async (url) => {
    urls.push(new URL(url));
    const next = queue.shift();
    if (next === undefined) throw new Error(`unexpected request to ${url}`);
    const { status = 200, body = next } = next && next.__status ? { status: next.__status, body: next.body } : {};
    return new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } });
  };
  return { fetch, urls };
}

function setup(...queue) {
  const { fetch, urls } = mockFetch(queue);
  return { api: new IaaiApi({ apiKey: KEY, fetch, maxRetries: 0 }), urls };
}

const car = (id) => ({ id, market: "us", source: id.split(":")[0], title: `car ${id}`, raw: {} });
const page = (ids, next_cursor = null, count = null) => ({ items: ids.map(car), next_cursor, count });
const params = (url) => Object.fromEntries(url.searchParams);

describe("constants", () => {
  it("preset the market and source", () => {
    assert.equal(MARKET, "us");
    assert.equal(SOURCE, "iaai");
    assert.equal(SHARED_MARKET, true);
    assert.equal(VERSION, "0.1.1");
  });
});

describe("cars", () => {
  it("sends market=us with the filters", async () => {
    const { api, urls } = setup(page(["iaai:1"], null, 1));
    const result = await api.cars({ brand: "Toyota", year_min: 2020, limit: 1 });
    assert.deepEqual(
      result.items.map((c) => c.id),
      ["iaai:1"],
    );
    assert.equal(urls[0].pathname, "/v1/cars");
    assert.deepEqual(params(urls[0]), { market: "us", brand: "Toyota", year_min: "2020", limit: "1" });
  });

  it("does not let a filter override the market", async () => {
    const { api, urls } = setup(page([]));
    await api.cars({ market: "xx" });
    assert.equal(urls[0].searchParams.get("market"), "us");
  });

  it("keeps only IAAI lots", async () => {
    const { api } = setup(page(["iaai:1", "other:2", "iaai:3"], "c2", 3));
    const result = await api.cars({ limit: 3 });
    assert.deepEqual(
      result.items.map((c) => c.id),
      ["iaai:1", "iaai:3"],
    );
    assert.equal(result.next_cursor, "c2");
    assert.equal(result.count, null);
  });

  it("iterCars collects maxItems lots across pages", async () => {
    const { api, urls } = setup(
      page(["other:1", "iaai:2"], "c2"),
      page(["other:3", "other:4"], "c3"),
      page(["iaai:5", "iaai:6"], "c4"),
    );
    const ids = [];
    for await (const c of api.iterCars({ limit: 2, maxItems: 2 })) ids.push(c.id);
    assert.deepEqual(ids, ["iaai:2", "iaai:5"]);
    assert.equal(urls.length, 3);
    assert.equal(urls[1].searchParams.get("cursor"), "c2");
  });

  it("iterCars with maxItems 0 makes no request", async () => {
    const { api, urls } = setup();
    for await (const c of api.iterCars({ maxItems: 0 })) assert.fail(`unexpected ${c.id}`);
    assert.equal(urls.length, 0);
  });
});

describe("car", () => {
  for (const listing of ["45551597", 45551597, "iaai:45551597"]) {
    it(`accepts ${JSON.stringify(listing)}`, async () => {
      const { api, urls } = setup(car("iaai:45551597"));
      assert.equal((await api.car(listing)).id, "iaai:45551597");
      assert.equal(urls[0].pathname, "/v1/cars/iaai:45551597");
    });
  }

  for (const bad of ["", "  ", "other:1", "iaai:"]) {
    it(`rejects ${JSON.stringify(bad)}`, () => {
      assert.throws(() => carId(bad), TypeError);
    });
  }

  it("throws the apiauto errors", async () => {
    const { api } = setup({ __status: 404, body: { error: { code: "not_found", message: "no such car" } } });
    await assert.rejects(api.car("1"), NotFoundError);
  });
});

describe("changes", () => {
  it("presets the market and keeps only IAAI events", async () => {
    const feed = {
      items: [
        { id: 1, car_id: "iaai:1", type: "added" },
        { id: 2, car_id: "other:2", type: "added" },
      ],
      next_cursor: null,
    };
    const { api, urls } = setup(feed, feed);
    const result = await api.changes({ since: "2026-11-01T00:00:00Z", type: ["added", "price_drop"] });
    assert.deepEqual(
      result.items.map((c) => c.car_id),
      ["iaai:1"],
    );
    assert.equal(urls[0].searchParams.get("market"), "us");
    assert.deepEqual(urls[0].searchParams.getAll("type"), ["added", "price_drop"]);
    const ids = [];
    for await (const c of api.iterChanges({ since: "2026-11-01T00:00:00Z", maxItems: 5 })) ids.push(c.id);
    assert.deepEqual(ids, [1]);
  });
});

describe("references", () => {
  it("brands, models and status use the market", async () => {
    const markets = {
      items: [
        { market: "kr", source: "encar" },
        { market: "cn", source: "che168" },
        { market: "us", source: "copart+iaai" },
      ],
    };
    const { api, urls } = setup([{ name: "Toyota", count: 5 }], [{ name: "Camry", count: 2 }], markets);
    assert.equal((await api.brands())[0].name, "Toyota");
    assert.deepEqual(params(urls[0]), { market: "us" });
    assert.equal((await api.models("Toyota"))[0].count, 2);
    assert.deepEqual(params(urls[1]), { market: "us", brand: "Toyota" });
    assert.equal((await api.status()).market, "us");
  });
});

describe("live", () => {
  it("keeps only IAAI lots", async () => {
    const { api, urls } = setup([car("iaai:1"), car("other:2")]);
    const lots = await api.live({ make: "Toyota", page: 1 });
    assert.deepEqual(
      lots.map((c) => c.id),
      ["iaai:1"],
    );
    assert.equal(urls[0].pathname, "/v1/us/live");
  });
});

describe("raw", () => {
  it("returns the raw fields or an empty object", () => {
    assert.deepEqual(raw({ raw: { source_values: { brand: "x" } } }).source_values, { brand: "x" });
    assert.deepEqual(raw({}), {});
  });
});
