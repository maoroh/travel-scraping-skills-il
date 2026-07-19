---
name: isrotel-deals-finder
description: >-
  Fetch live hotel room packages and pricing directly from Isrotel's booking API
  using cURL, with no API key or account required. Use when the user asks about
  Isrotel availability, room prices, packages, deals or promotions, names an Isrotel
  property such as Royal Beach, Beresheet, Cramim, Orient or Lagoona, or says things
  like "find me a deal at Isrotel", "cheapest Isrotel option", "malon Isrotel",
  "chadarim pnuyim be-Eilat", "mivtzaim be-Isrotel", or "chufsha be-Eilat le-zug".
  Covers 25 properties across Eilat, the Dead Sea, Mitzpe Ramon, Jerusalem, Tel Aviv
  and the north, returning web prices, Sun Club member prices and savings versus rack
  rate. Prefer this over web search for anything Isrotel-related. Do NOT use for other
  Israeli chains such as Dan, Fattal or Leonardo, for flight fares, or for completing
  an actual booking (always send the user to isrotel.co.il to book).
license: MIT
allowed-tools: 'Bash(curl:*) Bash(python3:*) Bash(bash:*)'
compatibility: >-
  Requires network access to isrotel.co.il, plus curl and python3 in the shell.
  No API key or account needed. Works with Claude Code, Claude.ai, and Cursor.
metadata:
  version: "1.0.1"
  category: "travel"
  author: "Maor Ohana"
  display_name:
    he: "מאתר מבצעי ישרוטל"
    en: "Isrotel Deals Finder"
  display_description:
    he: "שליפת חבילות אירוח ומחירים בזמן אמת ישירות ממערכת ההזמנות של ישרוטל, ללא צורך במפתח API או בחשבון. השתמשו כשמבקשים זמינות חדרים, מחירים, חבילות או מבצעים בישרוטל, או כשמזכירים שם מלון כמו רויאל ביץ', בראשית, כרמים או לגונה. מכסה 25 מלונות באילת, ים המלח, מצפה רמון, ירושלים, תל אביב והצפון, ומציג מחיר אתר, מחיר מועדון חוג השמש וההנחה מול מחיר המחירון. לא מיועד לרשתות אחרות כמו דן, פתאל או לאונרדו, ולא לביצוע הזמנה בפועל."
    en: "Fetch live hotel room packages and pricing directly from Isrotel's booking API using cURL, with no API key or account required. Use when the user asks about Isrotel availability, room prices, packages, deals or promotions, or names an Isrotel property such as Royal Beach, Beresheet, Cramim, Orient or Lagoona. Covers 25 properties across Eilat, the Dead Sea, Mitzpe Ramon, Jerusalem, Tel Aviv and the north, returning web prices, Sun Club member prices and savings versus rack rate. Do NOT use for other Israeli chains such as Dan, Fattal or Leonardo, or for completing an actual booking."
  tags:
    he: ["מלונות", "ישרוטל", "נסיעות", "הזמנות", "תמחור", "אילת", "ישראל"]
    en: ["hotels", "isrotel", "travel", "booking", "pricing", "eilat", "israel"]
  supported_agents: ["claude-code", "cursor", "github-copilot", "windsurf", "opencode", "codex", "gemini-cli"]
---

# Isrotel Deals Finder

Fetches live room packages from Isrotel's internal Umbraco search API using
cURL, extracts the pricing data embedded in the HTML response, and presents a
sorted price comparison.

## Instructions

### Step 1: Resolve Inputs

Gather these from the user's message and ask only for what is genuinely missing.

| Field | Required | Default | Notes |
|-------|----------|---------|-------|
| `hotel_code` | yes, or `location` | none | Look up in `references/hotel-directory.md` |
| `location` | yes, or `hotel_code` | none | A city or region. Searches every hotel there |
| `check_in` | yes | none | Convert any natural date to `YYYY-MM-DD` |
| `check_out` | yes | none | Convert any natural date to `YYYY-MM-DD` |
| `adults` | no | `2` | Ages 13 and up |
| `children` | no | `0` | Ages 2 to 12 |
| `infants` | no | `0` | Under age 2 |

