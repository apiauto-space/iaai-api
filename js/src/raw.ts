// Types of the IAAI-only fields of a record (`car.raw`).
/** The ECB daily rate behind `price_usd`. */
export interface FxQuote {
  currency: string;
  /** Decimal string: US dollars for one unit of `currency`. */
  usd_per_unit: string;
  date: string;
  source: string;
}

/** IAAI-only fields of a record (`car.raw`). Every key is optional. */
export interface IaaiRaw {
  /** The lot number at the auction. */
  lot_number?: string | null;
  status?: number | null;
  /** Auction date and time, ISO 8601. */
  sale_date?: string | null;
  /** The current bid, US dollars. */
  bid?: number | null;
  /** Buy-now price, US dollars. */
  buy_now?: number | null;
  /** The final bid of a sold lot, US dollars. */
  final_bid?: number | null;
  /** Primary damage, a canonical value such as `front` or `rear`. */
  damage_main?: string | null;
  damage_second?: string | null;
  /** Title document type, a canonical value such as `clean` or `salvage`. */
  title_doc?: string | null;
  keys_available?: boolean | null;
  airbags?: unknown;
  /** Odometer in miles as the auction shows it (`mileage_km` is converted). */
  odometer_mi?: number | null;
  odometer_status?: unknown;
  condition?: unknown;
  grade_iaai?: unknown;
  estimate_repair_price?: number | null;
  pre_accident_price?: number | null;
  clean_wholesale_price?: number | null;
  seller?: string | null;
  seller_type?: unknown;
  /** The auction yard, for example `Nashville (TN)`. */
  location_branch?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  video_url?: string | null;
  /** `fwd`, `rwd`, `awd` or `4wd`. */
  drive?: string | null;
  cylinders?: number | null;
  /** The auction's own spellings of make, model, fuel, damage and more. */
  source_values?: Record<string, string | null>;
  fx?: FxQuote | null;
}
