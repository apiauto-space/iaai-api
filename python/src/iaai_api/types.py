"""Types of the IAAI-only fields of a record.

Every record has the same common keys in every market (see :class:`apiauto.Car`);
the fields only IAAI has are in ``car["raw"]``. :func:`raw` returns them typed::

    from iaai_api import raw

    extra = raw(car)
    print(extra.get("source_values"))
"""

from __future__ import annotations

from typing import Any, TypedDict, cast

from apiauto import Car

__all__ = ["FxQuote", "IaaiRaw", "raw"]


class FxQuote(TypedDict):
    """The ECB daily rate behind ``price_usd``."""

    currency: str
    usd_per_unit: str
    """Decimal string: US dollars for one unit of ``currency``."""
    date: str
    source: str


class IaaiRaw(TypedDict, total=False):
    """IAAI-only fields of a record (``car["raw"]``). Keys can be missing; read them with ``.get``."""

    lot_number: str | None
    """The lot number at the auction."""
    status: int | None
    sale_date: str | None
    """Auction date and time, ISO 8601."""
    bid: int | float | None
    """The current bid, US dollars."""
    buy_now: int | float | None
    """Buy-now price, US dollars."""
    final_bid: int | float | None
    """The final bid of a sold lot, US dollars."""
    damage_main: str | None
    """Primary damage, a canonical value such as ``front`` or ``rear``."""
    damage_second: str | None
    title_doc: str | None
    """Title document type, a canonical value such as ``clean`` or ``salvage``."""
    keys_available: bool | None
    airbags: Any
    odometer_mi: int | None
    """Odometer in miles as the auction shows it (``mileage_km`` is converted)."""
    odometer_status: Any
    condition: Any
    grade_iaai: Any
    estimate_repair_price: int | float | None
    pre_accident_price: int | float | None
    clean_wholesale_price: int | float | None
    seller: str | None
    seller_type: Any
    location_branch: str | None
    """The auction yard, for example ``Nashville (TN)``."""
    latitude: float | None
    longitude: float | None
    video_url: str | None
    drive: str | None
    """``fwd``, ``rwd``, ``awd`` or ``4wd``."""
    cylinders: int | None
    source_values: dict[str, str | None]
    """The auction's own spellings of make, model, fuel, damage and more."""
    fx: FxQuote | None


def raw(car: Car) -> IaaiRaw:
    """The IAAI-only fields of a record, typed as :class:`IaaiRaw`."""
    return cast(IaaiRaw, car.get("raw") or {})