Supply either `hotel_code` or `location`, not both. When given a `location`,
pull every matching code from the region groupings in
`references/hotel-directory.md` and fetch them in parallel.

Watch for the ambiguous cases: "Royal Beach" is `RB` in Eilat but `RT` in Tel
Aviv, so ask which. If the user says "this weekend" with no dates, assume a
Friday check-in and Saturday check-out per Israeli convention and state that
assumption out loud.

### Step 2: Fetch a Single Hotel

```bash
bash scripts/fetch_packages.sh \
  --hotel-code RB \
  --check-in 2026-04-10 \
  --check-out 2026-04-12 \
  --adults 2 \
  --children 0 \
  --infants 0
```

The script prints the raw HTML to stdout. For the underlying URL
construction, required headers, and parameter semantics, consult
`references/api-reference.md`.

### Step 3: Fetch Several Hotels

For a whole city or region, use the batch script. It caps concurrency at 4 and
spaces batches out to stay polite to a live booking system.

```bash
bash scripts/fetch_all.sh \
  --codes "RB KS RG AG AM SP LG RC" \
  --check-in 2026-07-01 \
  --check-out 2026-07-03 \
  --adults 2
```

Never raise the concurrency limit. This is a production reservation system and
the constraint is a courtesy, not a technical ceiling.

### Step 4: Parse the Response

Pipe the raw output through the parser, which extracts every room and board
basis combination and sorts by price.

```bash
bash scripts/fetch_packages.sh --hotel-code RB --check-in 2026-04-10 --check-out 2026-04-12 \
  | python3 scripts/parse_packages.py \
      --hotel-name "Royal Beach Eilat" \
      --check-in 2026-04-10 \
      --check-out 2026-04-12 \
      --adults 2
```

The endpoint returns **HTML, not JSON**. The pricing data is embedded in an
inline script as `var AvailablePackages = [...]`, which the parser extracts and
flattens to one row per room and board basis. Add `--json` for machine-readable
output instead of a table.

The nesting is `AvailablePackages[] -> Sales[] -> BoardBases[]`, with prices
under each board basis:

| Field | Meaning |
|-------|---------|
| `RoomTitle` | Room name, in Hebrew |
| `Sales[].SaleText` | Promotion label, for example "Website Discount" |
| `BoardBases[].BoardBaseCode` | Board basis, suffix `WBB`, `WHB` or `WAI` |
| `GuestRoomPrice.IlsDisplayPrice` | Public web price |
| `SunClubRoomPrice.IlsDisplayPrice` | Sun Club loyalty member price |
| `IlsDisplayOperaPrice` | Rack rate, the struck-through original price |

All prices cover the entire stay, not one night.

Use `IlsDisplayOperaPrice` as the rack rate, **not** `IlsOperaPrice`. At package
hotels such as Beresheet, `IlsOperaPrice` is the room-only rate excluding the
package inclusions, so it falls below the display price and produces a negative
discount. The parser already handles this.

When the hotel is sold out, the HTML carries suggested alternative dates instead
of packages. The parser surfaces them, so offer them rather than just reporting
a dead end.

### Step 5: Present Results

```
Royal Beach Eilat  |  10 to 12 Apr 2026  |  2 nights  |  2 adults

  ROOM TYPE       BOARD       WEB PRICE   SUN CLUB        SAVINGS
  ----------------------------------------------------------------
  חדר משפחה       B&B            4,632      4,388     244 ILS (5%)
  חדר נשיאותי     B&B            4,689      4,442     247 ILS (5%)
  חדר משפחה       Half Board     5,582      5,288     294 ILS (5%)
```

Rules for the output:

- Sort by discounted price ascending, cheapest first
- Always show the web price and the Sun Club price side by side, since the gap
  is the main decision the user is making
