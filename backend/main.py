# import re
# from fastapi import FastAPI, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# import httpx
# from datetime import datetime, timezone
# from typing import Optional
# import logging
# from collections import defaultdict


# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# app = FastAPI(title="Kalshi Probability Proxy", version="2.0.0")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# KALSHI_BASE_URL = "https://api.elections.kalshi.com/trade-api/v2"

# # ─── Category → series tickers ───────────────────────────────────────────────
# SERIES_TICKERS: dict[str, list[str]] = {
#     "finance": [
#         "KXBTC", "KXETH", "KXCRYPTO", "KXSP500", "KXNASDAQ",
#         "KXDOW", "KXFED", "KXCPI", "KXGDP", "KXOIL", "KXGOLD",
#         "KXRATES", "KXJOBS", "KXECON", "KXSTOCKS",
#     ],
#     "sports": [
#         "KXNBA", "KXNFL", "KXMLB", "KXNHL", "KXNCAAB", "KXNCAAF",
#         "KXSOCCER", "KXTENNIS", "KXGOLF", "KXMMA", "KXBOXING",
#         "KXNASCAR", "KXFORMULA", "KXOLYMPICS", "KXSPORTS",
#     ],
#     "weather": [
#         "KXRAIN", "KXSNOW", "KXTEMP", "KXHURRICANE", "KXSTORM",
#         "KXWIND", "KXFLOOD", "KXWILD", "KXWX",
#     ],
# }

# # ─── Category keywords (title-based fallback classifier) ─────────────────────
# CATEGORY_KEYWORDS: dict[str, list[str]] = {
#     "finance": [
#         "s&p", "btc", "bitcoin", "nasdaq", "dow", "fed", "rate", "inflation",
#         "ethereum", "eth", "crypto", "stock", "market", "gdp", "cpi",
#         "interest", "bond", "oil", "gold", "dollar", "economy", "recession",
#         "earnings", "ipo", "index", "trade", "tariff", "jobs", "unemployment",
#     ],
#     "sports": [
#         "nba", "nfl", "mlb", "nhl", "ncaa", "win", "game", "championship",
#         "playoff", "match", "tournament", "league", "cup", "super bowl",
#         "world series", "finals", "score", "team", "player", "season",
#         "mls", "ufc", "mma", "boxing", "golf", "tennis", "formula", "nascar",
#         "olympic", "soccer", "football", "basketball", "baseball", "hockey",
#     ],
#     "weather": [
#         "rain", "snow", "temperature", "weather", "storm", "hurricane",
#         "tornado", "flood", "wind", "celsius", "fahrenheit", "forecast",
#         "precipitation", "drought", "wildfire", "hail", "blizzard",
#     ],
# }

# # Derived: series prefix → category (built once at startup)
# SERIES_PREFIX_MAP: dict[str, str] = {
#     prefix.upper(): cat
#     for cat, prefixes in SERIES_TICKERS.items()
#     for prefix in prefixes
# }

# # Day-of-week → category rotation
# DAY_CATEGORY: dict[int, str] = {
#     0: "finance",   # Mon
#     1: "sports",    # Tue
#     2: "weather",   # Wed
#     3: "finance",   # Thu
#     4: "sports",    # Fri
#     5: "sports",    # Sat
#     6: "weather",   # Sun
# }


# # ─── Helpers ──────────────────────────────────────────────────────────────────

# def classify_market(title: str, series_ticker: str = "") -> str:
#     """
#     1. Series prefix match (most reliable)
#     2. Title keyword match
#     3. Default → finance
#     """
#     st = (series_ticker or "").upper()
#     for prefix, category in SERIES_PREFIX_MAP.items():
#         if st.startswith(prefix):
#             return category

#     title_lower = title.lower()
#     for category, keywords in CATEGORY_KEYWORDS.items():
#         if any(kw in title_lower for kw in keywords):
#             return category

#     logger.debug(
#         f"classify_market: no match for title='{title}' "
#         f"series='{series_ticker}', defaulting to finance"
#     )
#     return "finance"


# def format_k(value: int) -> str:
#     return f"{round(value / 1000)}K"


# # def create_card_title(title: str, ticker: str, subtitle: str) -> str:
# #     search_text = f"{ticker} {subtitle} {title}".lower()

# #     btc_match = re.search(r'b(\d+)', ticker.lower())
# #     if "btc" in search_text and btc_match:
# #         price = int(btc_match.group(1))
# #         return f"BTC > ${format_k(price)}"

# #     eth_match = re.search(r'b(\d+)', ticker.lower())
# #     if "eth" in search_text and eth_match:
# #         price = int(eth_match.group(1))
# #         return f"ETH > ${format_k(price)}"

# #     cpi_match = re.search(r't(\d+(?:\.\d+)?)', ticker.lower())
# #     if "cpi" in search_text and cpi_match:
# #         value = cpi_match.group(1)
# #         return f"CPI > {value}%"

# #     if "lakers" in search_text:
# #         return "Lakers Win"
# #     if "rain" in search_text:
# #         return "NYC Rain"
# #     if "s&p" in search_text:
# #         return "S&P 500 Up"

# #     return title[:32]

# # Series prefix → human-readable short label
# SERIES_SHORT: dict[str, str] = {
#     "KXBTC":        "BTC",
#     "KXETH":        "ETH",
#     "KXCRYPTO":     "Crypto",
#     "KXSP500":      "S&P 500",
#     "KXNASDAQ":     "Nasdaq",
#     "KXDOW":        "Dow",
#     "KXFED":        "Fed Rate",
#     "KXCPI":        "CPI",
#     "KXGDP":        "GDP",
#     "KXOIL":        "Oil",
#     "KXGOLD":       "Gold",
#     "KXRATES":      "Rates",
#     "KXJOBS":       "Jobs",
#     "KXNBA":        "NBA",
#     "KXNFL":        "NFL",
#     "KXMLB":        "MLB",
#     "KXNHL":        "NHL",
#     "KXNCAAB":      "NCAA BB",
#     "KXNCAAF":      "NCAA FB",
#     "KXSOCCER":     "Soccer",
#     "KXMMA":        "MMA",
#     "KXBOXING":     "Boxing",
#     "KXGOLF":       "Golf",
#     "KXTENNIS":     "Tennis",
#     "KXNASCAR":     "NASCAR",
#     "KXFORMULA":    "F1",
#     "KXOLYMPICS":   "Olympics",
#     "KXSPORTS":     "Sports",
#     "KXMVESPORTS":  "eSports",   # ← catches KXMVESPORTSMULTIGAMEEXTENDED
#     "KXRAIN":       "Rain",
#     "KXSNOW":       "Snow",
#     "KXTEMP":       "Temp",
#     "KXHURRICANE":  "Hurricane",
#     "KXSTORM":      "Storm",
#     "KXWIND":       "Wind",
#     "KXFLOOD":      "Flood",
#     "KXWX":         "Weather",
# }


# def create_card_title(title: str, ticker: str, subtitle: str) -> str:
#     """
#     Build a short card title from ticker + subtitle + title.
#     """

#     t = (ticker or "").upper()
#     sub = (subtitle or "").strip()
#     titl = (title or "").strip()

#     # ── Step 1: series label ────────────────────────────────
#     label = None

#     for prefix in sorted(SERIES_SHORT, key=len, reverse=True):
#         if t.startswith(prefix):
#             label = SERIES_SHORT[prefix]
#             break

#     # ── Step 2: ticker-based thresholds ─────────────────────
#     threshold = ""

#     # BTC / ETH encoded bucket price
#     bucket_match = re.search(r'B(\d+)', t)

#     if bucket_match and label in {"BTC", "ETH"}:
#         value = int(bucket_match.group(1))
#         threshold = f"> ${round(value / 1000)}K"

#     # CPI encoded threshold
#     elif label == "CPI":
#         cpi_match = re.search(r'T(\d+(?:\.\d+)?)', t)
#         if cpi_match:
#             threshold = f"> {cpi_match.group(1)}%"

#     # Generic extraction fallback
#     if not threshold:
#         threshold = _extract_threshold(sub or titl)

#     # ── Step 3: compose ─────────────────────────────────────
#     if label and threshold:
#         result = f"{label} {threshold}"

#     elif label:
#         result = label

#     else:
#         result = titl[:15]

#     return result[:20]

# # Threshold extraction patterns (order matters — most specific first)
# # _THRESHOLD_PATTERNS = [
# #     # Dollar amounts  e.g. "> $70,000"  ">70000"  "above $1.2M"
# #     (re.compile(r'(?:above|over|>)\s*\$?([\d,]+(?:\.\d+)?)\s*([KkMm]?)', re.I),
# #      lambda m: _fmt_dollar(m.group(1), m.group(2))),

# #     # Percentage thresholds  e.g. "< 3.2%"  "below 5%"
# #     (re.compile(r'(?:below|under|<|above|over|>)?\s*([\d.]+)\s*%', re.I),
# #      lambda m: f"{m.group(1)}%"),

# #     # Direction words with no number — "higher", "lower", "up", "down", "win", "loss"
# #     (re.compile(r'\b(higher|up|gain|rise|bull)\b', re.I),  lambda _: "Up"),
# #     (re.compile(r'\b(lower|down|drop|fall|bear)\b', re.I), lambda _: "Down"),
# #     (re.compile(r'\bwin\b', re.I),                          lambda _: "Win"),
# #     (re.compile(r'\b(loss|lose)\b', re.I),                  lambda _: "Loss"),
# # ]
# _THRESHOLD_PATTERNS = [

#     # Dollar amounts
#     # Examples:
#     #   > $70,000
#     #   above $1.2M
#     #   over 70000
#     (
#         re.compile(
#             r'(?:above|over|>)\s*\$([\d,]+(?:\.\d+)?)\s*([KkMm]?)',
#             re.I
#         ),
#         lambda m: _fmt_dollar(m.group(1), m.group(2))
#     ),

#     # Percentages
#     (
#         re.compile(
#             r'(?:below|under|<|above|over|>)?\s*([\d.]+)\s*%',
#             re.I
#         ),
#         lambda m: f"> {m.group(1)}%"
#     ),

#     # Direction words
#     (
#         re.compile(r'\b(higher|up|gain|rise|bull)\b', re.I),
#         lambda _: "Up"
#     ),

#     (
#         re.compile(r'\b(lower|down|drop|fall|bear)\b', re.I),
#         lambda _: "Down"
#     ),

#     (
#         re.compile(r'\bwin\b', re.I),
#         lambda _: "Win"
#     ),

#     (
#         re.compile(r'\b(loss|lose)\b', re.I),
#         lambda _: "Loss"
#     ),
# ]


# def _fmt_dollar(digits: str, suffix: str) -> str:
#     """Turn '70000' / '70' / '1.2' + 'K'/'M' into '$70K' / '$1.2M'."""
#     val = float(digits.replace(",", ""))
#     s   = suffix.upper()
#     if s == "M" or val >= 1_000_000:
#         return f">${val / 1_000_000:.1f}M".rstrip("0").rstrip(".")  # >$1.2M
#     if s == "K" or val >= 1_000:
#         return f">${round(val / 1_000)}K"                            # >$70K
#     return f">${int(val)}"                                            # >$500


# def _extract_threshold(text: str) -> str:
#     """Return a short threshold string from free text, or empty string."""
#     for pattern, formatter in _THRESHOLD_PATTERNS:
#         m = pattern.search(text)
#         if m:
#             return formatter(m)
#     return ""

# def to_pct(value) -> float:
#     """
#     Convert a Kalshi _dollars field (string like "0.5600") to a percentage (56.0).
#     Safely handles None, 0, int, float, and string inputs.
#     """
#     try:
#         return float(value or 0) * 100
#     except (TypeError, ValueError):
#         return 0.0


# def parse_market(m: dict) -> Optional[dict]:
#     """
#     Parse a raw Kalshi market dict into our standard schema.

#     Probability priority:
#       1. Bid/ask midpoint        — tightest spread, best estimate
#       2. yes_bid + implied ask   — implied yes_ask = 100 - no_bid
#       3. yes_bid alone           — ask missing / thin book
#       4. yes_ask alone
#       5. last_price_dollars      — last traded price
#       6. Default 50              — truly no data

#     Returns None if the market cannot be safely parsed.
#     """
#     try:
#         ticker = m.get("ticker", "unknown")

#         # All _dollars fields are decimal strings e.g. "0.5600" → *100 → 56.0%
#         yes_bid    = to_pct(m.get("yes_bid_dollars"))
#         yes_ask    = to_pct(m.get("yes_ask_dollars"))
#         no_bid     = to_pct(m.get("no_bid_dollars"))
#         last_price = to_pct(m.get("last_price_dollars"))
#         volume     = float(m.get("volume_fp", 0) or 0)

#         # ── Probability cascade ───────────────────────────────────────────────
#         if yes_bid and yes_ask:
#             # Full spread — use midpoint
#             probability = round((yes_bid + yes_ask) / 2)
#         elif yes_bid and no_bid:
#             # Implied yes_ask from no_bid (binary identity: yes_ask = 100 - no_bid)
#             implied_yes_ask = 100 - no_bid
#             probability = round((yes_bid + implied_yes_ask) / 2)
#         elif yes_bid:
#             probability = round(yes_bid)
#         elif yes_ask:
#             probability = round(yes_ask)
#         elif last_price:
#             # Last traded price — reliable when book is empty
#             probability = round(last_price)
#         else:
#             probability = 50

#         # Clamp to valid display range — prevents filter edge-case bugs
#         probability = max(1, min(99, probability))

#         close_time_str = m.get("close_time") or m.get("expiration_time")
#         if not close_time_str:
#             return None

#         close_time = datetime.fromisoformat(close_time_str.replace("Z", "+00:00"))
#         hours_until_close = (
#             close_time - datetime.now(timezone.utc)
#         ).total_seconds() / 3600

#         series_ticker = m.get("series_ticker", "") or ""
#         title         = m.get("title", "")
#         subtitle      = m.get("yes_sub_title", "")

#         return {
#             "ticker":            ticker,
#             "series_ticker":     series_ticker,
#             "title":             title,
#             "yes_sub_title":     subtitle,
#             "subtitle":          m.get("subtitle", ""),
#             "card_title":        create_card_title(title, ticker, subtitle),
#             "probability":       probability,
#             "yes_bid":           round(yes_bid, 2),
#             "yes_ask":           round(yes_ask, 2),
#             "last_price":        round(last_price, 2),
#             "volume":            volume,
#             "close_time":        close_time_str,
#             "hours_until_close": round(hours_until_close, 1),
#             "status":            m.get("status", ""),
#             "category":          classify_market(title, series_ticker),
#         }
#     except Exception as e:
#         logger.warning(f"Failed to parse market {m.get('ticker')}: {e}")
#         return None


# def apply_filters(
#     pool: list[dict],
#     max_hours: float,
#     min_volume: float,
#     min_prob: int,
#     max_prob: int,
# ) -> list[dict]:
#     return [
#         m for m in pool
#         if m["status"] == "active"
#         and m["hours_until_close"] <= max_hours
#         and min_prob <= m["probability"] <= max_prob
#         and m["volume"] >= min_volume
#     ]


