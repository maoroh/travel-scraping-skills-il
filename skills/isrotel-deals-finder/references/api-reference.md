# Isrotel Booking API Reference

Full request and response specification for Isrotel's Umbraco search endpoint.
Consult when constructing a request by hand instead of using the bundled
scripts, when debugging an unexpected response shape, or when you need to
understand a price field.

This is an undocumented internal endpoint used by the isrotel.co.il booking
widget. It is not a public API and carries no stability guarantee.

## Endpoint

```
GET https://www.isrotel.co.il/umbraco/Surface/Search/GetSingleHotelSearchResults
```

## Query Parameters

| Parameter | Value | Notes |
|-----------|-------|-------|
| `query` | JSON object, URL-encoded | The search itself, see below |
| `currencyQuery` | JSON object, URL-encoded | `{"Currency":"NIS","Channel":"WHENIS"}` |
| `cultureLCID` | `1037` | Hebrew locale. Room names return in Hebrew |
| `homeRootNodeId` | `1050` | Umbraco site root, fixed |
| `isSunClubOrAgt` | `false` | Set true to price as a logged-in Sun Club member |
| `isMobileDevice` | `True` | Capital T is required, the server is case-sensitive here |
| `ec` | empty | Reserved |
| `couponCode` | empty | Populate to apply a promo code |

### The `query` object

```json
{
  "HotelCodes": ["RB"],
  "PreferredRoomCode": null,
  "StartDate": "2026-04-10T00:00Z",
  "EndDate": "2026-04-12T00:00Z",
  "Rooms": [
    {
      "AdultsNumber": 2,
      "ChildrenNumber": 0,
      "InfantsNumber": 0,
      "NumberOfRooms": 1
    }
  ],
  "searchType": 3,
  "DiscountId": null,
  "IsOfflineDiscount": false,
  "IncludeFlight": null,
  "FlightFrom": "-1",
  "RegionName": null,
  "HotelCode": "RB"
}
```

| Field | Notes |
|-------|-------|
| `HotelCodes` | Array, but this endpoint honours only the first entry. For several hotels, issue one request each |
| `HotelCode` | Must duplicate `HotelCodes[0]`. Omitting it returns an empty result set |
| `StartDate` / `EndDate` | ISO date plus the literal suffix `T00:00Z`. A plain `YYYY-MM-DD` is rejected |
| `Rooms` | One entry per physical room. Two rooms means two array entries, not `NumberOfRooms: 2` |
| `ChildrenNumber` | Guests aged 2 to 12 |
| `InfantsNumber` | Guests under 2 |
| `searchType` | `3` is the single-hotel date search. Other values are undocumented |

## Required Headers

```
User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36
Accept: application/json, text/plain, */*
Accept-Language: he-IL,he;q=0.9,en;q=0.8
Referer: https://www.isrotel.co.il/
```

The `Referer` header is mandatory. Without it the endpoint returns HTTP 403.
A browser-like `User-Agent` is also required; a default curl agent is rejected.

## Response Format

Despite the endpoint's appearance, the response is **HTML**, not JSON. It is a
rendered Umbraco partial for the booking widget. The pricing data is embedded in
an inline script block as a JavaScript variable:

```
<script>if(10>0){var AvailablePackages=[ ... ];
```

Extract it with a regex such as `var\s+AvailablePackages\s*=\s*(\[.*?\])\s*;`
and parse the captured group as JSON. `scripts/parse_packages.py` does this.

The wrapper element also carries a useful flag:

```
<div class="container search-query-id" data-has-results=True ...>
```

`data-has-results` is `True` or `False` and is the quickest availability check.

### AvailablePackages Structure

```
AvailablePackages[]           one entry per room category
  RoomTitle                   room name in Hebrew
  IsPackage                   true when the rate bundles extras
  Rooms[]
    RoomCode                  short code, for example STRS
    RoomName                  room name in Hebrew
    AvailableUnits            rooms left at this rate
    Occupancy                 {Adults, Children, Infants}
  Sales[]                     one entry per promotion
    SaleText                  label, for example "Website Discount"
    IsNonRefundable           true when the rate cannot be cancelled
    BoardBases[]              one entry per board basis
      BoardBaseCode           for example INT33WBB
      BoardBaseDictionaryText Hebrew board label
      GuestRoomPrice          price tier for non-members
      SunClubRoomPrice        price tier for Sun Club members
```

### Price Fields

Each price tier (`GuestRoomPrice`, `SunClubRoomPrice`) contains:

| Field | Meaning |
|-------|---------|
| `IlsDisplayPrice` | What the guest actually pays for that tier |
| `IlsDisplayOperaPrice` | Rack rate, the struck-through original price |
| `IlsOperaPrice` | Room-only rate, **excludes package inclusions** |
| `OperaPriceWithoutPackages` | Same as `IlsOperaPrice` |
| `TotalDiscount` | Saving the site reports for that tier |

**Use `IlsDisplayOperaPrice` as the rack rate.** At package hotels
(`IsPackage: true`) `IlsOperaPrice` drops below `IlsDisplayPrice` because it
strips the package inclusions, which produces a negative discount. Observed at
Beresheet for 13 to 15 August 2026:

| Hotel | IsPackage | IlsDisplayPrice | IlsOperaPrice | IlsDisplayOperaPrice |
|-------|-----------|-----------------|---------------|----------------------|
| Royal Beach | true | 4,727 | 4,976 | 4,976 |
| Beresheet | true | 7,812 | 6,969 | 8,224 |

Note that `TotalDiscount` is not always exactly `IlsDisplayOperaPrice` minus
`IlsDisplayPrice`. At Beresheet the difference is 412 while `TotalDiscount`
reports 348.47. Prefer the computed difference for a displayed saving, since it
matches the two prices shown beside it.

All prices are for the **entire stay**, not per night, and include VAT. Eilat
bookings are VAT-exempt for tourists, which the API does not model, so an
overseas guest may be charged less at the desk.

### Sold-Out Responses

When `data-has-results=False`, the HTML contains no `AvailablePackages` and
instead offers alternative dates:

```
<label data-alt-arrival-date=13-08-2026 data-alt-departure-date=15-08-2026 ...>
```

Dates are `DD-MM-YYYY`, so reverse the parts to get ISO format. The parser
extracts these and prints them as suggestions.

### Board Base Codes

The code is a prefix plus a board suffix, for example `INT25WBB`. Match on the
suffix.

| Suffix | Board Basis | Hebrew |
|--------|-------------|--------|
| `WBB` / `BB` | Bed and breakfast | לינה וארוחת בוקר |
| `WHB` / `HB` | Half board | חצי פנסיון |
| `WAI` / `AI` | All inclusive | הכל כלול |

`BoardBaseDictionaryText` carries the Hebrew label directly and is the safer
field to display when present.

## HTTP Status Codes

| Status | Meaning | Action |
|--------|---------|--------|
| 200 | Success, may still contain an empty `packages` array | Parse normally |
| 403 | Missing or wrong `Referer` / `User-Agent` | Fix headers and retry |
| 429 | Rate limited | Wait 2 seconds, retry once, then report |
| 500 | Malformed `query`, often a bad date format | Check the `T00:00Z` suffix |

## Rate Limiting

There is no published limit. Empirically, four concurrent requests are safe.
Keep concurrency at or below 4 and insert roughly 300ms between batches. This
is a courtesy constraint on a production booking system, not a technical one,
so respect it.
