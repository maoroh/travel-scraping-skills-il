#!/usr/bin/env bash
# fetch_packages.sh
# Fetches room packages for a single Isrotel hotel via their Umbraco API.
#
# Usage:
#   bash fetch_packages.sh --hotel-code RB --check-in 2026-04-10 --check-out 2026-04-12
#   bash fetch_packages.sh --hotel-code RB --check-in 2026-04-10 --check-out 2026-04-12 --adults 2 --children 1
#
# Output: Raw newline-delimited JSON from the API (pipe to fetch_packages_parse.sh for clean output)

set -euo pipefail

# ── Defaults ──────────────────────────────────────────────────────────────────
HOTEL_CODE=""
CHECK_IN=""
CHECK_OUT=""
ADULTS=2
CHILDREN=0
INFANTS=0

# ── Arg parsing ───────────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --hotel-code)  HOTEL_CODE="$2";  shift 2 ;;
    --check-in)    CHECK_IN="$2";    shift 2 ;;
    --check-out)   CHECK_OUT="$2";   shift 2 ;;
    --adults)      ADULTS="$2";      shift 2 ;;
    --children)    CHILDREN="$2";    shift 2 ;;
    --infants)     INFANTS="$2";     shift 2 ;;
    *) echo "Unknown arg: $1" >&2; exit 1 ;;
  esac
done

if [[ -z "$HOTEL_CODE" || -z "$CHECK_IN" || -z "$CHECK_OUT" ]]; then
  echo "Usage: $0 --hotel-code <CODE> --check-in <YYYY-MM-DD> --check-out <YYYY-MM-DD>" >&2
  exit 1
fi

# ── Build JSON payloads ───────────────────────────────────────────────────────
QUERY=$(python3 -c "
import json, sys
print(json.dumps({
    'HotelCodes': ['$HOTEL_CODE'],
    'PreferredRoomCode': None,
    'StartDate': '${CHECK_IN}T00:00Z',
    'EndDate': '${CHECK_OUT}T00:00Z',
    'Rooms': [{
        'AdultsNumber': $ADULTS,
        'ChildrenNumber': $CHILDREN,
        'InfantsNumber': $INFANTS,
        'NumberOfRooms': 1
    }],
    'searchType': 3,
    'DiscountId': None,
    'IsOfflineDiscount': False,
    'IncludeFlight': None,
    'FlightFrom': '-1',
    'RegionName': None,
    'HotelCode': '$HOTEL_CODE'
}))
")

CURRENCY_QUERY='{"Currency":"NIS","Channel":"WHENIS"}'

# ── Fire the request ──────────────────────────────────────────────────────────
BASE_URL="https://www.isrotel.co.il/umbraco/Surface/Search/GetSingleHotelSearchResults"

curl --silent --fail --show-error \
  --max-time 20 \
  --retry 1 \
  --retry-delay 2 \
  -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36" \
  -H "Accept: application/json, text/plain, */*" \
  -H "Accept-Language: he-IL,he;q=0.9,en;q=0.8" \
  -H "Referer: https://www.isrotel.co.il/" \
  -G \
  --data-urlencode "cultureLCID=1037" \
  --data-urlencode "query=${QUERY}" \
  --data-urlencode "currencyQuery=${CURRENCY_QUERY}" \
  --data-urlencode "homeRootNodeId=1050" \
  --data-urlencode "isSunClubOrAgt=false" \
  --data-urlencode "isMobileDevice=True" \
  --data-urlencode "ec=" \
  --data-urlencode "couponCode=" \
  "$BASE_URL"