# def rank(pool: list[dict]) -> list[dict]:
#     """Sort by: highest volume → soonest close → shortest title."""
#     return sorted(
#         pool,
#         key=lambda x: (-x["volume"], x["hours_until_close"], len(x["title"])),
#     )


# # ─── Data fetchers ────────────────────────────────────────────────────────────

# async def fetch_by_category(category: str, limit: int = 50) -> list[dict]:
#     """Fetch markets for every series ticker in a category."""
#     series_list = SERIES_TICKERS.get(category, [])
#     results: list[dict] = []
#     async with httpx.AsyncClient(timeout=10) as client:
#         for series in series_list:
#             try:
#                 resp = await client.get(
#                     f"{KALSHI_BASE_URL}/markets",
#                     params={"status": "open", "series_ticker": series, "limit": limit},
#                 )
#                 if resp.status_code == 200:
#                     for m in resp.json().get("markets", []):
#                         parsed = parse_market(m)
#                         if parsed:
#                             results.append(parsed)
#             except httpx.HTTPError:
#                 continue
#     logger.info(f"fetch_by_category({category}) → {len(results)} markets")
#     return results


# async def fetch_global(limit: int = 200) -> list[dict]:
#     """Fetch open markets globally (last-resort fallback)."""
#     async with httpx.AsyncClient(timeout=10) as client:
#         try:
#             resp = await client.get(
#                 f"{KALSHI_BASE_URL}/markets",
#                 params={"status": "open", "limit": limit},
#             )
#             resp.raise_for_status()
#             return [
#                 p
#                 for p in (parse_market(m) for m in resp.json().get("markets", []))
#                 if p
#             ]
#         except httpx.HTTPError as e:
#             raise HTTPException(status_code=502, detail=f"Kalshi API error: {str(e)}")


# def top_for_category(pool: list[dict], n: int = 10) -> list[dict]:
#     """
#     Apply cascading filters within one category pool, return top-n.
#     n=10 gives enough depth to skip title/ticker dupes and still fill all slots.
#     """
#     candidates = (
#         apply_filters(pool, max_hours=48,  min_volume=100, min_prob=10, max_prob=90)
     
#     )
#     return rank(candidates)[:n]


# def normalize_title(title: str) -> str:
#     return title.lower().strip()


# # ─── Routes ───────────────────────────────────────────────────────────────────

# @app.get("/health")
# def health():
#     return {"status": "ok", "time": datetime.now(timezone.utc).isoformat()}


# # ── /debug/markets ────────────────────────────────────────────────────────────
# @app.get("/debug/markets")
# async def debug_markets():
#     """
#     Debug endpoint — raw filter diagnostics from Kalshi.
#     Uses _dollars fields (current v2 API). The old integer yes_ask/yes_bid
#     fields are deprecated and removed — using them always returned 0.
#     """
#     async with httpx.AsyncClient(timeout=10) as client:
#         try:
#             resp = await client.get(
#                 f"{KALSHI_BASE_URL}/markets",
#                 params={"status": "open", "limit": 20},
#             )
#             resp.raise_for_status()
#         except httpx.HTTPError as e:
#             raise HTTPException(status_code=502, detail=f"Kalshi API error: {str(e)}")

#     now     = datetime.now(timezone.utc)
#     markets = resp.json().get("markets", [])
#     sample  = []

#     for m in markets[:20]:
#         yes_bid    = to_pct(m.get("yes_bid_dollars"))
#         yes_ask    = to_pct(m.get("yes_ask_dollars"))
#         no_bid     = to_pct(m.get("no_bid_dollars"))
#         last_price = to_pct(m.get("last_price_dollars"))

#         if yes_bid and yes_ask:
#             probability = round((yes_bid + yes_ask) / 2)
#         elif yes_bid and no_bid:
#             probability = round((yes_bid + (100 - no_bid)) / 2)
#         elif yes_bid:
#             probability = round(yes_bid)
#         elif yes_ask:
#             probability = round(yes_ask)
#         elif last_price:
#             probability = round(last_price)
#         else:
#             probability = 0

#         close_time_str = m.get("close_time") or m.get("expiration_time")
#         hours_left     = None
#         if close_time_str:
#             try:
#                 ct         = datetime.fromisoformat(close_time_str.replace("Z", "+00:00"))
#                 hours_left = round((ct - now).total_seconds() / 3600, 1)
#             except Exception:
#                 pass

#         # volume_fp is the current field; volume is the deprecated integer field
#         volume = float(m.get("volume_fp") or m.get("volume") or 0)

#         sample.append({
#             "ticker":        m.get("ticker"),
#             "title":         m.get("title"),
#             "status":        m.get("status"),
#             "probability":   probability,
#             "yes_bid":       round(yes_bid, 2),
#             "yes_ask":       round(yes_ask, 2),
#             "last_price":    round(last_price, 2),
#             "volume":        volume,
#             "hours_left":    hours_left,
#             "passes_status": m.get("status") == "active",
#             "passes_hours":  hours_left is not None and hours_left <= 48,
#             "passes_prob":   10 <= probability <= 90,
#             "passes_volume": volume >= 100,
#             "all_pass": (
#                 m.get("status") == "active"
#                 and hours_left is not None and hours_left <= 48
#                 and 10 <= probability <= 90
#                 and volume >= 100
#             ),
#         })

#     passing = [s for s in sample if s["all_pass"]]
#     return {
#         "total_returned":  len(markets),
#         "sample_size":     len(sample),
#         "passing_filters": len(passing),
#         "sample":          sample,
#     }


# # ── /markets/ticker ───────────────────────────────────────────────────────────
# @app.get("/markets/ticker")
# async def get_ticker_markets():
#     """
#     Returns 3–5 live markets for the probability ticker.

#     Guarantees:
#       - Minimum 3 markets always returned.
#       - Maximum 5 markets.
#       - No duplicate tickers or titles.
#       - At least 1 market per category when data is available.
#       - If a category fails, compensates from other categories → MIN 3 always held.

#     Steps:
#       1. Fetch each category independently via series tickers.
#       2. Global fallback for any completely empty category pool.
#       3. Pre-compute top-10 candidates per category (filters applied once).
#       4. Guarantee 1 per category (best effort, skipping dupes).
#       5. Compensate missing slots from other categories → MIN 3.
#       6. Fill remaining slots up to 5 → MAX 5.
#     """
#     now = datetime.now(timezone.utc)

#     # ── Step 1: Fetch per category ────────────────────────────────────────────
#     category_pool: dict[str, list[dict]] = {}
#     for cat in SERIES_TICKERS:
#         category_pool[cat] = await fetch_by_category(cat, limit=1000)

#     # ── Step 2: Global fallback for empty categories ──────────────────────────
#     empty_cats = [cat for cat, pool in category_pool.items() if not pool]
#     if empty_cats:
#         logger.warning(f"Empty pools for {empty_cats} — trying global fetch")
#         global_markets = await fetch_global(limit=200)
#         for m in global_markets:
#             if m["category"] in empty_cats:
#                 category_pool[m["category"]].append(m)

#     # ── Step 3: Pre-compute top-10 per category ───────────────────────────────
#     category_tops: dict[str, list[dict]] = {
#         cat: top_for_category(category_pool[cat], n=10)
#         for cat in SERIES_TICKERS
#     }
#     logger.info(f'sljfldsjf====={category_tops.get("finance")}')
#     # ── Dedup state ───────────────────────────────────────────────────────────
#     picked: list[dict] = []
#     seen_tickers: set[str] = set()
#     seen_titles: set[str]  = set()
#     category_counts: dict[str, int] = {cat: 0 for cat in SERIES_TICKERS}
#     MAX_PER_CATEGORY = 2
    


#     def try_add(market: dict) -> bool:
#         """Add market only if both ticker AND normalized title are unseen."""
#         ticker     = market["ticker"]
#         norm_title = normalize_title(market["title"])
#         if ticker in seen_tickers or norm_title in seen_titles:
#             return False
#         picked.append(market)
#         seen_tickers.add(ticker)
#         seen_titles.add(norm_title)
#         return True

#     # ── Step 4: Guarantee 1 per category ─────────────────────────────────────
#     failed_cats: list[str] = []
#     for cat in SERIES_TICKERS:
#         added = False
#         for candidate in category_tops[cat]:
#             if try_add(candidate):
#                 logger.info(
#                     f"[{cat}] Guaranteed pick: "
#                     f"{candidate['ticker']} | '{candidate['title']}'"
#                 )
#                 added = True
#                 break
#         if not added:
#             logger.warning(f"[{cat}] No unique market — will compensate")
#             failed_cats.append(cat)

#     # ── Step 5: Compensate for failed categories → MIN 3 ─────────────────────
#     if failed_cats:
#         needed = len(failed_cats)
#         logger.warning(f"Compensating {needed} missing slot(s) from runner-ups")

#         compensation_pool = rank([
#             m
#             for cat in SERIES_TICKERS
#             if cat not in failed_cats
#             for m in category_tops[cat]
#         ])
#         for candidate in compensation_pool:
#             if needed <= 0:
#                 break
#             if try_add(candidate):
#                 logger.info(
#                     f"Compensation fill: "
#                     f"{candidate['ticker']} | '{candidate['title']}'"
#                 )
#                 needed -= 1

#         if len(picked) < 3:
#             logger.error(
#                 f"Could only pick {len(picked)} markets — "
#                 "Kalshi data may be too thin"
#             )

#     # ── Step 6: Fill up to MAX 5 with per-category runner-ups ────────────────
#     for cat in SERIES_TICKERS:
#         if len(picked) >= 5:
#             break
#         for candidate in category_tops[cat]:
#             if len(picked) >= 5:
#                 break
#             if try_add(candidate):
#                 logger.info(
#                     f"[{cat}] Runner-up fill: "
#                     f"{candidate['ticker']} | '{candidate['title']}'"
#                 )

#     picked = rank(picked)
#     logger.info(f"/markets/ticker — returning {len(picked)} markets (min=3, max=5)")
#     return {"markets": picked, "fetched_at": now.isoformat()}


# # ── /markets/daily ────────────────────────────────────────────────────────────
# @app.get("/markets/daily")
# async def get_daily_question():
#     """
#     Returns the single daily question market based on day-of-week rotation.

#     Category rotation:
#       Mon/Thu → finance | Tue/Fri/Sat → sports | Wed/Sun → weather

#     Filter cascade (always stays within the target category):
#       1. Strict:      close<=24h, vol>=500, prob 20-80%
#       2. Fallback 1:  close<=24h, vol>=100, prob 20-80%
#       3. Fallback 2:  close<=48h, vol>=100, prob 10-90%
#       4. Last resort: any active market in target category

#     Title <=80 chars is a soft preference (not a hard cut) so we never
#     silently return None just because all titles are long.

#     Never falls back to a different category.
#     """
#     today           = datetime.now(timezone.utc)
#     target_category = DAY_CATEGORY[today.weekday()]
#     logger.info(
#         f"/markets/daily — target_category={target_category} "
#         f"(weekday={today.weekday()})"
#     )

#     def pick_best(pool: list[dict]) -> Optional[dict]:
#         filtered = [
#             m for m in pool
#             if m["status"] == "active"
#             and m["category"] == target_category
#         ]
#         if not filtered:
#             return None

#         candidates = (
#             apply_filters(filtered, max_hours=24, min_volume=500, min_prob=20, max_prob=80)
#             or apply_filters(filtered, max_hours=24, min_volume=100, min_prob=20, max_prob=80)
            
#         )

#         # Soft-prefer short titles; fall back to all candidates if none are short enough
#         # FIX: previously a hard filter — could silently return None when all titles >80
#         short = [m for m in candidates if len(m["title"]) <= 80]
#         final = short if short else candidates

#         return rank(final)[0] if final else None

#     # Step 1: fetch via series tickers
#     pool   = await fetch_by_category(target_category, limit=500)
#     chosen = pick_best(pool)
#     if chosen:
#         logger.info(f"Chose market from series fetch: {chosen['ticker']}")

#     # Step 2: global fetch, still target category only
#     if not chosen:
#         logger.warning(
#             f"Series fetch found nothing for {target_category} — "
#             "trying global fetch"
#         )
#         all_markets = await fetch_global(limit=200)
#         chosen      = pick_best(all_markets)
#         if chosen:
#             logger.info(f"Chose market from global fetch: {chosen['ticker']}")

#     if not chosen:
#         raise HTTPException(
#             status_code=404,
#             detail=f"No {target_category} market found for today",
#         )

#     return {
#         "market":          chosen,
#         "target_category": target_category,
#         "date":            today.date().isoformat(),
#     }


# # ── /markets/{ticker} ─────────────────────────────────────────────────────────
# @app.get("/markets/{ticker}")
# async def get_market_result(ticker: str):
#     """
#     Fetch a specific market by ticker.
#     Used by the iOS app the next day to check the result.

#     result field:
#       null  → still open / not yet resolved
#       "yes" → resolved YES
#       "no"  → resolved NO
#     """
#     async with httpx.AsyncClient(timeout=10) as client:
#         try:
#             resp = await client.get(f"{KALSHI_BASE_URL}/markets/{ticker}")
#             resp.raise_for_status()
#         except httpx.HTTPError as e:
#             raise HTTPException(status_code=502, detail=f"Kalshi API error: {str(e)}")

#     market = resp.json().get("market", {})
#     parsed = parse_market(market)
#     if not parsed:
#         raise HTTPException(status_code=422, detail="Could not parse market data")

#     parsed["result"] = market.get("result")   # null | "yes" | "no"
#     return {"market": parsed}















# import re
# from fastapi import FastAPI, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# import httpx
# from datetime import datetime, timezone
# from typing import Optional
# import logging
# from collections import defaultdict


# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# app = FastAPI(title="Kalshi Probability Proxy", version="2.0.0")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# KALSHI_BASE_URL = "https://api.elections.kalshi.com/trade-api/v2"

# # ─── Category → series tickers ───────────────────────────────────────────────
# SERIES_TICKERS: dict[str, list[str]] = {
#      "finance": [
#         "KXBTC",
#         "KXETH",
#         "KXCRYPTO",
#         "KXSP500",
#         "KXNASDAQ",
#         "KXDOW",
#         "KXFED",
#         "KXCPI",
#         "KXGDP",
#         "KXOIL",
#         "KXGOLD",
#         "KXRATES",
#         "KXJOBS",
#         "KXECON",
#         "KXSTOCKS"
#     ],
   
#     "sports": [
#         "KXNBA",
#         "KXNFL",
#         "KXMLB",
#         "KXNHL",
#         "KXNCAAB",
#         "KXNCAAF",
#         "KXSOCCER",
#         "KXTENNIS",
#         "KXGOLF",
#         "KXMMA",
#         "KXBOXING",
#         "KXNASCAR",
#         "KXFORMULA",
#         "KXOLYMPICS",
#         "KXSPORTS"
#     ],
    
#     "weather": [
#         "KXRAIN",
#         "KXSNOW",
#         "KXTEMP",
#         "KXHURRICANE",
#         "KXSTORM",
#         "KXWIND",
#         "KXFLOOD",
#         "KXWILD",
#         "KXWX",
#         "KXHIGHNY"
#     ]
# }

