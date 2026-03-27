---
name: isrotel-offerings
description: >
  Fetch live hotel room packages and pricing directly from Isrotel's booking
  API using cURL (no MCP required). Use this skill whenever the user asks
  about Isrotel hotel availability, room prices, packages, deals, or
  promotions — even if they just mention a hotel name like "Royal Beach",
  "Beresheet", "Cramim", "Lagoona", or any other Isrotel property. Also
  trigger when the user says things like "find me a deal at Isrotel", "what
  rooms are available at X hotel this weekend", "cheapest Isrotel option",
  or "search Isrotel for dates". Always prefer this skill over web search
  for anything Isrotel-related.
---

# Isrotel Offerings Skill

Fetches live room packages directly from Isrotel's internal Umbraco search
API using cURL, normalizes the response, and presents results clearly.

---

## Step 1 — Resolve inputs

Gather these from the user's message (ask only for what's missing):

| Field | Required | Default | Notes |
|---|---|---|---|
| `hotel_code` | yes* | — | See hotel directory below |
| `check_in` | yes | — | Any natural date, convert to `YYYY-MM-DD` |
| `check_out` | yes | — | Any natural date, convert to `YYYY-MM-DD` |
| `adults` | no | `2` | |
| `children` | no | `0` | Age > 2 |
| `infants` | no | `0` | Age < 2 |
| `location` | yes* | — | Alternative to hotel_code — search all hotels in that city |

\* Provide either `hotel_code` OR `location`. If `location` is given, look up
all matching codes from the Hotel Directory and fetch them in parallel.

---

## Step 2 — Build the cURL request

The endpoint is Isrotel's Umbraco search API. Use the fetch script:

```bash
bash /path/to/skill/scripts/fetch_packages.sh \
  --hotel-code RB \
  --check-in 2026-04-10 \
  --check-out 2026-04-12 \
  --adults 2 \
  --children 0 \
  --infants 0
```

Or call it inline — see **scripts/fetch_packages.sh** for the full cURL
construction. The script prints newline-delimited JSON; parse `packages[]`
from the line that contains it.

### URL construction reference

```
BASE = https://www.isrotel.co.il/umbraco/Surface/Search/GetSingleHotelSearchResults

query param `query` (JSON-encoded):
{
  "HotelCodes": ["<hotel_code>"],
  "PreferredRoomCode": null,
  "StartDate": "<YYYY-MM-DD>T00:00Z",
  "EndDate": "<YYYY-MM-DD>T00:00Z",
  "Rooms": [{ "AdultsNumber": 2, "ChildrenNumber": 0, "InfantsNumber": 0, "NumberOfRooms": 1 }],
  "searchType": 3,
  "DiscountId": null,
  "IsOfflineDiscount": false,
  "IncludeFlight": null,
  "FlightFrom": "-1",
  "RegionName": null,
  "HotelCode": "<hotel_code>"
}

query param `currencyQuery` (JSON-encoded):
{ "Currency": "NIS", "Channel": "WHENIS" }

Fixed params:
  cultureLCID=1037
  homeRootNodeId=1050
  isSunClubOrAgt=false
  isMobileDevice=True
  ec=
  couponCode=
```

Required headers:
```
User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36
Accept: application/json, text/plain, */*
Accept-Language: he-IL,he;q=0.9,en;q=0.8
Referer: https://www.isrotel.co.il/
```

---

## Step 3 — Parse the response

The API returns **newline-delimited JSON** (not a JSON array). Each line is a
separate object. The line containing `"packages"` has this shape:

```json
{
  "status": "success",
  "packages": [
    {
      "title": "<room type in Hebrew>",
      "sales": [
        {
          "sale_title": "Website Discount",
          "board_bases": [
            {
              "BoardBaseCode": "INT25WBB",
              "BoardBaseDictionaryText": "<board base label in Hebrew>",
              "GuestRoomPrice": {
                "IlsDisplayPrice": 4632,
                "IlsOperaPrice": 4876,
                "TotalDiscount": 243.8
              },
              "SunClubRoomPrice": {
                "IlsDisplayPrice": 4388,
                "IlsOperaPrice": 4876,
                "TotalDiscount": 487.6
              }
            }
          ]
        }
      ]
    }
  ]
}
```

