// Smoke test against the real API. Skipped unless APIAUTO_KEY is set; spends a few records.
import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { IaaiApi, raw } from "../dist/index.js";

const enabled = Boolean(process.env.APIAUTO_KEY);

describe("live API", { skip: !enabled && "APIAUTO_KEY is not set" }, () => {
  it("returns IAAI cars and one car by its number", async () => {
    const api = new IaaiApi({ baseUrl: process.env.APIAUTO_BASE_URL });
    assert.equal((await api.status()).market, "us");
    const cars = [];
    for await (const car of api.iterCars({ limit: 10, maxItems: 3 })) cars.push(car);
    assert.ok(cars.length > 0, "the catalog returned no IAAI cars");
    assert.ok(cars.every((car) => car.source === "iaai"));
    const one = await api.car(cars[0].source_id);
    assert.equal(one.id, cars[0].id);
    assert.equal(typeof raw(one), "object");
  });
});