# # ─── Category keywords (title-based fallback classifier) ─────────────────────
# CATEGORY_KEYWORDS: dict[str, list[str]] = {
#     "finance": [
#         "s&p", "btc", "bitcoin", "nasdaq", "dow", "fed", "rate", "inflation",
#         "ethereum", "eth", "crypto", "stock", "market", "gdp", "cpi",
#         "interest", "bond", "oil", "gold", "dollar", "economy", "recession",
#         "earnings", "ipo", "index", "trade", "tariff", "jobs", "unemployment",
#     ],
#     "sports": [
#         "nba", "nfl", "mlb", "nhl", "ncaa", "win", "game", "championship",
#         "playoff", "match", "tournament", "league", "cup", "super bowl",
#         "world series", "finals", "score", "team", "player", "season",
#         "mls", "ufc", "mma", "boxing", "golf", "tennis", "formula", "nascar",
#         "olympic", "soccer", "football", "basketball", "baseball", "hockey",
#     ],
#     "weather": [
#         "rain", "snow", "temperature", "weather", "storm", "hurricane",
#         "tornado", "flood", "wind", "celsius", "fahrenheit", "forecast",
#         "precipitation", "drought", "wildfire", "hail", "blizzard",
#     ],
# }

# # Derived: series prefix → category (built once at startup)
# SERIES_PREFIX_MAP: dict[str, str] = {
#     prefix.upper(): cat
#     for cat, prefixes in SERIES_TICKERS.items()
#     for prefix in prefixes
# }

# # Day-of-week → category rotation
# DAY_CATEGORY: dict[int, str] = {
#     0: "finance",   # Mon
#     1: "sports",    # Tue
#     2: "weather",   # Wed
#     3: "finance",   # Thu
#     4: "sports",    # Fri
#     5: "sports",    # Sat
#     6: "weather",   # Sun
# }

# # Sports series that benefit from team-name extraction in card titles
# SPORTS_SERIES: set[str] = {
#     "NBA", "NFL", "MLB", "NHL", "NCAA BB", "NCAA FB",
#     "Soccer", "MMA", "Boxing", "Tennis", "Golf", "F1", "NASCAR",
# }


# # ─── Helpers ──────────────────────────────────────────────────────────────────

# def classify_market(title: str, series_ticker: str = "") -> str:
#     """
#     1. Series prefix match (most reliable)
#     2. Title keyword match
#     3. Default → finance
#     """
#     st = (series_ticker or "").upper()
#     for prefix, category in SERIES_PREFIX_MAP.items():
#         if st.startswith(prefix):
#             return category

#     title_lower = title.lower()
#     for category, keywords in CATEGORY_KEYWORDS.items():
#         if any(kw in title_lower for kw in keywords):
#             return category

#     logger.debug(
#         f"classify_market: no match for title='{title}' "
#         f"series='{series_ticker}', defaulting to finance"
#     )
#     return "finance"


# def format_k(value: int) -> str:
#     return f"{round(value / 1000)}K"


# # Series prefix → human-readable short label
# SERIES_SHORT: dict[str, str] = {
#     "KXBTC":        "BTC",
#     "KXETH":        "ETH",
#     "KXCRYPTO":     "Crypto",
#     "KXSP500":      "S&P 500",
#     "KXNASDAQ":     "Nasdaq",
#     "KXDOW":        "Dow",
#     "KXFED":        "Fed Rate",
#     "KXCPI":        "CPI",
#     "KXGDP":        "GDP",
#     "KXOIL":        "Oil",
#     "KXGOLD":       "Gold",
#     "KXRATES":      "Rates",
#     "KXJOBS":       "Jobs",
#     "KXNBA":        "NBA",
#     "KXNFL":        "NFL",
#     "KXMLB":        "MLB",
#     "KXNHL":        "NHL",
#     "KXNCAAB":      "NCAA BB",
#     "KXNCAAF":      "NCAA FB",
#     "KXSOCCER":     "Soccer",
#     "KXMMA":        "MMA",
#     "KXBOXING":     "Boxing",
#     "KXGOLF":       "Golf",
#     "KXTENNIS":     "Tennis",
#     "KXNASCAR":     "NASCAR",
#     "KXFORMULA":    "F1",
#     "KXOLYMPICS":   "Olympics",
#     "KXSPORTS":     "Sports",
#     "KXMVESPORTS":  "eSports",
#     "KXRAIN":       "Rain",
#     "KXSNOW":       "Snow",
#     "KXTEMP":       "Temp",
#     "KXHURRICANE":  "Hurricane",
#     "KXSTORM":      "Storm",
#     "KXWIND":       "Wind",
#     "KXFLOOD":      "Flood",
#     "KXWX":         "Weather",
# }

# _THRESHOLD_PATTERNS = [
#     # Dollar amounts: > $70,000 / above $1.2M / over 70000
#     (
#         re.compile(r'(?:above|over|exceed|>)\s*\$?([\d,]+(?:\.\d+)?)\s*([KkMm]?)', re.I),
#         lambda m: _fmt_dollar(m.group(1), m.group(2))
#     ),
#     # Percentages — catches "above 0.5%", "> 3%", "0.6%"
#     (
#         re.compile(r'(?:above|over|>|exceed)?\s*([\d.]+)\s*%', re.I),
#         lambda m: f"> {m.group(1)}%"
#     ),
#     # Plain dollar with K/M suffix already written: "$70K", "$1.2M"
#     (
#         re.compile(r'\$\s*([\d.]+)\s*([KkMm])', re.I),
#         lambda m: _fmt_dollar(m.group(1), m.group(2))
#     ),
#     # Direction words
#     (re.compile(r'\b(higher|up|gain|rise|bull)\b', re.I), lambda _: "↑"),
#     (re.compile(r'\b(lower|down|drop|fall|bear)\b', re.I), lambda _: "↓"),
#     (re.compile(r'\bwin\b', re.I),                         lambda _: "Win"),
#     (re.compile(r'\b(loss|lose)\b', re.I),                 lambda _: "Loss"),
# ]


# def _fmt_dollar(digits: str, suffix: str) -> str:
#     """Turn '70000' / '70' / '1.2' + 'K'/'M' into '>$70K' / '>$1.2M'."""
#     val = float(digits.replace(",", ""))
#     s   = suffix.upper()
#     if s == "M" or val >= 1_000_000:
#         return f">${val / 1_000_000:.1f}M".rstrip("0").rstrip(".")
#     if s == "K" or val >= 1_000:
#         return f">${round(val / 1_000)}K"
#     return f">${int(val)}"


# def _extract_threshold(text: str) -> str:
#     """Return a short threshold string from free text, or empty string."""
#     for pattern, formatter in _THRESHOLD_PATTERNS:
#         m = pattern.search(text)
#         if m:
#             return formatter(m)
#     return ""


# def create_card_title(title: str, ticker: str, subtitle: str) -> str:
#     """
#     Build a short card title from ticker + subtitle + title.

#     Priority:
#       1. Sports series → "NBA: Lakers" using yes_sub_title team name
#       2. Subtitle text threshold (most specific — e.g. CPI "above 0.5%")
#       3. Title text threshold
#       4. Ticker-encoded bucket (BTC/ETH price buckets B<price>)
#       5. Direction word fallback (↑ / ↓)
#       6. Raw label only
#       7. Truncated raw title
#     """
#     t    = (ticker or "").upper()
#     sub  = (subtitle or "").strip()
#     titl = (title or "").strip()

#     # ── Step 1: resolve series label ────────────────────────────────
#     label = None
#     for prefix in sorted(SERIES_SHORT, key=len, reverse=True):
#         if t.startswith(prefix):
#             label = SERIES_SHORT[prefix]
#             break

#     # ── Step 2: sports → extract team/player from subtitle ──────────
#     if label in SPORTS_SERIES and sub:
#         team = sub.split("(")[0].strip()          # strip record "(52-30)"
#         parts = team.split()
#         short = parts[-1] if len(team) > 10 and parts else team
#         if short:
#             return f"{label}: {short}"[:20]

#     # ── Step 3: threshold — subtitle first (most specific), then title
#     threshold = _extract_threshold(sub) or _extract_threshold(titl)

#     # ── Step 4: ticker-encoded bucket fallback (BTC/ETH only) ───────
#     if not threshold:
#         bucket_match = re.search(r'B(\d+)', t)
#         if bucket_match and label in {"BTC", "ETH"}:
#             value     = int(bucket_match.group(1))
#             threshold = f">${round(value / 1_000)}K"

#     # ── Step 5: direction word fallback ─────────────────────────────
#     if not threshold:
#         if re.search(r'\babove\b|\bover\b|\bhigher\b|\bexceed', titl, re.I):
#             threshold = "↑"
#         elif re.search(r'\bbelow\b|\bunder\b|\blower\b|\bdrop', titl, re.I):
#             threshold = "↓"

#     # ── Step 6: compose ─────────────────────────────────────────────
#     if label and threshold:
#         return f"{label} {threshold}"[:20]
#     if label:
#         return label[:20]
#     return titl[:20]


# def to_pct(value) -> float:
#     """Convert a Kalshi _dollars field (e.g. "0.5600") to a percentage (56.0)."""
#     try:
#         return float(value or 0) * 100
#     except (TypeError, ValueError):
#         return 0.0


# def parse_market(m: dict) -> Optional[dict]:
#     """
#     Parse a raw Kalshi market dict into our standard schema.

#     Probability priority:
#       1. Bid/ask midpoint
#       2. yes_bid + implied ask (100 - no_bid)
#       3. yes_bid alone
#       4. yes_ask alone
#       5. last_price_dollars
#       6. Default 50
#     """
#     try:
#         ticker = m.get("ticker", "unknown")

#         yes_bid    = to_pct(m.get("yes_bid_dollars"))
#         yes_ask    = to_pct(m.get("yes_ask_dollars"))
#         no_bid     = to_pct(m.get("no_bid_dollars"))
#         last_price = to_pct(m.get("last_price_dollars"))
#         volume     = float(m.get("volume_fp", 0) or 0)

#         # ── Probability cascade ───────────────────────────────────────────────
#         if yes_bid and yes_ask:
#             probability = round((yes_bid + yes_ask) / 2)
#         elif yes_bid:
#             probability = round(yes_bid)
#         elif yes_ask:
#             probability = round(yes_ask)
#         elif last_price:
#             probability = round(last_price)
#         else:
#             probability = 50

#         probability = max(1, min(99, probability))

#         close_time_str = m.get("close_time") or m.get("expiration_time")
#         if not close_time_str:
#             return None

#         close_time        = datetime.fromisoformat(close_time_str.replace("Z", "+00:00"))
#         hours_until_close = (close_time - datetime.now(timezone.utc)).total_seconds() / 3600

#         series_ticker = m.get("series_ticker", "") or ""
#         title         = m.get("title", "")
#         subtitle      = m.get("yes_sub_title", "")

#         return {
#             "ticker":            ticker,
#             "series_ticker":     series_ticker,
#             "title":             title,
#             "yes_sub_title":     subtitle,
#             "subtitle":          m.get("subtitle", ""),
#             "card_title":        create_card_title(title, ticker, subtitle),
#             "probability":       probability,
#             "yes_bid":           round(yes_bid, 2),
#             "yes_ask":           round(yes_ask, 2),
#             "last_price":        round(last_price, 2),
#             "volume":            volume,
#             "close_time":        close_time_str,
#             "hours_until_close": round(hours_until_close, 1),
#             "status":            m.get("status", ""),
#             "category":          classify_market(title, series_ticker),
#         }
#     except Exception as e:
#         logger.warning(f"Failed to parse market {m.get('ticker')}: {e}")
#         return None


# def apply_filters(
#     pool: list[dict],
#     max_hours: float,
#     min_volume: float,
#     min_prob: int,
#     max_prob: int,
# ) -> list[dict]:
#     return [
#         m for m in pool
#         if m["status"] == "active"
#         and m["hours_until_close"] <= max_hours
#         and min_prob <= m["probability"] <= max_prob
#         and m["volume"] >= min_volume
#     ]


# def rank(pool: list[dict]) -> list[dict]:
#     """Sort by: highest volume → soonest close → shortest title."""
#     return sorted(
#         pool,
#         key=lambda x: (-x["volume"], x["hours_until_close"], len(x["title"])),
#     )


# def dedupe_series(pool: list[dict]) -> list[dict]:
#     """
#     Keep only the best (first after ranking) market per series_ticker.
#     Falls back to ticker itself when series_ticker is absent.
#     Must be called AFTER rank() so the highest-volume market wins.
#     """
#     seen: set[str] = set()
#     result: list[dict] = []
#     for m in pool:
#         series = m.get("series_ticker") or m["ticker"]
#         if series not in seen:
#             seen.add(series)
#             result.append(m)
#     return result


# # ─── Data fetchers ────────────────────────────────────────────────────────────

# async def fetch_by_category(category: str, limit: int = 50) -> list[dict]:
#     """Fetch markets for every series ticker in a category."""
#     series_list = SERIES_TICKERS.get(category, [])
#     results: list[dict] = []
#     async with httpx.AsyncClient(timeout=10) as client:
#         for series in series_list:
#             try:
#                 resp = await client.get(
#                     f"{KALSHI_BASE_URL}/markets",
#                     params={"status": "open", "series_ticker": series, "limit": limit},
#                 )
#                 if resp.status_code == 200:
#                     for m in resp.json().get("markets", []):
#                         parsed = parse_market(m)
#                         if parsed:
#                             results.append(parsed)
#             except httpx.HTTPError:
#                 continue
#     logger.info(f"fetch_by_category({category}) → {len(results)} markets")
#     return results


# async def fetch_global(limit: int = 200) -> list[dict]:
#     """Fetch open markets globally (last-resort fallback)."""
#     async with httpx.AsyncClient(timeout=10) as client:
#         try:
#             resp = await client.get(
#                 f"{KALSHI_BASE_URL}/markets",
#                 params={"status": "open", "limit": limit},
#             )
#             resp.raise_for_status()
#             return [
#                 p
#                 for p in (parse_market(m) for m in resp.json().get("markets", []))
#                 if p
#             ]
#         except httpx.HTTPError as e:
#             raise HTTPException(status_code=502, detail=f"Kalshi API error: {str(e)}")


# def top_for_category(pool: list[dict], n: int = 10) -> list[dict]:
#     """
#     Apply cascading filters, rank, dedupe by series, return top-n.

#     Order matters:
#       1. rank()          — best market per series floats to the top
#       2. dedupe_series() — drop duplicate series, keeping only the best
#       3. [:n]            — slice after dedup so n reflects unique series
#     """
#     candidates = (
#         apply_filters(pool, max_hours=48,  min_volume=100, min_prob=10, max_prob=90)
      
#     )
#     return dedupe_series(rank(candidates))[:n]


# def normalize_title(title: str) -> str:
#     return title.lower().strip()


# # ─── Routes ───────────────────────────────────────────────────────────────────

# @app.get("/health")
# def health():
#     return {"status": "ok", "time": datetime.now(timezone.utc).isoformat()}


