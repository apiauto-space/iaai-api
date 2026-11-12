# Changelog

## 0.1.1 — 2026-11-12

- README: the quick start collects cars with `iterCars({ maxItems })` and fetches the first one by its listing
  number, instead of a fixed listing that has gone off sale since.
  One page of the shared `us` market can hold no IAAI lots at all, so the old `cars(limit=20)` example
  could print nothing.
- README: links to the other source clients use their registry names (`encar-api-client`).

## 0.1.0 — 2026-11-09

- First release: `IaaiApi` over `apiauto` with the market preset to `us`, `carId()`, `raw()` and
  `IaaiRaw` types.