**Key price fields:**
- `IlsOperaPrice` — rack / full price (ILS)
- `IlsDisplayPrice` (GuestRoomPrice) — web discounted price
- `IlsDisplayPrice` (SunClubRoomPrice) — Sun Club member price
- `TotalDiscount` — ILS savings vs rack

**Common BoardBaseCodes:**
- `*WBB` → Bed & Breakfast (לינה וא. בוקר)
- `*WHB` → Half Board (חצי פנסיון)
- `*WAI` / `*AI` → All Inclusive

---

## Step 4 — Present results

Use `jq` (via the parse script) or parse inline. Present results in this format:

```
🏨 Royal Beach Eilat  |  10–12 Apr 2026  |  2 nights  |  2 adults

ROOM TYPE              BOARD       WEB PRICE    SUN CLUB     SAVINGS
─────────────────────────────────────────────────────────────────────
חדר משפחה             B&B         ₪4,632       ₪4,388       ₪244 (5%)
חדר משפחה             Half Board  ₪5,582       ₪5,288       ₪294 (5%)
חדר נשיאותי           B&B         ₪4,689       ₪4,442       ₪247 (5%)
...
```

- Always show both web price and Sun Club price
- Show savings both as ILS amount and % off rack
- Sort by discounted price ascending (cheapest first)
- If searching multiple hotels, group by hotel with a summary line per hotel

For multi-hotel searches, lead with a **summary ranking** (cheapest option
per hotel) before breaking down per-hotel details.

---

## Hotel Directory

Use this to resolve names → codes and to build multi-hotel searches.

### Eilat
| Code | Name |
|------|------|
| `RB` | Royal Beach Eilat |
| `KS` | King Solomon Eilat |
| `RG` | Royal Garden Eilat |
| `AG` | Agamim Eilat |
| `AM` | Yam Suf Eilat |
| `SP` | Sport Club Eilat All Inclusive |
| `LG` | Lagoona Eilat All Inclusive |
| `RC` | Riviera Eilat |

### Dead Sea
| Code | Name |
|------|------|
| `DS` | Nebo |
| `GA` | Noga |

### Mitzpe Ramon / Negev
| Code | Name |
|------|------|
| `BR` | Beresheet |
| `RI` | Daroma (formerly Ramon Inn) |
| `KD` | Kedma |

### Jerusalem
| Code | Name |
|------|------|
| `CR` | Cramim |
| `OR` | Orient |

### Tel Aviv / Herzliya
| Code | Name |
|------|------|
| `RT` | Royal Beach Tel Aviv |
| `TT` | Sea Tower Tel Aviv |
| `PT` | Port Tower Tel Aviv |
| `AL` | Alberto Tel Aviv |
| `TLVTX` | Gymnasya Tel Aviv |
| `TLVAK` | Publica Herzliya |

### North / Kinneret
| Code | Name |
|------|------|
| `AY` | Ayla |
| `MH` | Mizpe Hayamim |
| `YM` | Goma Kinneret |
| `CF` | Carmel Forest Estate |

### Segments
- **exclusive**: RB, BR, CR, OR, RT, MH, CF
- **collection**: KS, RG, AG, AM, SP, LG, RC, DS, GA, RI, KD, AY, YM
- **design**: TT, PT, AL, TLVTX, TLVAK

---

## Multi-hotel search

When fetching multiple hotels (e.g. all Eilat hotels), run requests in
parallel using the `fetch_all.sh` script or by constructing concurrent bash
subprocesses. Limit concurrency to 4 to avoid rate limiting. Add a 300ms
delay between batches.

```bash
bash scripts/fetch_all.sh \
  --codes "RB KS RG AG AM SP LG RC" \
  --check-in 2026-07-01 \
  --check-out 2026-07-03 \
  --adults 2
```

---

## Error handling

- **HTTP non-200**: Report the status and hotel code; skip and continue for
  multi-hotel searches.
- **Empty packages array**: Hotel has no availability for those dates — say so
  explicitly rather than showing an empty table.
- **Malformed JSON line**: Skip that line; the useful data is on the line
  containing `"packages"`.
- **Rate limiting / 429**: Wait 2 seconds and retry once. If it fails again,
  report it.