# # ── /debug/markets ────────────────────────────────────────────────────────────
# @app.get("/debug/markets")
# async def debug_markets():
#     """
#     Debug endpoint — raw filter diagnostics from Kalshi.
#     Uses _dollars fields (current v2 API).
#     """
#     async with httpx.AsyncClient(timeout=10) as client:
#         try:
#             resp = await client.get(
#                 f"{KALSHI_BASE_URL}/markets",
#                 params={"status": "open", "limit": 20},
#             )
#             resp.raise_for_status()
#         except httpx.HTTPError as e:
#             raise HTTPException(status_code=502, detail=f"Kalshi API error: {str(e)}")

#     now     = datetime.now(timezone.utc)
#     markets = resp.json().get("markets", [])
#     sample  = []

#     for m in markets[:20]:
#         yes_bid    = to_pct(m.get("yes_bid_dollars"))
#         yes_ask    = to_pct(m.get("yes_ask_dollars"))
#         no_bid     = to_pct(m.get("no_bid_dollars"))
#         last_price = to_pct(m.get("last_price_dollars"))

#         if yes_bid and yes_ask:
#             probability = round((yes_bid + yes_ask) / 2)
#         elif yes_bid and no_bid:
#             probability = round((yes_bid + (100 - no_bid)) / 2)
#         elif yes_bid:
#             probability = round(yes_bid)
#         elif yes_ask:
#             probability = round(yes_ask)
#         elif last_price:
#             probability = round(last_price)
#         else:
#             probability = 0

#         close_time_str = m.get("close_time") or m.get("expiration_time")
#         hours_left     = None
#         if close_time_str:
#             try:
#                 ct         = datetime.fromisoformat(close_time_str.replace("Z", "+00:00"))
#                 hours_left = round((ct - now).total_seconds() / 3600, 1)
#             except Exception:
#                 pass

#         volume = float(m.get("volume_fp") or m.get("volume") or 0)

#         sample.append({
#             "ticker":        m.get("ticker"),
#             "title":         m.get("title"),
#             "status":        m.get("status"),
#             "probability":   probability,
#             "yes_bid":       round(yes_bid, 2),
#             "yes_ask":       round(yes_ask, 2),
#             "last_price":    round(last_price, 2),
#             "volume":        volume,
#             "hours_left":    hours_left,
#             "passes_status": m.get("status") == "active",
#             "passes_hours":  hours_left is not None and hours_left <= 48,
#             "passes_prob":   10 <= probability <= 90,
#             "passes_volume": volume >= 100,
#             "all_pass": (
#                 m.get("status") == "active"
#                 and hours_left is not None and hours_left <= 48
#                 and 10 <= probability <= 90
#                 and volume >= 100
#             ),
#         })

#     passing = [s for s in sample if s["all_pass"]]
#     return {
#         "total_returned":  len(markets),
#         "sample_size":     len(sample),
#         "passing_filters": len(passing),
#         "sample":          sample,
#     }


# # ── /markets/ticker ───────────────────────────────────────────────────────────
# @app.get("/markets/ticker")
# async def get_ticker_markets():
#     """
#     Returns 3–5 live markets for the probability ticker.
#     Guarantees:
#       - Minimum 3 markets always returned.
#       - Maximum 5 markets.
#       - No duplicate tickers, titles, or series.
#       - At most 2 markets per category.
#       - At least 1 market per category when data is available.
#       - If a category fails, compensates from other categories → MIN 3.

#     Steps:
#       1. Fetch each category independently via series tickers.
#       2. Global fallback for any completely empty category pool.
#       3. Pre-compute top-10 per category: rank → dedupe_series → slice.
#       4. Guarantee 1 per category (best effort, skipping dupes).
#       5. Compensate missing slots from other categories → MIN 3.
#       6. Fill remaining slots up to 5 → MAX 5 (capped at 2 per category).
#     """
#     now = datetime.now(timezone.utc)

#     # ── Step 1: Fetch per category ────────────────────────────────────────────
#     category_pool: dict[str, list[dict]] = {}
#     for cat in SERIES_TICKERS:
#         category_pool[cat] = await fetch_by_category(cat, limit=1000)

#     # ── Step 2: Global fallback for empty categories ──────────────────────────
#     empty_cats = [cat for cat, pool in category_pool.items() if not pool]
#     if empty_cats:
#         logger.warning(f"Empty pools for {empty_cats} — trying global fetch")
#         global_markets = await fetch_global(limit=200)
#         for m in global_markets:
#             if m["category"] in empty_cats:
#                 category_pool[m["category"]].append(m)

#     # ── Step 3: Pre-compute top-10 per category (ranked + series-deduped) ─────
#     category_tops: dict[str, list[dict]] = {
#         cat: top_for_category(category_pool[cat], n=10)
#         for cat in SERIES_TICKERS
#     }
#     for cat, tops in category_tops.items():
#         logger.info(
#             f"[{cat}] top candidates: {len(tops)} — "
#             f"{[m['ticker'] for m in tops]}"
#         )

#     # ── Dedup + per-category cap state ───────────────────────────────────────
#     picked: list[dict]              = []
#     seen_tickers: set[str]          = set()
#     seen_titles: set[str]           = set()
#     seen_series: set[str]           = set()
#     category_counts: dict[str, int] = {cat: 0 for cat in SERIES_TICKERS}
#     MAX_PER_CATEGORY                = 2

#     def try_add(market: dict) -> bool:
#         """
#         Add market only if:
#           - ticker unseen
#           - normalized title unseen
#           - series_ticker unseen (no same-series duplicates)
#           - category hasn't hit MAX_PER_CATEGORY (2)
#         """
#         ticker     = market["ticker"]
#         norm_title = normalize_title(market["title"])
#         cat        = market["category"]
#         series     = market.get("series_ticker") or ticker

#         if ticker in seen_tickers or norm_title in seen_titles:
#             return False
#         if series in seen_series:
#             return False
#         if category_counts.get(cat, 0) >= MAX_PER_CATEGORY:
#             return False

#         picked.append(market)
#         seen_tickers.add(ticker)
#         seen_titles.add(norm_title)
#         seen_series.add(series)
#         category_counts[cat] = category_counts.get(cat, 0) + 1
#         return True

#     # ── Step 4: Guarantee 1 per category ─────────────────────────────────────
#     failed_cats: list[str] = []
#     for cat in SERIES_TICKERS:
#         added = False
#         for candidate in category_tops[cat]:
#             if try_add(candidate):
#                 logger.info(
#                     f"[{cat}] Guaranteed pick: "
#                     f"{candidate['ticker']} | '{candidate['title']}'"
#                 )
#                 added = True
#                 break
#         if not added:
#             logger.warning(f"[{cat}] No unique market — will compensate")
#             failed_cats.append(cat)

#     # ── Step 5: Compensate for failed categories → MIN 3 ─────────────────────
#     if failed_cats:
#         needed = len(failed_cats)
#         logger.warning(f"Compensating {needed} missing slot(s) from runner-ups")

#         compensation_pool = rank([
#             m
#             for cat in SERIES_TICKERS
#             if cat not in failed_cats
#             for m in category_tops[cat]
#         ])
#         for candidate in compensation_pool:
#             if needed <= 0:
#                 break
#             if try_add(candidate):
#                 logger.info(
#                     f"Compensation fill: "
#                     f"{candidate['ticker']} | '{candidate['title']}'"
#                 )
#                 needed -= 1

#         if len(picked) < 3:
#             logger.error(
#                 f"Could only pick {len(picked)} markets — "
#                 "Kalshi data may be too thin"
#             )

#     # ── Step 6: Fill up to MAX 5 with per-category runner-ups ────────────────
#     for cat in SERIES_TICKERS:
#         if len(picked) >= 5:
#             break
#         for candidate in category_tops[cat]:
#             if len(picked) >= 5:
#                 break
#             if try_add(candidate):
#                 logger.info(
#                     f"[{cat}] Runner-up fill: "
#                     f"{candidate['ticker']} | '{candidate['title']}'"
#                 )

#     picked = rank(picked)
#     logger.info(f"/markets/ticker — returning {len(picked)} markets (min=3, max=5)")
#     return {"markets": picked, "fetched_at": now.isoformat()}


# # ── /markets/daily ────────────────────────────────────────────────────────────
# @app.get("/markets/daily")
# async def get_daily_question():
#     """
#     Returns the single daily question market based on day-of-week rotation.

#     Category rotation:
#       Mon/Thu → finance | Tue/Fri/Sat → sports | Wed/Sun → weather

#     Filter cascade (always stays within the target category):
#       1. Strict:      close<=24h, vol>=500, prob 20-80%
#       2. Fallback 1:  close<=24h, vol>=100, prob 20-80%
#       3. Fallback 2:  close<=48h, vol>=100, prob 10-90%
#       4. Last resort: any active market in target category
#     """
#     today           = datetime.now(timezone.utc)
#     target_category = DAY_CATEGORY[today.weekday()]
#     logger.info(
#         f"/markets/daily — target_category={target_category} "
#         f"(weekday={today.weekday()})"
#     )

#     def pick_best(pool: list[dict]) -> Optional[dict]:
#         filtered = [
#             m for m in pool
#             if m["status"] == "active"
#             and m["category"] == target_category
#         ]
#         if not filtered:
#             return None

#         candidates = (
#             apply_filters(filtered, max_hours=24, min_volume=500, min_prob=20, max_prob=80)
#             or apply_filters(filtered, max_hours=24, min_volume=100, min_prob=20, max_prob=80)
#         )

#         short = [m for m in candidates if len(m["title"]) <= 80]
#         final = short if short else candidates

#         return rank(final)[0] if final else None

#     # Step 1: fetch via series tickers
#     pool   = await fetch_by_category(target_category, limit=500)
#     chosen = pick_best(pool)
#     if chosen:
#         logger.info(f"Chose market from series fetch: {chosen['ticker']}")

#     # Step 2: global fetch, still target category only
#     if not chosen:
#         logger.warning(
#             f"Series fetch found nothing for {target_category} — "
#             "trying global fetch"
#         )
#         all_markets = await fetch_global(limit=200)
#         chosen      = pick_best(all_markets)
#         if chosen:
#             logger.info(f"Chose market from global fetch: {chosen['ticker']}")

#     if not chosen:
#         raise HTTPException(
#             status_code=404,
#             detail=f"No {target_category} market found for today",
#         )

#     return {
#         "market":          chosen,
#         "target_category": target_category,
#         "date":            today.date().isoformat(),
#     }


# # ── /markets/{ticker} ─────────────────────────────────────────────────────────
# @app.get("/markets/{ticker}")
# async def get_market_result(ticker: str):
#     """
#     Fetch a specific market by ticker.
#     Used by the iOS app the next day to check the result.

#     result field:
#       null  → still open / not yet resolved
#       "yes" → resolved YES
#       "no"  → resolved NO
#     """
#     async with httpx.AsyncClient(timeout=10) as client:
#         try:
#             resp = await client.get(f"{KALSHI_BASE_URL}/markets/{ticker}")
#             resp.raise_for_status()
#         except httpx.HTTPError as e:
#             raise HTTPException(status_code=502, detail=f"Kalshi API error: {str(e)}")

#     market = resp.json().get("market", {})
#     parsed = parse_market(market)
#     if not parsed:
#         raise HTTPException(status_code=422, detail="Could not parse market data")

#     parsed["result"] = market.get("result")   # null | "yes" | "no"
#     return {"market": parsed}








# import re
# import asyncio
# from fastapi import FastAPI, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# import httpx
# from datetime import datetime, timezone
# from typing import Optional
# import logging
# from collections import defaultdict


# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# app = FastAPI(title="Kalshi Probability Proxy", version="2.0.0")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# KALSHI_BASE_URL = "https://api.elections.kalshi.com/trade-api/v2"
# KALSHI_EXTERNAL_URL = "https://external-api.kalshi.com/trade-api/v2"

# # ─── Finance: hardcoded (stable, predictable series) ─────────────────────────
# FINANCE_SERIES: list[str] = [
#     "KXBTC", "KXETH", "KXCRYPTO", "KXSP500", "KXNASDAQ",
#     "KXDOW", "KXFED", "KXCPI", "KXGDP", "KXOIL", "KXGOLD",
#     "KXRATES", "KXJOBS", "KXECON", "KXSTOCKS",
# ]

# # ─── Sports + Weather: populated dynamically at startup ──────────────────────
# # Keys match the Kalshi category query param exactly.
# DYNAMIC_CATEGORY_MAP: dict[str, str] = {
#     "Sports": "sports",
#     "Climate and Weather": "weather",
# }

# # This dict is mutated at startup by _load_dynamic_series().
# SERIES_TICKERS: dict[str, list[str]] = {
#     "finance": FINANCE_SERIES,
#     "sports":  [],   # filled at startup
#     "weather": [],   # filled at startup
# }


# async def _fetch_series_for_category(kalshi_category: str) -> list[str]:
#     """
#     Call GET /series?category=<kalshi_category> and return all series tickers.
#     Returns an empty list on any error so the app still starts.
#     """
#     async with httpx.AsyncClient(timeout=15) as client:
#         try:
#             resp = await client.get(
#                 f"{KALSHI_EXTERNAL_URL}/series",
#                 params={"category": kalshi_category},
#             )
#             resp.raise_for_status()
#             series_list = resp.json().get("series", [])
#             tickers = [s["ticker"] for s in series_list if s.get("ticker")]
#             logger.info(
#                 f"_fetch_series_for_category({kalshi_category!r}) "
#                 f"→ {len(tickers)} tickers"
#             )
#             return tickers
#         except Exception as e:
#             logger.error(
#                 f"Failed to fetch series for category {kalshi_category!r}: {e}"
#             )
#             return []


# async def _load_dynamic_series() -> None:
#     """
#     Fetch sports and weather series concurrently and populate SERIES_TICKERS.
#     Called once from the startup event.
#     """
#     results = await asyncio.gather(
#         *[
#             _fetch_series_for_category(kalshi_cat)
#             for kalshi_cat in DYNAMIC_CATEGORY_MAP
#         ]
#     )
#     for (kalshi_cat, app_cat), tickers in zip(DYNAMIC_CATEGORY_MAP.items(), results):
#         if tickers:
#             SERIES_TICKERS[app_cat] = tickers
#             logger.info(
#                 f"Loaded {len(tickers)} {app_cat} series tickers from Kalshi"
#             )
#         else:
#             logger.warning(
#                 f"No tickers loaded for {app_cat} — "
#                 "using empty list (fallback to global fetch will apply)"
#             )


# @app.on_event("startup")
# async def startup_event() -> None:
#     await _load_dynamic_series()


# # ─── Category keywords (title-based fallback classifier) ─────────────────────
# CATEGORY_KEYWORDS: dict[str, list[str]] = {
#     "finance": [
#         "s&p", "btc", "bitcoin", "nasdaq", "dow", "fed", "rate", "inflation",
#         "ethereum", "eth", "crypto", "stock", "market", "gdp", "cpi",
#         "interest", "bond", "oil", "gold", "dollar", "economy", "recession",
#         "earnings", "ipo", "index", "trade", "tariff", "jobs", "unemployment",
#     ],
#     "sports": [
#         "nba", "nfl", "mlb", "nhl", "ncaa", "win", "game", "championship",
#         "playoff", "match", "tournament", "league", "cup", "super bowl",
#         "world series", "finals", "score", "team", "player", "season",
#         "mls", "ufc", "mma", "boxing", "golf", "tennis", "formula", "nascar",
#         "olympic", "soccer", "football", "basketball", "baseball", "hockey",
#     ],
#     "weather": [
#         "rain", "snow", "temperature", "weather", "storm", "hurricane",
#         "tornado", "flood", "wind", "celsius", "fahrenheit", "forecast",
#         "precipitation", "drought", "wildfire", "hail", "blizzard",
#     ],
# }