- Express savings as both an ILS amount and a percentage off rack rate
- For multi-hotel searches, lead with a ranking of the cheapest option per
  hotel, then break down each hotel underneath
- State prices are for the whole stay, not per night
- Close by telling the user to confirm on isrotel.co.il before booking, because
  live prices shift with caching and session state

## Examples

### Example 1: Single Hotel, Specific Dates

User says: "What's available at Beresheet on 10 to 12 April 2026 for 2 adults?"

Actions:
1. Resolve Beresheet to code `BR` via `references/hotel-directory.md`
2. Run `fetch_packages.sh --hotel-code BR --check-in 2026-04-10 --check-out 2026-04-12 --adults 2`
3. Pipe through `parse_packages.py` with `--hotel-name "Beresheet"`
4. Present the sorted table

Result: Every room and board combination at Beresheet, cheapest first, with web
and Sun Club pricing.

### Example 2: Whole City Comparison

User says: "Find me the cheapest Isrotel in Eilat for the first weekend in July"

Actions:
1. Resolve "Eilat" to the region grouping `RB KS RG AG AM SP LG RC`
2. Resolve "first weekend in July" to check-in 2026-07-03, check-out 2026-07-04,
   and say that you assumed a Friday to Saturday weekend
3. Run `fetch_all.sh --codes "RB KS RG AG AM SP LG RC" --check-in 2026-07-03 --check-out 2026-07-04`
4. Build a ranking of the single cheapest option at each of the 8 hotels, then
   detail the top 3

Result: A cross-hotel ranking naming the cheapest property and room.

### Example 3: Hebrew Request with a Family

User says: "chadarim pnuyim be-Cramim le-mishpacha, 2 mevugarim ve-2 yeladim"

Actions:
1. Translate using `references/hebrew-glossary.md`: available rooms at Cramim
   for a family, 2 adults and 2 children
2. Resolve Cramim to code `CR`
3. Ask for dates, which the request omits
4. Run with `--adults 2 --children 2`
5. Present results, flagging which room types actually sleep 4

Result: Family-suitable rooms at Cramim with correct occupancy pricing.

### Example 4: No Availability

User says: "Check Lagoona for Yom Kippur"

Actions:
1. Resolve Lagoona to `LG` and Yom Kippur 2026 to its dates
2. Run the fetch and receive HTTP 200 with an empty `packages` array
3. Say plainly that the hotel is sold out for those dates rather than printing
   an empty table
4. Show the alternative dates the parser extracted, or offer the other Eilat properties

Result: A clear sold-out answer plus a concrete next step.

## Bundled Resources

### Scripts

- `scripts/fetch_packages.sh` -- Fetches room packages for one hotel and prints
  the raw HTML response. Run: `bash scripts/fetch_packages.sh --hotel-code RB --check-in 2026-04-10 --check-out 2026-04-12`
- `scripts/fetch_all.sh` -- Fetches several hotels in parallel with concurrency
  capped at 4. Run: `bash scripts/fetch_all.sh --codes "RB KS" --check-in 2026-04-10 --check-out 2026-04-12`
- `scripts/parse_packages.py` -- Reads the HTML on stdin, extracts `AvailablePackages`,
  and prints a sorted price table. Run: `python3 scripts/parse_packages.py --help`

### References

- `references/hotel-directory.md` -- All 25 property codes by region, brand
  segments, and ready-made region groupings. Consult when resolving a hotel or
  city name to a code, or building a multi-hotel search.
- `references/api-reference.md` -- Full endpoint specification: query object
  fields, required headers, response shape, price field meanings, board base
  codes, and HTTP status handling. Consult when building a request by hand or
  debugging an unexpected response.
- `references/hebrew-glossary.md` -- Booking, guest type, board basis and room
  type terminology in Hebrew with transliterations. Consult when the user writes
  in Hebrew or when translating room names returned by the API.

## Reference Links

Official sources for verifying and updating the information in this skill.

