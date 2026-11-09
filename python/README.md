# iaai-api — IAAI API client for Python

[![PyPI version](https://img.shields.io/pypi/v/iaai-api.svg)](https://pypi.org/project/iaai-api/)
[![Python versions](https://img.shields.io/pypi/pyversions/iaai-api.svg)](https://pypi.org/project/iaai-api/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/apiauto-space/iaai-api/blob/main/LICENSE)

`iaai-api` gives you IAAI insurance auction lots (USA) with VIN, damage and sale date as clean JSON through the [apiauto.space](https://apiauto.space/en/iaai-api/)
REST API, without writing or maintaining a scraper. Search by make, model, year, price and mileage, page
through the whole catalog, fetch one listing by its number and follow a feed of new cars, cars taken off sale
and price changes.

It is a thin layer over the general [`apiauto-space`](https://pypi.org/project/apiauto-space/) client with
the market preset to `us`, plus types for the IAAI-only fields. It comes from the apiauto.space team;
the project is not affiliated with IAAI (Insurance Auto Auctions).

- Sync `Client` and `AsyncClient`, retries on 429 and 5xx, one exception class per API error
- `car("45551597")` takes the IAAI listing number as well as the record id
- `IaaiRaw` types for the IAAI-only fields in `car["raw"]`
- Python 3.10+, `py.typed`, checked with `mypy --strict`

## Install

```bash
pip install iaai-api
```

The module you import is `iaai_api`.

## Get a key

Open the Telegram bot [@apiautospace_bot](https://t.me/apiautospace_bot?start=demo) and take a free demo
key: one day, 100 data requests, up to 20 cars per request. Paid plans are on the
[pricing page](https://apiauto.space/en/#pricing).

Save the key in the `APIAUTO_KEY` environment variable — the client reads it from there:

```bash
export APIAUTO_KEY="your-key"
```

Keep the key on your server: the API does not accept browser requests.

## Quick start

```python
import iaai_api

with iaai_api.Client() as client:  # reads APIAUTO_KEY
    page = client.cars(brand="Toyota", year_min=2020, limit=20)
    for car in page["items"]:
        print(car["id"], car["title"], car["price"]["amount"], car["price"]["currency"])

    one = client.car("45551597")  # a listing number or "iaai:45551597"
    print(one["listing_url"], one["photos"][:1])
```

A record looks like this (shortened; real values from the catalog):

```json
{
  "id": "iaai:45551597",
  "market": "us",
  "source": "iaai",
  "source_id": "45551597",
  "title": "2019 Toyota Sienna",
  "brand": "Toyota",
  "model": "Sienna",
  "year": 2019,
  "mileage_km": 97417,
  "fuel": "gasoline",
  "transmission": "automatic",
  "body_type": "minivan",
  "vin": "5TDZZ3DC1KS012693",
  "price": {
    "amount": "2150.00",
    "currency": "USD"
  },
  "price_usd": "2150.00",
  "location": {
    "country": "US",
    "region": "IL",
    "city": "St. Louis"
  },
  "listing_url": null,
  "is_active": true,
  "first_seen_at": "2026-09-23T00:21:30.655454Z",
  "photos": [
    "https://api.apiauto.space/img/iaai:45551597/1.jpg?exp=...&sig=..."
  ],
  "raw": {
    "lot_number": "45551597",
    "sale_date": "2026-09-29T14:30:00+00:00",
    "bid": 2150,
    "damage_main": "normal_wear",
    "title_doc": "clean",
    "location_branch": "St. Louis (IL)"
  }
}
```

Every record has the same keys as in the other apiauto.space markets; a value the source does not provide is
`None`. Prices are decimal strings in USD, `price_usd` is converted at the ECB daily rate.

## Copart and IAAI share one market

The API keeps Copart and IAAI lots together in the `us` market and does not filter by auction yet. This client
asks for `us` cars and keeps only IAAI lots on the client side. What that means for you:

- a page from `cars()` can hold fewer than `limit` lots, and its `count` is `None`;
- the Copart lots that were dropped still count against your quota;
- `iter_cars(max_items=...)` reads pages until it has collected `max_items` IAAI lots.

When you need both auctions, use the general `apiauto` client with `client.cars("us")`.

## Methods

| Method | What it does | Quota |
|---|---|---|
| `cars(**filters)` | One page of IAAI cars: `brand`, `model`, `year_min`, `year_max`, `price_min`, `price_max`, `mileage_max`, `fuel`, `body_type`, `sort`, `limit`, `cursor` | Cars returned |
| `iter_cars(max_items=None, **filters)` | Every matching car, page after page | Cars returned |
| `car(listing)` | One car by listing number or id, including cars taken off sale in the last 14 days | 1 record |
| `changes(since, type=None)` / `iter_changes(...)` | Feed of `added`, `disappeared`, `price_drop`, `price_up` events | Events returned |
| `brands()` / `models(brand)` | Makes and models with car counts | Free |
| `status()` | Plan access, data age and the number of active cars of the market | Free |
| `usage()` | Your plan, its term and the quota spent | Free |
| `live(make=..., model=...)` | Live search at the auction data provider for lots not in the catalog yet, Pro and Max plans | Separate counter |

The general client is at `client.core` for anything else. Errors are the `apiauto` exceptions, re-exported
here: `QuotaExceededError`, `RateLimitError`, `NotFoundError`, `AuthenticationError` and the rest.

## IAAI-only fields

```python
from iaai_api import raw

extra = raw(car)  # typed as IaaiRaw
print(extra.get("source_values"))
```

`IaaiRaw` lists the keys with comments; every key is optional, so read them with `.get`.

## Links

- [IAAI API on apiauto.space](https://apiauto.space/en/iaai-api/) and the [API documentation](https://apiauto.space/en/docs/)
- [`apiauto-space`](https://pypi.org/project/apiauto-space/): the general client for all markets
- Clients for the other sources: [`encar-api-client`](https://pypi.org/project/encar-api-client/), [`che168-api`](https://pypi.org/project/che168-api/), [`copart-api`](https://pypi.org/project/copart-api/)
- [Examples in curl, Python, JavaScript and PHP](https://github.com/apiauto-space/iaai-api-examples)
- The JavaScript version of this client: [`iaai-api` on npm](https://www.npmjs.com/package/iaai-api)

## License

MIT. IAAI is a trademark of its owner; it is named here only to say which listings the client returns.