# # Day-of-week → category rotation
# DAY_CATEGORY: dict[int, str] = {
#     0: "finance",   # Mon
#     1: "sports",    # Tue
#     2: "weather",   # Wed
#     3: "finance",   # Thu
#     4: "sports",    # Fri
#     5: "sports",    # Sat
#     6: "weather",   # Sun
# }

# # Sports series that benefit from team-name extraction in card titles
# SPORTS_SERIES: set[str] = {
#     "NBA", "NFL", "MLB", "NHL", "NCAA BB", "NCAA FB",
#     "Soccer", "MMA", "Boxing", "Tennis", "Golf", "F1", "NASCAR",
# }


# # ─── Helpers ──────────────────────────────────────────────────────────────────

# def _build_series_prefix_map() -> dict[str, str]:
#     """Build series prefix → category map from current SERIES_TICKERS."""
#     return {
#         prefix.upper(): cat
#         for cat, prefixes in SERIES_TICKERS.items()
#         for prefix in prefixes
#     }


# def classify_market(title: str, series_ticker: str = "") -> str:
#     """
#     1. Series prefix match (most reliable) — rebuilt each call so it
#        reflects dynamically loaded series.
#     2. Title keyword match
#     3. Default → finance
#     """
#     prefix_map = _build_series_prefix_map()
#     st = (series_ticker or "").upper()
#     for prefix, category in prefix_map.items():
#         if st.startswith(prefix):
#             return category

#     title_lower = title.lower()
#     for category, keywords in CATEGORY_KEYWORDS.items():
#         if any(kw in title_lower for kw in keywords):
#             return category

#     logger.debug(
#         f"classify_market: no match for title='{title}' "
#         f"series='{series_ticker}', defaulting to finance"
#     )
#     return "finance"


# def format_k(value: int) -> str:
#     return f"{round(value / 1000)}K"


# # Series prefix → human-readable short label
# SERIES_SHORT: dict[str, str] = {
#     "KXBTC":        "BTC",
#     "KXETH":        "ETH",
#     "KXCRYPTO":     "Crypto",
#     "KXSP500":      "S&P 500",
#     "KXNASDAQ":     "Nasdaq",
#     "KXDOW":        "Dow",
#     "KXFED":        "Fed Rate",
#     "KXCPI":        "CPI",
#     "KXGDP":        "GDP",
#     "KXOIL":        "Oil",
#     "KXGOLD":       "Gold",
#     "KXRATES":      "Rates",
#     "KXJOBS":       "Jobs",
#     "KXNBA":        "NBA",
#     "KXNFL":        "NFL",
#     "KXMLB":        "MLB",
#     "KXNHL":        "NHL",
#     "KXNCAAB":      "NCAA BB",
#     "KXNCAAF":      "NCAA FB",
#     "KXSOCCER":     "Soccer",
#     "KXMMA":        "MMA",
#     "KXBOXING":     "Boxing",
#     "KXGOLF":       "Golf",
#     "KXTENNIS":     "Tennis",
#     "KXNASCAR":     "NASCAR",
#     "KXFORMULA":    "F1",
#     "KXOLYMPICS":   "Olympics",
#     "KXSPORTS":     "Sports",
#     "KXMVESPORTS":  "eSports",
#     "KXRAIN":       "Rain",
#     "KXSNOW":       "Snow",
#     "KXTEMP":       "Temp",
#     "KXHURRICANE":  "Hurricane",
#     "KXSTORM":      "Storm",
#     "KXWIND":       "Wind",
#     "KXFLOOD":      "Flood",
#     "KXWX":         "Weather",
# }

# _THRESHOLD_PATTERNS = [
#     (
#         re.compile(r'(?:above|over|exceed|>)\s*\$?([\d,]+(?:\.\d+)?)\s*([KkMm]?)', re.I),
#         lambda m: _fmt_dollar(m.group(1), m.group(2))
#     ),
#     (
#         re.compile(r'(?:above|over|>|exceed)?\s*([\d.]+)\s*%', re.I),
#         lambda m: f"> {m.group(1)}%"
#     ),
#     (
#         re.compile(r'\$\s*([\d.]+)\s*([KkMm])', re.I),
#         lambda m: _fmt_dollar(m.group(1), m.group(2))
#     ),
#     (re.compile(r'\b(higher|up|gain|rise|bull)\b', re.I), lambda _: "↑"),
#     (re.compile(r'\b(lower|down|drop|fall|bear)\b', re.I), lambda _: "↓"),
#     (re.compile(r'\bwin\b', re.I),                         lambda _: "Win"),
#     (re.compile(r'\b(loss|lose)\b', re.I),                 lambda _: "Loss"),
# ]


# def _fmt_dollar(digits: str, suffix: str) -> str:
#     val = float(digits.replace(",", ""))
#     s   = suffix.upper()
#     if s == "M" or val >= 1_000_000:
#         return f">${val / 1_000_000:.1f}M".rstrip("0").rstrip(".")
#     if s == "K" or val >= 1_000:
#         return f">${round(val / 1_000)}K"
#     return f">${int(val)}"


# def _extract_threshold(text: str) -> str:
#     for pattern, formatter in _THRESHOLD_PATTERNS:
#         m = pattern.search(text)
#         if m:
#             return formatter(m)
#     return ""


# def create_card_title(title: str, ticker: str, subtitle: str) -> str:
#     t    = (ticker or "").upper()
#     sub  = (subtitle or "").strip()
#     titl = (title or "").strip()

#     label = None
#     for prefix in sorted(SERIES_SHORT, key=len, reverse=True):
#         if t.startswith(prefix):
#             label = SERIES_SHORT[prefix]
#             break

#     if label in SPORTS_SERIES and sub:
#         team = sub.split("(")[0].strip()
#         parts = team.split()
#         short = parts[-1] if len(team) > 10 and parts else team
#         if short:
#             return f"{label}: {short}"[:20]

#     threshold = _extract_threshold(sub) or _extract_threshold(titl)

#     if not threshold:
#         bucket_match = re.search(r'B(\d+)', t)
#         if bucket_match and label in {"BTC", "ETH"}:
#             value     = int(bucket_match.group(1))
#             threshold = f">${round(value / 1_000)}K"

#     if not threshold:
#         if re.search(r'\babove\b|\bover\b|\bhigher\b|\bexceed', titl, re.I):
#             threshold = "↑"
#         elif re.search(r'\bbelow\b|\bunder\b|\blower\b|\bdrop', titl, re.I):
#             threshold = "↓"

#     if label and threshold:
#         return f"{label} {threshold}"[:20]
#     if label:
#         return label[:20]
#     return titl[:20]


# def to_pct(value) -> float:
#     try:
#         return float(value or 0) * 100
#     except (TypeError, ValueError):
#         return 0.0


# def parse_market(m: dict) -> Optional[dict]:
#     try:
#         ticker = m.get("ticker", "unknown")

#         yes_bid    = to_pct(m.get("yes_bid_dollars"))
#         yes_ask    = to_pct(m.get("yes_ask_dollars"))
#         no_bid     = to_pct(m.get("no_bid_dollars"))
#         last_price = to_pct(m.get("last_price_dollars"))
#         volume     = float(m.get("volume_fp", 0) or 0)

#         if yes_bid and yes_ask:
#             probability = round((yes_bid + yes_ask) / 2)
#         elif yes_bid and no_bid:
#             implied_yes_ask = 100 - no_bid
#             probability = round((yes_bid + implied_yes_ask) / 2)
#         elif yes_bid:
#             probability = round(yes_bid)
#         elif yes_ask:
#             probability = round(yes_ask)
#         elif last_price:
#             probability = round(last_price)
#         else:
#             probability = 50

#         probability = max(1, min(99, probability))

#         close_time_str = m.get("close_time") or m.get("expiration_time")
#         if not close_time_str:
#             return None

#         close_time        = datetime.fromisoformat(close_time_str.replace("Z", "+00:00"))
#         hours_until_close = (close_time - datetime.now(timezone.utc)).total_seconds() / 3600

#         series_ticker = m.get("series_ticker", "") or ""
#         title         = m.get("title", "")
#         subtitle      = m.get("yes_sub_title", "")

#         return {
#             "ticker":            ticker,
#             "series_ticker":     series_ticker,
#             "title":             title,
#             "yes_sub_title":     subtitle,
#             "subtitle":          m.get("subtitle", ""),
#             "card_title":        create_card_title(title, ticker, subtitle),
#             "probability":       probability,
#             "yes_bid":           round(yes_bid, 2),
#             "yes_ask":           round(yes_ask, 2),
#             "last_price":        round(last_price, 2),
#             "volume":            volume,
#             "close_time":        close_time_str,
#             "hours_until_close": round(hours_until_close, 1),
#             "status":            m.get("status", ""),
#             "category":          classify_market(title, series_ticker),
#         }
#     except Exception as e:
#         logger.warning(f"Failed to parse market {m.get('ticker')}: {e}")
#         return None


# def apply_filters(
#     pool: list[dict],
#     max_hours: float,
#     min_volume: float,
#     min_prob: int,
#     max_prob: int,
# ) -> list[dict]:
#     return [
#         m for m in pool
#         if m["status"] == "active"
#         and m["hours_until_close"] <= max_hours
#         and min_prob <= m["probability"] <= max_prob
#         and m["volume"] >= min_volume
#     ]


# def rank(pool: list[dict]) -> list[dict]:
#     return sorted(
#         pool,
#         key=lambda x: (-x["volume"], x["hours_until_close"], len(x["title"])),
#     )


# def dedupe_series(pool: list[dict]) -> list[dict]:
#     seen: set[str] = set()
#     result: list[dict] = []
#     for m in pool:
#         series = m.get("series_ticker") or m["ticker"]
#         if series not in seen:
#             seen.add(series)
#             result.append(m)
#     return result


# # ─── Data fetchers ────────────────────────────────────────────────────────────

# async def fetch_by_category(category: str, limit: int = 50) -> list[dict]:
#     """Fetch markets for every series ticker in a category."""
#     series_list = SERIES_TICKERS.get(category, [])
#     results: list[dict] = []
#     async with httpx.AsyncClient(timeout=10) as client:
#         for series in series_list:
#             try:
#                 resp = await client.get(
#                     f"{KALSHI_BASE_URL}/markets",
#                     params={"status": "open", "series_ticker": series, "limit": limit},
#                 )
#                 if resp.status_code == 200:
#                     for m in resp.json().get("markets", []):
#                         parsed = parse_market(m)
#                         if parsed:
#                             results.append(parsed)
#             except httpx.HTTPError:
#                 continue
#     logger.info(f"fetch_by_category({category}) → {len(results)} markets")
#     return results


# async def fetch_global(limit: int = 200) -> list[dict]:
#     """Fetch open markets globally (last-resort fallback)."""
#     async with httpx.AsyncClient(timeout=10) as client:
#         try:
#             resp = await client.get(
#                 f"{KALSHI_BASE_URL}/markets",
#                 params={"status": "open", "limit": limit},
#             )
#             resp.raise_for_status()
#             return [
#                 p
#                 for p in (parse_market(m) for m in resp.json().get("markets", []))
#                 if p
#             ]
#         except httpx.HTTPError as e:
#             raise HTTPException(status_code=502, detail=f"Kalshi API error: {str(e)}")


# def top_for_category(pool: list[dict], n: int = 10) -> list[dict]:
#     candidates = (
#         apply_filters(pool, max_hours=48,  min_volume=100, min_prob=10, max_prob=90)
#         # or apply_filters(pool, max_hours=168, min_volume=10,  min_prob=5,  max_prob=95)
#         # or apply_filters(pool, max_hours=720, min_volume=0,   min_prob=1,  max_prob=99)
#         # or [m for m in pool if m["status"] == "active"]
#     )
#     return dedupe_series(rank(candidates))[:n]


# def normalize_title(title: str) -> str:
#     return title.lower().strip()


# # ─── Routes ───────────────────────────────────────────────────────────────────

# @app.get("/health")
# def health():
#     return {
#         "status": "ok",
#         "time": datetime.now(timezone.utc).isoformat(),
#         "series_counts": {cat: len(tickers) for cat, tickers in SERIES_TICKERS.items()},
#     }


# @app.get("/series/reload")
# async def reload_series():
#     """
#     Manually re-fetch sports and weather series from Kalshi.
#     Useful for refreshing without a full server restart.
#     """
#     await _load_dynamic_series()
#     return {
#         "status": "reloaded",
#         "series_counts": {cat: len(tickers) for cat, tickers in SERIES_TICKERS.items()},
#     }


# # ── /debug/markets ────────────────────────────────────────────────────────────
# @app.get("/debug/markets")
# async def debug_markets():
#     async with httpx.AsyncClient(timeout=10) as client:
#         try:
#             resp = await client.get(
#                 f"{KALSHI_BASE_URL}/markets",
#                 params={"status": "open", "limit": 20},
#             )
#             resp.raise_for_status()
#         except httpx.HTTPError as e:
#             raise HTTPException(status_code=502, detail=f"Kalshi API error: {str(e)}")

#     now     = datetime.now(timezone.utc)
#     markets = resp.json().get("markets", [])
#     sample  = []

#     for m in markets[:20]:
#         yes_bid    = to_pct(m.get("yes_bid_dollars"))
#         yes_ask    = to_pct(m.get("yes_ask_dollars"))
#         no_bid     = to_pct(m.get("no_bid_dollars"))
#         last_price = to_pct(m.get("last_price_dollars"))

#         if yes_bid and yes_ask:
#             probability = round((yes_bid + yes_ask) / 2)
#         elif yes_bid and no_bid:
#             probability = round((yes_bid + (100 - no_bid)) / 2)
#         elif yes_bid:
#             probability = round(yes_bid)
#         elif yes_ask:
#             probability = round(yes_ask)
#         elif last_price:
#             probability = round(last_price)
#         else:
#             probability = 0

#         close_time_str = m.get("close_time") or m.get("expiration_time")
#         hours_left     = None
#         if close_time_str:
#             try:
#                 ct         = datetime.fromisoformat(close_time_str.replace("Z", "+00:00"))
#                 hours_left = round((ct - now).total_seconds() / 3600, 1)
#             except Exception:
#                 pass

#         volume = float(m.get("volume_fp") or m.get("volume") or 0)

#         sample.append({
#             "ticker":        m.get("ticker"),
#             "title":         m.get("title"),
#             "status":        m.get("status"),
#             "probability":   probability,
#             "yes_bid":       round(yes_bid, 2),
#             "yes_ask":       round(yes_ask, 2),
#             "last_price":    round(last_price, 2),
#             "volume":        volume,
#             "hours_left":    hours_left,
#             "passes_status": m.get("status") == "active",
#             "passes_hours":  hours_left is not None and hours_left <= 48,
#             "passes_prob":   10 <= probability <= 90,
#             "passes_volume": volume >= 100,
#             "all_pass": (
#                 m.get("status") == "active"
#                 and hours_left is not None and hours_left <= 48
#                 and 10 <= probability <= 90
#                 and volume >= 100
#             ),
#         })

