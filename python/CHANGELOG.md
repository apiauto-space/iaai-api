# Changelog

## 0.1.1 — 2026-11-12

- README: the quick start collects cars with `iter_cars(max_items=...)` and fetches the first one by its listing
  number, instead of a fixed listing that has gone off sale since.
  One page of the shared `us` market can hold no IAAI lots at all, so the old `cars(limit=20)` example
  could print nothing.
- README: links to the other source clients use their registry names (`encar-api-client`).

## 0.1.0 — 2026-11-09

- First release: `Client` and `AsyncClient` over `apiauto-space` with the market preset to `us`,
  `car_id()`, `raw()` and `IaaiRaw` types.