| Source | URL | What to Check |
|--------|-----|---------------|
| Isrotel official site | https://www.isrotel.co.il | Hotel list, renames, new properties |
| Isrotel English site | https://www.isrotel.com | English hotel names and descriptions |
| Isrotel Sun Club | https://www.isrotel.co.il/sun-club/ | Loyalty programme terms and member discount rates |
| Israel Ministry of Tourism | https://www.gov.il/en/departments/ministry_of_tourism | Tourist VAT exemption rules affecting Eilat pricing |
| Isrotel hotel index | https://www.isrotel.co.il/hotels/ | Live list of every property, used to confirm the code directory |
| Isrotel terms of use | https://www.isrotel.co.il/terms-of-use/ | Site terms governing automated access |

## Gotchas

- The response is HTML, not JSON, despite the endpoint looking like a JSON API.
  The data lives in an inline `var AvailablePackages = [...]` script block.
  Calling `json.loads()` on the response body fails.
- Rack rate is `IlsDisplayOperaPrice`, not `IlsOperaPrice`. At package hotels the
  latter excludes package inclusions and yields negative savings.
- `fetch_all.sh` avoids `declare -A` because macOS ships bash 3.2, where
  associative arrays do not exist. Keep any new lookups as case statements.
- The `query` object needs both `HotelCodes: ["RB"]` and `HotelCode: "RB"`.
  Setting only the array returns an empty result set with HTTP 200, which looks
  like a sold-out hotel rather than a malformed request.
- Dates need the literal `T00:00Z` suffix. A bare `YYYY-MM-DD` returns HTTP 500.
- The `Referer: https://www.isrotel.co.il/` header is mandatory and a
  browser-like `User-Agent` is required. A default curl agent gets HTTP 403.
- Prices cover the entire stay, not one night. Presenting a 2-night total as a
  nightly rate understates the cost by half.
- Room names return in Hebrew because `cultureLCID=1037`. Keep them in Hebrew
  and translate alongside rather than replacing, since the Hebrew name is what
  the user will see on the booking site.
- Two rooms means two entries in the `Rooms` array, not `NumberOfRooms: 2`.

## Troubleshooting

### Error: HTTP 403 Forbidden

Cause: Missing `Referer` header, or a `User-Agent` the server does not accept.
Solution: Send both `Referer: https://www.isrotel.co.il/` and a browser-like
`User-Agent`. The bundled scripts already do this; check for typos if you built
the request by hand.

### Error: HTTP 500 Internal Server Error

Cause: Almost always a malformed date in the `query` object.
Solution: Confirm `StartDate` and `EndDate` end with `T00:00Z`, for example
`2026-04-10T00:00Z`. Also confirm `check_out` is strictly after `check_in`.

### Error: No offers found on HTTP 200

Cause: Either genuine sold-out dates, or `HotelCode` was omitted from the query.
Solution: Check `data-has-results` in the HTML. If it is `False`, the hotel truly
is unavailable, and the parser will print the alternative dates the site
suggests. If it is `True` but no rows appear, verify `HotelCode` duplicates
`HotelCodes[0]`.

### Error: Negative savings in the output

Cause: Reading `IlsOperaPrice` as the rack rate at a package hotel.
Solution: Use `IlsDisplayOperaPrice`. See the note in Step 4.

### Error: declare: -A: invalid option

Cause: Running `fetch_all.sh` on bash 3.2, which macOS still ships as `/bin/bash`.
Solution: The bundled script uses case statements instead of associative arrays,
so update to the current version. Do not reintroduce `declare -A`.

### Error: HTTP 429 Too Many Requests

Cause: Too many concurrent requests during a multi-hotel search.
Solution: Wait 2 seconds and retry once. Keep concurrency at or below 4 with
roughly 300ms between batches. If it fails again, report it rather than
hammering the endpoint.

### Error: json.JSONDecodeError while parsing

Cause: Treating the response as a single JSON document.
Solution: Split on newlines, attempt `json.loads()` per line, and skip failures.
Only the line containing `"packages"` carries the data you need.