#     passing = [s for s in sample if s["all_pass"]]
#     return {
#         "total_returned":  len(markets),
#         "sample_size":     len(sample),
#         "passing_filters": len(passing),
#         "sample":          sample,
#     }


# # ── /markets/ticker ───────────────────────────────────────────────────────────
# @app.get("/markets/ticker")
# async def get_ticker_markets():
#     now = datetime.now(timezone.utc)

#     category_pool: dict[str, list[dict]] = {}
#     for cat in SERIES_TICKERS:
#         category_pool[cat] = await fetch_by_category(cat, limit=1000)

#     empty_cats = [cat for cat, pool in category_pool.items() if not pool]
#     if empty_cats:
#         logger.warning(f"Empty pools for {empty_cats} — trying global fetch")
#         global_markets = await fetch_global(limit=200)
#         for m in global_markets:
#             if m["category"] in empty_cats:
#                 category_pool[m["category"]].append(m)

#     category_tops: dict[str, list[dict]] = {
#         cat: top_for_category(category_pool[cat], n=10)
#         for cat in SERIES_TICKERS
#     }
#     for cat, tops in category_tops.items():
#         logger.info(
#             f"[{cat}] top candidates: {len(tops)} — "
#             f"{[m['ticker'] for m in tops]}"
#         )

#     picked: list[dict]              = []
#     seen_tickers: set[str]          = set()
#     seen_titles: set[str]           = set()
#     seen_series: set[str]           = set()
#     category_counts: dict[str, int] = {cat: 0 for cat in SERIES_TICKERS}
#     MAX_PER_CATEGORY                = 2

#     def try_add(market: dict) -> bool:
#         ticker     = market["ticker"]
#         norm_title = normalize_title(market["title"])
#         cat        = market["category"]
#         series     = market.get("series_ticker") or ticker

#         if ticker in seen_tickers or norm_title in seen_titles:
#             return False
#         if series in seen_series:
#             return False
#         if category_counts.get(cat, 0) >= MAX_PER_CATEGORY:
#             return False

#         picked.append(market)
#         seen_tickers.add(ticker)
#         seen_titles.add(norm_title)
#         seen_series.add(series)
#         category_counts[cat] = category_counts.get(cat, 0) + 1
#         return True

#     failed_cats: list[str] = []
#     for cat in SERIES_TICKERS:
#         added = False
#         for candidate in category_tops[cat]:
#             if try_add(candidate):
#                 logger.info(
#                     f"[{cat}] Guaranteed pick: "
#                     f"{candidate['ticker']} | '{candidate['title']}'"
#                 )
#                 added = True
#                 break
#         if not added:
#             logger.warning(f"[{cat}] No unique market — will compensate")
#             failed_cats.append(cat)

#     if failed_cats:
#         needed = len(failed_cats)
#         logger.warning(f"Compensating {needed} missing slot(s) from runner-ups")

#         compensation_pool = rank([
#             m
#             for cat in SERIES_TICKERS
#             if cat not in failed_cats
#             for m in category_tops[cat]
#         ])
#         for candidate in compensation_pool:
#             if needed <= 0:
#                 break
#             if try_add(candidate):
#                 logger.info(
#                     f"Compensation fill: "
#                     f"{candidate['ticker']} | '{candidate['title']}'"
#                 )
#                 needed -= 1

#         if len(picked) < 3:
#             logger.error(
#                 f"Could only pick {len(picked)} markets — "
#                 "Kalshi data may be too thin"
#             )

#     for cat in SERIES_TICKERS:
#         if len(picked) >= 5:
#             break
#         for candidate in category_tops[cat]:
#             if len(picked) >= 5:
#                 break
#             if try_add(candidate):
#                 logger.info(
#                     f"[{cat}] Runner-up fill: "
#                     f"{candidate['ticker']} | '{candidate['title']}'"
#                 )

#     picked = rank(picked)
#     logger.info(f"/markets/ticker — returning {len(picked)} markets (min=3, max=5)")
#     return {"markets": picked, "fetched_at": now.isoformat()}


# # ── /markets/daily ────────────────────────────────────────────────────────────
# @app.get("/markets/daily")
# async def get_daily_question():
#     today           = datetime.now(timezone.utc)
#     target_category = DAY_CATEGORY[today.weekday()]
#     logger.info(
#         f"/markets/daily — target_category={target_category} "
#         f"(weekday={today.weekday()})"
#     )

#     def pick_best(pool: list[dict]) -> Optional[dict]:
#         filtered = [
#             m for m in pool
#             if m["status"] == "active"
#             and m["category"] == target_category
#         ]
#         if not filtered:
#             return None

#         candidates = (
#             apply_filters(filtered, max_hours=24, min_volume=500, min_prob=20, max_prob=80)
#             or apply_filters(filtered, max_hours=24, min_volume=100, min_prob=20, max_prob=80)
#             # or apply_filters(filtered, max_hours=48, min_volume=100, min_prob=10, max_prob=90)
#             # or filtered
#         )

#         short = [m for m in candidates if len(m["title"]) <= 80]
#         final = short if short else candidates

#         return rank(final)[0] if final else None

#     pool   = await fetch_by_category(target_category, limit=500)
#     chosen = pick_best(pool)
#     if chosen:
#         logger.info(f"Chose market from series fetch: {chosen['ticker']}")

#     if not chosen:
#         logger.warning(
#             f"Series fetch found nothing for {target_category} — "
#             "trying global fetch"
#         )
#         all_markets = await fetch_global(limit=200)
#         chosen      = pick_best(all_markets)
#         if chosen:
#             logger.info(f"Chose market from global fetch: {chosen['ticker']}")

#     if not chosen:
#         raise HTTPException(
#             status_code=404,
#             detail=f"No {target_category} market found for today",
#         )

#     return {
#         "market":          chosen,
#         "target_category": target_category,
#         "date":            today.date().isoformat(),
#     }


# # ── /markets/{ticker} ─────────────────────────────────────────────────────────
# @app.get("/markets/{ticker}")
# async def get_market_result(ticker: str):
#     async with httpx.AsyncClient(timeout=10) as client:
#         try:
#             resp = await client.get(f"{KALSHI_BASE_URL}/markets/{ticker}")
#             resp.raise_for_status()
#         except httpx.HTTPError as e:
#             raise HTTPException(status_code=502, detail=f"Kalshi API error: {str(e)}")

#     market = resp.json().get("market", {})
#     parsed = parse_market(market)
#     if not parsed:
#         raise HTTPException(status_code=422, detail="Could not parse market data")

#     parsed["result"] = market.get("result")
#     return {"market": parsed}





# import re
# from fastapi import FastAPI, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# import httpx
# from datetime import datetime, timezone
# from typing import Optional
# import logging
# from collections import defaultdict


# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# app = FastAPI(title="Kalshi Probability Proxy", version="2.0.0")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# KALSHI_BASE_URL = "https://api.elections.kalshi.com/trade-api/v2"

# # ─── Category → series tickers ───────────────────────────────────────────────
# SERIES_TICKERS: dict[str, list[str]] = {
#     "finance": [
#         "KXBTC", "KXETH", "KXCRYPTO", "KXSP500", "KXNASDAQ",
#         "KXDOW", "KXFED", "KXCPI", "KXGDP", "KXOIL", "KXGOLD",
#         "KXRATES", "KXJOBS", "KXECON", "KXSTOCKS",
#     ],
#     "sports": [
#         "KXNBA", "KXNFL", "KXMLB", "KXNHL", "KXNCAAB", "KXNCAAF",
#         "KXSOCCER", "KXTENNIS", "KXGOLF", "KXMMA", "KXBOXING",
#         "KXNASCAR", "KXFORMULA", "KXOLYMPICS", "KXSPORTS",
#     ],
#     "weather": [
#         "KXRAIN", "KXSNOW", "KXTEMP", "KXHURRICANE", "KXSTORM",
#         "KXWIND", "KXFLOOD", "KXWILD", "KXWX",
#     ],
# }

# # ─── Category keywords (title-based fallback classifier) ─────────────────────
# CATEGORY_KEYWORDS: dict[str, list[str]] = {
#     "finance": [
#         "s&p", "btc", "bitcoin", "nasdaq", "dow", "fed", "rate", "inflation",
#         "ethereum", "eth", "crypto", "stock", "market", "gdp", "cpi",
#         "interest", "bond", "oil", "gold", "dollar", "economy", "recession",
#         "earnings", "ipo", "index", "trade", "tariff", "jobs", "unemployment",
#     ],
#     "sports": [
#         "nba", "nfl", "mlb", "nhl", "ncaa", "win", "game", "championship",
#         "playoff", "match", "tournament", "league", "cup", "super bowl",
#         "world series", "finals", "score", "team", "player", "season",
#         "mls", "ufc", "mma", "boxing", "golf", "tennis", "formula", "nascar",
#         "olympic", "soccer", "football", "basketball", "baseball", "hockey",
#     ],
#     "weather": [
#         "rain", "snow", "temperature", "weather", "storm", "hurricane",
#         "tornado", "flood", "wind", "celsius", "fahrenheit", "forecast",
#         "precipitation", "drought", "wildfire", "hail", "blizzard",
#     ],
# }


# SERIES_LABELS: dict[str, str] = {
#     "KXBTC": "BTC", "KXETH": "ETH", "KXSP500": "S&P 500", "KXNASDAQ": "Nasdaq",
#     "KXDOW": "Dow", "KXFED": "Fed Rate", "KXCPI": "CPI", "KXGDP": "GDP",
#     "KXOIL": "Oil", "KXGOLD": "Gold",
#     "KXNBA": "NBA", "KXNFL": "NFL", "KXMLB": "MLB", "KXNHL": "NHL",
#     "KXSOCCER": "Soccer", "KXTENNIS": "Tennis", "KXGOLF": "Golf", "KXMMA": "MMA",
#     "KXRAIN": "Rain", "KXSNOW": "Snow", "KXTEMP": "Temp",
#     "KXHURRICANE": "Hurricane", "KXSTORM": "Storm", "KXWIND": "Wind", "KXFLOOD": "Flood",
# }

# # Derived: series prefix → category (built once at startup)
# SERIES_PREFIX_MAP: dict[str, str] = {
#     prefix.upper(): cat
#     for cat, prefixes in SERIES_TICKERS.items()
#     for prefix in prefixes
# }

# # Day-of-week → category rotation
# DAY_CATEGORY: dict[int, str] = {
#     0: "finance",   # Mon
#     1: "sports",    # Tue
#     2: "weather",   # Wed
#     3: "finance",   # Thu
#     4: "sports",    # Fri
#     5: "sports",    # Sat
#     6: "weather",   # Sun
# }


# # ─── Helpers ──────────────────────────────────────────────────────────────────

# def classify_market(title: str, series_ticker: str = "") -> str:
#     """
#     1. Series prefix match (most reliable)
#     2. Title keyword match
#     3. Default → finance
#     """
#     st = (series_ticker or "").upper()
#     for prefix, category in SERIES_PREFIX_MAP.items():
#         if st.startswith(prefix):
#             return category

#     title_lower = title.lower()
#     for category, keywords in CATEGORY_KEYWORDS.items():
#         if any(kw in title_lower for kw in keywords):
#             return category

#     logger.debug(
#         f"classify_market: no match for title='{title}' "
#         f"series='{series_ticker}', defaulting to finance"
#     )
#     return "finance"


# def format_k(value: int) -> str:
#     return f"{round(value / 1000)}K"


# # Series prefix → human-readable short label
# SERIES_SHORT: dict[str, str] = {
#     "KXBTC":        "BTC",
#     "KXETH":        "ETH",
#     "KXCRYPTO":     "Crypto",
#     "KXSP500":      "S&P 500",
#     "KXNASDAQ":     "Nasdaq",
#     "KXDOW":        "Dow",
#     "KXFED":        "Fed Rate",
#     "KXCPI":        "CPI",
#     "KXGDP":        "GDP",
#     "KXOIL":        "Oil",
#     "KXGOLD":       "Gold",
#     "KXRATES":      "Rates",
#     "KXJOBS":       "Jobs",
#     "KXNBA":        "NBA",
#     "KXNFL":        "NFL",
#     "KXMLB":        "MLB",
#     "KXNHL":        "NHL",
#     "KXNCAAB":      "NCAA BB",
#     "KXNCAAF":      "NCAA FB",
#     "KXSOCCER":     "Soccer",
#     "KXMMA":        "MMA",
#     "KXBOXING":     "Boxing",
#     "KXGOLF":       "Golf",
#     "KXTENNIS":     "Tennis",
#     "KXNASCAR":     "NASCAR",
#     "KXFORMULA":    "F1",
#     "KXOLYMPICS":   "Olympics",
#     "KXSPORTS":     "Sports",
#     "KXMVESPORTS":  "eSports",
#     "KXRAIN":       "Rain",
#     "KXSNOW":       "Snow",
#     "KXTEMP":       "Temp",
#     "KXHURRICANE":  "Hurricane",
#     "KXSTORM":      "Storm",
#     "KXWIND":       "Wind",
#     "KXFLOOD":      "Flood",
#     "KXWX":         "Weather",
# }

# _THRESHOLD_PATTERNS = [
#     # Dollar amounts: > $70,000 / above $1.2M / over 70000
#     (
#         re.compile(r'(?:above|over|>)\s*\$([\d,]+(?:\.\d+)?)\s*([KkMm]?)', re.I),
#         lambda m: _fmt_dollar(m.group(1), m.group(2))
#     ),
#     # Percentages
#     (
#         re.compile(r'(?:below|under|<|above|over|>)?\s*([\d.]+)\s*%', re.I),
#         lambda m: f"> {m.group(1)}%"
#     ),
#     # Direction words
#     (re.compile(r'\b(higher|up|gain|rise|bull)\b', re.I), lambda _: "Up"),
#     (re.compile(r'\b(lower|down|drop|fall|bear)\b', re.I), lambda _: "Down"),
#     (re.compile(r'\bwin\b', re.I), lambda _: "Win"),
#     (re.compile(r'\b(loss|lose)\b', re.I), lambda _: "Loss"),
# ]


# def _fmt_dollar(digits: str, suffix: str) -> str:
#     """Turn '70000' / '70' / '1.2' + 'K'/'M' into '$70K' / '$1.2M'."""
#     val = float(digits.replace(",", ""))
#     s   = suffix.upper()
#     if s == "M" or val >= 1_000_000:
#         return f">${val / 1_000_000:.1f}M".rstrip("0").rstrip(".")
#     if s == "K" or val >= 1_000:
#         return f">${round(val / 1_000)}K"
#     return f">${int(val)}"


# def _extract_threshold(text: str) -> str:
#     """Return a short threshold string from free text, or empty string."""
#     for pattern, formatter in _THRESHOLD_PATTERNS:
#         m = pattern.search(text)
#         if m:
#             return formatter(m)
#     return ""


# def create_card_title(title: str, ticker: str, subtitle: str) -> str:
#     """Build a short card title from ticker + subtitle + title."""
#     t    = (ticker or "").upper()
#     sub  = (subtitle or "").strip()
#     titl = (title or "").strip()

#     # ── Step 1: series label ─────────────────────────────────
#     label = None
#     for prefix in sorted(SERIES_SHORT, key=len, reverse=True):
#         if t.startswith(prefix):
#             label = SERIES_SHORT[prefix]
#             break

#     # ── Step 2: ticker-based thresholds ─────────────────────
#     threshold = ""

#     bucket_match = re.search(r'B(\d+)', t)
#     if bucket_match and label in {"BTC", "ETH"}:
#         value     = int(bucket_match.group(1))
#         threshold = f"> ${round(value / 1000)}K"
#     elif label == "CPI":
#         cpi_match = re.search(r'T(\d+(?:\.\d+)?)', t)
#         if cpi_match:
#             threshold = f"> {cpi_match.group(1)}%"

#     if not threshold:
#         threshold = _extract_threshold(sub or titl)

#     # ── Step 3: compose ──────────────────────────────────────
#     if label and threshold:
#         result = f"{label} {threshold}"
#     elif label:
#         result = label
#     else:
#         result = titl[:15]

#     return result[:20]


# def to_pct(value) -> float:
#     """Convert a Kalshi _dollars field (e.g. "0.5600") to a percentage (56.0)."""
#     try:
#         return float(value or 0) * 100
#     except (TypeError, ValueError):
#         return 0.0

# def get_label(series_ticker: str) -> str:
#     for prefix in sorted(SERIES_LABELS, key=len, reverse=True):
#         if series_ticker.upper().startswith(prefix):
#             return SERIES_LABELS[prefix]
#     return series_ticker.replace("KX", "")

# def make_card_title(series_ticker: str, category: str, yes_sub_title: str, title: str) -> str:
#     label = get_label(series_ticker)
#     sub   = yes_sub_title or ""
#     tl    = title.lower()
#     sl    = sub.lower()

#     if category == "sports" and sub:
#         team = sub.split()[-1]
#         if "win" in tl:   return f"{team} win"
#         if "loss" in tl:  return f"{team} loss"
#         return f"{label}: {team}"

#     if category == "weather" and "nyc" in tl:
#         return f"NYC {label}"

#     if "above" in sl:
#         return f"{label} > {sub.replace('above','').strip()}"
#     if "below" in sl:
#         return f"{label} < {sub.replace('or below','').replace('below','').strip()}"
#     if "to" in sub:
#         raw = sub.split("to")[0].replace("$", "").replace(",", "").strip()
#         try:
#             n = float(raw)
#             short = f"{n/1_000_000:.1f}M" if n >= 1_000_000 else f"{n/1_000:.1f}K" if n >= 1_000 else str(int(n))
#             return f"{label} >{short}"
#         except ValueError:
#             pass

#     return label

# # def parse_market(m: dict) -> Optional[dict]:
# #     try:
# #         yes_bid    = to_pct(m.get("yes_bid_dollars"))
# #         yes_ask    = to_pct(m.get("yes_ask_dollars"))
# #         no_bid     = to_pct(m.get("no_bid_dollars"))
# #         last_price = to_pct(m.get("last_price_dollars"))

# #         if yes_bid and yes_ask:
# #             prob = round((yes_bid + yes_ask) / 2)
# #         elif yes_bid and no_bid:
# #             prob = round((yes_bid + (100 - no_bid)) / 2)
# #         elif yes_bid:   prob = round(yes_bid)
# #         elif yes_ask:   prob = round(yes_ask)
# #         elif last_price: prob = round(last_price)
# #         else:            prob = 50
# #         prob = max(1, min(99, prob))

# #         close_time_str = m.get("close_time") or m.get("expiration_time")
# #         if not close_time_str:
# #             return None
# #         close_time        = datetime.fromisoformat(close_time_str.replace("Z", "+00:00"))
# #         hours_until_close = (close_time - datetime.now(timezone.utc)).total_seconds() / 3600

# #         series_ticker = m.get("series_ticker", "")
# #         title         = m.get("title", "")
# #         subtitle      = m.get("yes_sub_title", "")
# #         category      = get_category(series_ticker)

# #         return {
# #             "ticker":            m.get("ticker", "unknown"),
# #             "series_ticker":     series_ticker,
# #             "title":             title,
# #             "yes_sub_title":     subtitle,
# #             "card_title":        make_card_title(series_ticker, category, subtitle, title),
# #             "probability":       prob,
# #             "volume":            float(m.get("volume_fp", 0) or 0),
# #             "close_time":        close_time_str,
# #             "hours_until_close": round(hours_until_close, 1),
# #             "status":            m.get("status", ""),
# #             "category":          category,
# #         }
# #     except Exception as e:
# #         logger.warning(f"Failed to parse market {m.get('ticker')}: {e}")
# #         return None


# def parse_market(m: dict) -> Optional[dict]:
#     """
#     Parse a raw Kalshi market dict into our standard schema.

#     Probability priority:
#       1. Bid/ask midpoint
#       2. yes_bid + implied ask (100 - no_bid)
#       3. yes_bid alone
#       4. yes_ask alone
#       5. last_price_dollars
#       6. Default 50
#     """
#     try:
#         ticker = m.get("ticker", "unknown")

#         yes_bid    = to_pct(m.get("yes_bid_dollars"))
#         yes_ask    = to_pct(m.get("yes_ask_dollars"))
#         no_bid     = to_pct(m.get("no_bid_dollars"))
#         last_price = to_pct(m.get("last_price_dollars"))
#         volume     = float(m.get("volume_fp", 0) or 0)

#         # ── Probability cascade ───────────────────────────────────────────────
#         if yes_bid and yes_ask:
#             probability = round((yes_bid + yes_ask) / 2)
#         elif yes_bid and no_bid:
#             implied_yes_ask = 100 - no_bid
#             probability = round((yes_bid + implied_yes_ask) / 2)
#         elif yes_bid:
#             probability = round(yes_bid)
#         elif yes_ask:
#             probability = round(yes_ask)
#         elif last_price:
#             probability = round(last_price)
#         else:
#             probability = 50

#         probability = max(1, min(99, probability))

#         close_time_str = m.get("close_time") or m.get("expiration_time")
#         if not close_time_str:
#             return None

#         close_time        = datetime.fromisoformat(close_time_str.replace("Z", "+00:00"))
#         hours_until_close = (close_time - datetime.now(timezone.utc)).total_seconds() / 3600

#         series_ticker = m.get("series_ticker", "") or ""
#         title         = m.get("title", "")
#         subtitle      = m.get("yes_sub_title", "")

#         return {
#             "ticker":            ticker,
#             "series_ticker":     series_ticker,
#             "title":             title,
#             "yes_sub_title":     subtitle,
#             "subtitle":          m.get("subtitle", ""),
#             "card_title":        make_card_title(series_ticker,  classify_market(title, series_ticker), subtitle, title),
#             # "card_title":        create_card_title(title, ticker, subtitle),
#             "probability":       probability,
#             "yes_bid":           round(yes_bid, 2),
#             "yes_ask":           round(yes_ask, 2),
#             "last_price":        round(last_price, 2),
#             "volume":            volume,
#             "close_time":        close_time_str,
#             "hours_until_close": round(hours_until_close, 1),
#             "status":            m.get("status", ""),
#             "category":          classify_market(title, series_ticker),
#         }
#     except Exception as e:
#         logger.warning(f"Failed to parse market {m.get('ticker')}: {e}")
#         return None


# def apply_filters(
#     pool: list[dict],
#     max_hours: float,
#     min_volume: float,
#     min_prob: int,
#     max_prob: int,
# ) -> list[dict]:
#     return [
#         m for m in pool
#         if m["status"] == "active"
#         and m["hours_until_close"] <= max_hours
#         and min_prob <= m["probability"] <= max_prob
#         and m["volume"] >= min_volume
#     ]


# def rank(pool: list[dict]) -> list[dict]:
#     """Sort by: highest volume → soonest close → shortest title."""
#     return sorted(
#         pool,
#         key=lambda x: (-x["volume"], x["hours_until_close"], len(x["title"])),
#     )


# # ─── Data fetchers ────────────────────────────────────────────────────────────

# async def fetch_by_category(category: str, limit: int = 50) -> list[dict]:
#     """Fetch markets for every series ticker in a category."""
#     series_list = SERIES_TICKERS.get(category, [])
#     results: list[dict] = []
#     async with httpx.AsyncClient(timeout=10) as client:
#         for series in series_list:
#             try:
#                 resp = await client.get(
#                     f"{KALSHI_BASE_URL}/markets",
#                     params={"status": "open", "series_ticker": series, "limit": limit},
#                 )
#                 if resp.status_code == 200:
#                     for m in resp.json().get("markets", []):
#                         parsed = parse_market(m)
#                         if parsed:
#                             results.append(parsed)
#             except httpx.HTTPError:
#                 continue
#     logger.info(f"fetch_by_category({category}) → {len(results)} markets")
#     return results


# async def fetch_global(limit: int = 200) -> list[dict]:
#     """Fetch open markets globally (last-resort fallback)."""
#     async with httpx.AsyncClient(timeout=10) as client:
#         try:
#             resp = await client.get(
#                 f"{KALSHI_BASE_URL}/markets",
#                 params={"status": "open", "limit": limit},
#             )
#             resp.raise_for_status()
#             return [
#                 p
#                 for p in (parse_market(m) for m in resp.json().get("markets", []))
#                 if p
#             ]
#         except httpx.HTTPError as e:
#             raise HTTPException(status_code=502, detail=f"Kalshi API error: {str(e)}")


# def top_for_category(pool: list[dict], n: int = 10) -> list[dict]:
#     """
#     Apply cascading filters within one category pool, return top-n.
#     n=10 gives enough depth to skip title/ticker dupes and still fill all slots.
#     """
#     candidates = (
#         apply_filters(pool, max_hours=48,  min_volume=100, min_prob=10, max_prob=90)
#         # or apply_filters(pool, max_hours=168, min_volume=10,  min_prob=5,  max_prob=95)
#         # or apply_filters(pool, max_hours=720, min_volume=0,   min_prob=1,  max_prob=99)
#         #  or [m for m in pool if m["status"] == "active"]
#     )
#     return rank(candidates)[:n]


# def normalize_title(title: str) -> str:
#     return title.lower().strip()


# # ─── Routes ───────────────────────────────────────────────────────────────────

# @app.get("/health")
# def health():
#     return {"status": "ok", "time": datetime.now(timezone.utc).isoformat()}


# # ── /debug/markets ────────────────────────────────────────────────────────────
# @app.get("/debug/markets")
# async def debug_markets():
#     """
#     Debug endpoint — raw filter diagnostics from Kalshi.
#     Uses _dollars fields (current v2 API).
#     """
#     async with httpx.AsyncClient(timeout=10) as client:
#         try:
#             resp = await client.get(
#                 f"{KALSHI_BASE_URL}/markets",
#                 params={"status": "open", "limit": 20},
#             )
#             resp.raise_for_status()
#         except httpx.HTTPError as e:
#             raise HTTPException(status_code=502, detail=f"Kalshi API error: {str(e)}")

#     now     = datetime.now(timezone.utc)
#     markets = resp.json().get("markets", [])
#     sample  = []

#     for m in markets[:20]:
#         yes_bid    = to_pct(m.get("yes_bid_dollars"))
#         yes_ask    = to_pct(m.get("yes_ask_dollars"))
#         no_bid     = to_pct(m.get("no_bid_dollars"))
#         last_price = to_pct(m.get("last_price_dollars"))

#         if yes_bid and yes_ask:
#             probability = round((yes_bid + yes_ask) / 2)
#         elif yes_bid and no_bid:
#             probability = round((yes_bid + (100 - no_bid)) / 2)
#         elif yes_bid:
#             probability = round(yes_bid)
#         elif yes_ask:
#             probability = round(yes_ask)
#         elif last_price:
#             probability = round(last_price)
#         else:
#             probability = 0

#         close_time_str = m.get("close_time") or m.get("expiration_time")
#         hours_left     = None
#         if close_time_str:
#             try:
#                 ct         = datetime.fromisoformat(close_time_str.replace("Z", "+00:00"))
#                 hours_left = round((ct - now).total_seconds() / 3600, 1)
#             except Exception:
#                 pass

#         volume = float(m.get("volume_fp") or m.get("volume") or 0)

#         sample.append({
#             "ticker":        m.get("ticker"),
#             "title":         m.get("title"),
#             "status":        m.get("status"),
#             "probability":   probability,
#             "yes_bid":       round(yes_bid, 2),
#             "yes_ask":       round(yes_ask, 2),
#             "last_price":    round(last_price, 2),
#             "volume":        volume,
#             "hours_left":    hours_left,
#             "passes_status": m.get("status") == "active",
#             "passes_hours":  hours_left is not None and hours_left <= 48,
#             "passes_prob":   10 <= probability <= 90,
#             "passes_volume": volume >= 100,
#             "all_pass": (
#                 m.get("status") == "active"
#                 and hours_left is not None and hours_left <= 48
#                 and 10 <= probability <= 90
#                 and volume >= 100
#             ),
#         })

#     passing = [s for s in sample if s["all_pass"]]
#     return {
#         "total_returned":  len(markets),
#         "sample_size":     len(sample),
#         "passing_filters": len(passing),
#         "sample":          sample,
#     }


# # ── /markets/ticker ───────────────────────────────────────────────────────────
# @app.get("/markets/ticker")
# async def get_ticker_markets():
#     """
#     Returns 3–5 live markets for the probability ticker.

#     Guarantees:
#       - Minimum 3 markets always returned.
#       - Maximum 5 markets.
#       - No duplicate tickers or titles.
#       - At most 2 markets per category.
#       - At least 1 market per category when data is available.
#       - If a category fails, compensates from other categories → MIN 3 always held.

#     Steps:
#       1. Fetch each category independently via series tickers.
#       2. Global fallback for any completely empty category pool.
#       3. Pre-compute top-10 candidates per category (filters applied once).
#       4. Guarantee 1 per category (best effort, skipping dupes).
#       5. Compensate missing slots from other categories → MIN 3.
#       6. Fill remaining slots up to 5 → MAX 5 (capped at 2 per category).
#     """
#     now = datetime.now(timezone.utc)

#     # ── Step 1: Fetch per category ────────────────────────────────────────────
#     category_pool: dict[str, list[dict]] = {}
#     for cat in SERIES_TICKERS:
#         category_pool[cat] = await fetch_by_category(cat, limit=1000)

#     # ── Step 2: Global fallback for empty categories ──────────────────────────
#     empty_cats = [cat for cat, pool in category_pool.items() if not pool]
#     if empty_cats:
#         logger.warning(f"Empty pools for {empty_cats} — trying global fetch")
#         global_markets = await fetch_global(limit=200)
#         for m in global_markets:
#             if m["category"] in empty_cats:
#                 category_pool[m["category"]].append(m)

#     # ── Step 3: Pre-compute top-10 per category ───────────────────────────────
#     category_tops: dict[str, list[dict]] = {
#         cat: top_for_category(category_pool[cat], n=10)
#         for cat in SERIES_TICKERS
#     }

#     # ── Dedup + per-category cap state ───────────────────────────────────────
#     picked: list[dict]           = []
#     seen_tickers: set[str]       = set()
#     seen_titles: set[str]        = set()
#     category_counts: dict[str, int] = {cat: 0 for cat in SERIES_TICKERS}
#     MAX_PER_CATEGORY              = 2

#     def try_add(market: dict) -> bool:
#         """Add market only if:
#           - ticker is unseen
#           - normalized title is unseen
#           - category hasn't hit MAX_PER_CATEGORY (2)
#         """
#         ticker     = market["ticker"]
#         norm_title = normalize_title(market["title"])
#         cat        = market["category"]
#         if ticker in seen_tickers or norm_title in seen_titles:
#             return False
#         if category_counts.get(cat, 0) >= MAX_PER_CATEGORY:
#             return False
#         picked.append(market)
#         seen_tickers.add(ticker)
#         seen_titles.add(norm_title)
#         category_counts[cat] = category_counts.get(cat, 0) + 1
#         return True

#     # ── Step 4: Guarantee 1 per category ─────────────────────────────────────
#     failed_cats: list[str] = []
#     for cat in SERIES_TICKERS:
#         added = False
#         for candidate in category_tops[cat]:
#             if try_add(candidate):
#                 logger.info(
#                     f"[{cat}] Guaranteed pick: "
#                     f"{candidate['ticker']} | '{candidate['title']}'"
#                 )
#                 added = True
#                 break
#         if not added:
#             logger.warning(f"[{cat}] No unique market — will compensate")
#             failed_cats.append(cat)

#     # ── Step 5: Compensate for failed categories → MIN 3 ─────────────────────
#     if failed_cats:
#         needed = len(failed_cats)
#         logger.warning(f"Compensating {needed} missing slot(s) from runner-ups")

#         compensation_pool = rank([
#             m
#             for cat in SERIES_TICKERS
#             if cat not in failed_cats
#             for m in category_tops[cat]
#         ])
#         for candidate in compensation_pool:
#             if needed <= 0:
#                 break
#             if try_add(candidate):
#                 logger.info(
#                     f"Compensation fill: "
#                     f"{candidate['ticker']} | '{candidate['title']}'"
#                 )
#                 needed -= 1

#         if len(picked) < 3:
#             logger.error(
#                 f"Could only pick {len(picked)} markets — "
#                 "Kalshi data may be too thin"
#             )

#     # ── Step 6: Fill up to MAX 5 with per-category runner-ups ────────────────
#     for cat in SERIES_TICKERS:
#         if len(picked) >= 5:
#             break
#         for candidate in category_tops[cat]:
#             if len(picked) >= 5:
#                 break
#             if try_add(candidate):
#                 logger.info(
#                     f"[{cat}] Runner-up fill: "
#                     f"{candidate['ticker']} | '{candidate['title']}'"
#                 )

#     picked = rank(picked)
#     logger.info(f"/markets/ticker — returning {len(picked)} markets (min=3, max=5)")
#     return {"markets": picked, "fetched_at": now.isoformat()}


# # ── /markets/daily ────────────────────────────────────────────────────────────
# @app.get("/markets/daily")
# async def get_daily_question():
#     """
#     Returns the single daily question market based on day-of-week rotation.

#     Category rotation:
#       Mon/Thu → finance | Tue/Fri/Sat → sports | Wed/Sun → weather

#     Filter cascade (always stays within the target category):
#       1. Strict:      close<=24h, vol>=500, prob 20-80%
#       2. Fallback 1:  close<=24h, vol>=100, prob 20-80%
#       3. Fallback 2:  close<=48h, vol>=100, prob 10-90%
#       4. Last resort: any active market in target category
#     """
#     today           = datetime.now(timezone.utc)
#     target_category = DAY_CATEGORY[today.weekday()]
#     logger.info(
#         f"/markets/daily — target_category={target_category} "
#         f"(weekday={today.weekday()})"
#     )

#     def pick_best(pool: list[dict]) -> Optional[dict]:
#         filtered = [
#             m for m in pool
#             if m["status"] == "active"
#             and m["category"] == target_category
#         ]
#         if not filtered:
#             return None

#         candidates = (
#             apply_filters(filtered, max_hours=24, min_volume=500, min_prob=20, max_prob=80)
#             or apply_filters(filtered, max_hours=24, min_volume=100, min_prob=20, max_prob=80)
#             # or apply_filters(filtered, max_hours=48, min_volume=100, min_prob=10, max_prob=90)
#             # or filtered
#         )

#         short = [m for m in candidates if len(m["title"]) <= 80]
#         final = short if short else candidates

#         return rank(final)[0] if final else None

#     # Step 1: fetch via series tickers
#     pool   = await fetch_by_category(target_category, limit=500)
#     chosen = pick_best(pool)
#     if chosen:
#         logger.info(f"Chose market from series fetch: {chosen['ticker']}")

#     # Step 2: global fetch, still target category only
#     if not chosen:
#         logger.warning(
#             f"Series fetch found nothing for {target_category} — "
#             "trying global fetch"
#         )
#         all_markets = await fetch_global(limit=200)
#         chosen      = pick_best(all_markets)
#         if chosen:
#             logger.info(f"Chose market from global fetch: {chosen['ticker']}")

#     if not chosen:
#         raise HTTPException(
#             status_code=404,
#             detail=f"No {target_category} market found for today",
#         )

#     return {
#         "market":          chosen,
#         "target_category": target_category,
#         "date":            today.date().isoformat(),
#     }


# # ── /markets/{ticker} ─────────────────────────────────────────────────────────
# @app.get("/markets/{ticker}")
# async def get_market_result(ticker: str):
#     """
#     Fetch a specific market by ticker.
#     Used by the iOS app the next day to check the result.

#     result field:
#       null  → still open / not yet resolved
#       "yes" → resolved YES
#       "no"  → resolved NO
#     """
#     async with httpx.AsyncClient(timeout=10) as client:
#         try:
#             resp = await client.get(f"{KALSHI_BASE_URL}/markets/{ticker}")
#             resp.raise_for_status()
#         except httpx.HTTPError as e:
#             raise HTTPException(status_code=502, detail=f"Kalshi API error: {str(e)}")

#     market = resp.json().get("market", {})
#     parsed = parse_market(market)
#     if not parsed:
#         raise HTTPException(status_code=422, detail="Could not parse market data")

#     parsed["result"] = market.get("result")   # null | "yes" | "no"
#     return {"market": parsed}





from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
from datetime import datetime, timezone
import logging
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Kalshi Probability Proxy", version="3.4.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

KALSHI_BASE_URL = "https://api.elections.kalshi.com/trade-api/v2"

SERIES_TICKERS: dict[str, list[str]] = {
    "finance": [
        "KXBTC",
        "KXETH",
        "KXCRYPTO",
        "KXSP500",
        "KXNASDAQ",
        "KXDOW",
        "KXFED",
        "KXCPI",
        "KXGDP",
        "KXOIL",
        "KXGOLD",
        "KXRATES",
        "KXJOBS",
        "KXECON",
        "KXSTOCKS"
    ],
   
    "sports": [
        "KXNBA",
        "KXNFL",
        "KXMLB",
        "KXNHL",
        "KXNCAAB",
        "KXNCAAF",
        "KXSOCCER",
        "KXTENNIS",
        "KXGOLF",
        "KXMMA",
        "KXBOXING",
        "KXNASCAR",
        "KXFORMULA",
        "KXOLYMPICS",
        "KXSPORTS"
    ],
    
    "weather": [
        "KXRAIN",
        "KXSNOW",
        "KXTEMP",
        "KXHURRICANE",
        "KXSTORM",
        "KXWIND",
        "KXFLOOD",
        "KXWILD",
        "KXWX",
        "KXHIGHNY"
    ]
}

# Map each series prefix → category (longest-first for safe matching)
SERIES_PREFIX_MAP: dict[str, str] = {
    prefix: cat
    for cat, prefixes in SERIES_TICKERS.items()
    for prefix in prefixes
}

SERIES_LABELS: dict[str, str] = {
    "KXBTC": "BTC", "KXETH": "ETH", "KXSP500": "S&P 500", "KXNASDAQ": "Nasdaq",
    "KXDOW": "Dow", "KXFED": "Fed Rate", "KXCPI": "CPI", "KXGDP": "GDP",
    "KXOIL": "Oil", "KXGOLD": "Gold",
    "KXNBA": "NBA", "KXNFL": "NFL", "KXMLB": "MLB", "KXNHL": "NHL",
    "KXSOCCER": "Soccer", "KXTENNIS": "Tennis", "KXGOLF": "Golf", "KXMMA": "MMA",
    "KXRAIN": "Rain", "KXSNOW": "Snow", "KXTEMP": "Temp", "KXHIGHNY": "High Temp",
    "KXHURRICANE": "Hurricane", "KXSTORM": "Storm", "KXWIND": "Wind", "KXFLOOD": "Flood",
}

DAY_CATEGORY: dict[int, str] = {
    0: "finance", 1: "sports",  2: "weather",
    3: "finance", 4: "sports",  5: "sports",  6: "weather",
}

# ─── Helpers ────────────────────────────────────────────────────────────────

def get_category(series_ticker: str) -> str:
    for prefix in sorted(SERIES_PREFIX_MAP, key=len, reverse=True):
        if series_ticker.upper().startswith(prefix):
            return SERIES_PREFIX_MAP[prefix]
    return "finance"

def get_label(series_ticker: str) -> str:
    for prefix in sorted(SERIES_LABELS, key=len, reverse=True):
        if series_ticker.upper().startswith(prefix):
            return SERIES_LABELS[prefix]
    return series_ticker.replace("KX", "")

def to_pct(value) -> float:
    try:
        return float(value or 0) * 100
    except (TypeError, ValueError):
        return 0.0

def make_card_title(series_ticker: str, category: str, yes_sub_title: str, title: str) -> str:
    label = get_label(series_ticker)
    logger.info(f'----------------------------{label}')
    sub   = yes_sub_title or ""
    tl    = title.lower()
    sl    = sub.lower()

    if category == "sports" and sub:
        team = sub.split()[-1]
        if "win" in tl:   return f"{team} win"
        if "loss" in tl:  return f"{team} loss"
        return f"{label}: {team}"

    if category == "weather" and "nyc" in tl:
        return f"NYC {label}"

    if "above" in sl:
        return f"{label} > {sub.replace('above','').strip()}"
    if "below" in sl:
        return f"{label} < {sub.replace('or below','').replace('below','').strip()}"
    if "to" in sub:
        raw = sub.split("to")[0].replace("$", "").replace(",", "").strip()
        try:
            n = float(raw)
            short = f"{n/1_000_000:.1f}M" if n >= 1_000_000 else f"{n/1_000:.1f}K" if n >= 1_000 else str(int(n))
            return f"{label} >{short}"
        except ValueError:
            pass

    return label

def parse_market(m: dict,series:str) -> Optional[dict]:
    try:
        yes_bid    = to_pct(m.get("yes_bid_dollars"))
        yes_ask    = to_pct(m.get("yes_ask_dollars"))
        no_bid     = to_pct(m.get("no_bid_dollars"))
        last_price = to_pct(m.get("last_price_dollars"))

        if yes_bid and yes_ask:
            prob = round((yes_bid + yes_ask) / 2)
        elif yes_bid and no_bid:
            prob = round((yes_bid + (100 - no_bid)) / 2)
        elif yes_bid:   prob = round(yes_bid)
        elif yes_ask:   prob = round(yes_ask)
        elif last_price: prob = round(last_price)
        else:            prob = 50
        prob = max(1, min(99, prob))

        close_time_str = m.get("close_time") or m.get("expiration_time")
        if not close_time_str:
            return None
        close_time        = datetime.fromisoformat(close_time_str.replace("Z", "+00:00"))
        hours_until_close = (close_time - datetime.now(timezone.utc)).total_seconds() / 3600

        series_ticker = series
        title         = m.get("title", "")
        subtitle      = m.get("yes_sub_title", "")
        category      = get_category(series_ticker)

        return {
            "ticker":            m.get("ticker", "unknown"),
            "series_ticker":     series_ticker,
            "title":             title,
            "yes_sub_title":     subtitle,
            "card_title":        make_card_title(series_ticker, category, subtitle, title),
            "probability":       prob,
            "volume":            float(m.get("volume_fp", 0) or 0),
            "close_time":        close_time_str,
            "hours_until_close": round(hours_until_close, 1),
            "status":            m.get("status", ""),
            "category":          category,
        }
    except Exception as e:
        logger.warning(f"Failed to parse market {m.get('ticker')}: {e}")
        return None

def apply_filters(pool: list[dict], *, min_prob=10, max_prob=90, min_volume=100, max_hours=48) -> list[dict]:
    return [
        m for m in pool
        if m["status"] == "active"
        and m["hours_until_close"] <= max_hours
        and min_prob <= m["probability"] <= max_prob
        and m["volume"] >= min_volume
    ]

def rank(pool: list[dict]) -> list[dict]:
    return sorted(pool, key=lambda x: (-x["volume"], x["hours_until_close"]))

async def fetch_category(category: str, limit: int = 200) -> list[dict]:
    results: list[dict] = []
    async with httpx.AsyncClient(timeout=10) as client:
        for series in SERIES_TICKERS.get(category, []):
            try:
                resp = await client.get(
                    f"{KALSHI_BASE_URL}/markets",
                    params={"status": "open", "series_ticker": series, "limit": limit},
                )
                if resp.status_code == 200:
                    for m in resp.json().get("markets", []):
                        parsed = parse_market(m,series)
                        if parsed:
                            results.append(parsed)
            except httpx.HTTPError:
                continue
    return results

# ─── Routes ────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "time": datetime.now(timezone.utc).isoformat()}


@app.get("/markets/ticker")
async def get_ticker_markets():
    by_category: dict[str, list] = {}
    for cat in SERIES_TICKERS:
        pool     = await fetch_category(cat)
        filtered = apply_filters(pool, min_prob=10, max_prob=90, min_volume=100, max_hours=48)
        by_category[cat] = rank(filtered)[:3]

    merged = rank([m for ms in by_category.values() for m in ms])[:5]
    return {"markets": merged, "by_category": by_category, "fetched_at": datetime.now(timezone.utc).isoformat()}


@app.get("/markets/daily")
async def get_daily_market():
    today    = datetime.now(timezone.utc)
    category = DAY_CATEGORY[today.weekday()]
    logger.info(f"/markets/daily — category={category}")

    pool = await fetch_category(category)

    # Try strict filter first, then relax volume
    candidates =  apply_filters(pool, min_prob=20, max_prob=80, min_volume=500, max_hours=24)
    if not candidates:
        candidates = apply_filters(pool, min_prob=20, max_prob=80, min_volume=100, max_hours=24)

    best = rank(candidates)
    if not best:
        raise HTTPException(status_code=404, detail=f"No {category} market found for today")

    return {"market": best[0], "category": category, "date": today.date().isoformat()}


@app.get("/markets/{ticker}")
async def get_market(ticker: str):
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(f"{KALSHI_BASE_URL}/markets/{ticker}")
        resp.raise_for_status()
    market = resp.json().get("market", {})
    parsed = parse_market(market)
    if not parsed:
        raise HTTPException(status_code=422, detail="Could not parse market data")
    parsed["result"] = market.get("result")
    return {"market": parsed}