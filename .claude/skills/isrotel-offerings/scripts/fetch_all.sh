#!/usr/bin/env bash
# fetch_all.sh
# Fetches packages for multiple hotels in parallel (max 4 concurrent).
# Outputs one JSON file per hotel in a temp directory, then prints a summary.
#
# Usage:
#   bash fetch_all.sh --codes "RB KS RG" --check-in 2026-07-01 --check-out 2026-07-03 --adults 2
#   bash fetch_all.sh --location eilat --check-in 2026-07-01 --check-out 2026-07-03

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── Defaults ──────────────────────────────────────────────────────────────────
CODES=""
LOCATION=""
CHECK_IN=""
CHECK_OUT=""
ADULTS=2
CHILDREN=0
INFANTS=0
CONCURRENCY=4

# ── Location → hotel codes map ────────────────────────────────────────────────
declare -A LOCATION_CODES
LOCATION_CODES["eilat"]="RB KS RG AG AM SP LG RC"
LOCATION_CODES["dead sea"]="DS GA"
LOCATION_CODES["deadsea"]="DS GA"
LOCATION_CODES["mitzpe ramon"]="BR RI"
LOCATION_CODES["negev"]="BR RI KD"
LOCATION_CODES["jerusalem"]="CR OR"
LOCATION_CODES["tel aviv"]="RT TT PT AL TLVTX"
LOCATION_CODES["telaviv"]="RT TT PT AL TLVTX"
LOCATION_CODES["herzliya"]="TLVAK"
LOCATION_CODES["north"]="AY MH CF"
LOCATION_CODES["kinneret"]="YM"

# Hotel code → name map
declare -A HOTEL_NAMES
HOTEL_NAMES["RB"]="Royal Beach Eilat"
HOTEL_NAMES["KS"]="King Solomon Eilat"
HOTEL_NAMES["RG"]="Royal Garden Eilat"
HOTEL_NAMES["AG"]="Agamim Eilat"
HOTEL_NAMES["AM"]="Yam Suf Eilat"
HOTEL_NAMES["SP"]="Sport Club Eilat All Inclusive"
HOTEL_NAMES["LG"]="Lagoona Eilat All Inclusive"
HOTEL_NAMES["RC"]="Riviera Eilat"
HOTEL_NAMES["DS"]="Nebo (Dead Sea)"
HOTEL_NAMES["GA"]="Noga (Dead Sea)"
HOTEL_NAMES["BR"]="Beresheet"
HOTEL_NAMES["RI"]="Daroma"
HOTEL_NAMES["KD"]="Kedma"
HOTEL_NAMES["CR"]="Cramim"
HOTEL_NAMES["OR"]="Orient Jerusalem"
HOTEL_NAMES["RT"]="Royal Beach Tel Aviv"
HOTEL_NAMES["TT"]="Sea Tower Tel Aviv"
HOTEL_NAMES["PT"]="Port Tower Tel Aviv"
HOTEL_NAMES["AL"]="Alberto Tel Aviv"
HOTEL_NAMES["TLVTX"]="Gymnasya Tel Aviv"
HOTEL_NAMES["TLVAK"]="Publica Herzliya"
HOTEL_NAMES["AY"]="Ayla"
HOTEL_NAMES["MH"]="Mizpe Hayamim"
HOTEL_NAMES["YM"]="Goma Kinneret"
HOTEL_NAMES["CF"]="Carmel Forest Estate"

# ── Arg parsing ───────────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --codes)       CODES="$2";      shift 2 ;;
    --location)    LOCATION="$2";   shift 2 ;;
    --check-in)    CHECK_IN="$2";   shift 2 ;;
    --check-out)   CHECK_OUT="$2";  shift 2 ;;
    --adults)      ADULTS="$2";     shift 2 ;;
    --children)    CHILDREN="$2";   shift 2 ;;
    --infants)     INFANTS="$2";    shift 2 ;;
    --concurrency) CONCURRENCY="$2"; shift 2 ;;
    *) echo "Unknown arg: $1" >&2; exit 1 ;;
  esac
done

# Resolve codes from location if needed
if [[ -z "$CODES" && -n "$LOCATION" ]]; then
  LOC_KEY=$(echo "$LOCATION" | tr '[:upper:]' '[:lower:]')
  CODES="${LOCATION_CODES[$LOC_KEY]:-}"
  if [[ -z "$CODES" ]]; then
    echo "Unknown location: $LOCATION" >&2
    echo "Known locations: ${!LOCATION_CODES[*]}" >&2
    exit 1
  fi
fi

if [[ -z "$CODES" || -z "$CHECK_IN" || -z "$CHECK_OUT" ]]; then
  echo "Usage: $0 --codes 'RB KS' --check-in YYYY-MM-DD --check-out YYYY-MM-DD" >&2
  echo "   or: $0 --location eilat --check-in YYYY-MM-DD --check-out YYYY-MM-DD" >&2
  exit 1
fi

# ── Parallel fetch ─────────────────────────────────────────────────────────────
TMPDIR=$(mktemp -d)
trap "rm -rf $TMPDIR" EXIT

codes_array=($CODES)
total=${#codes_array[@]}
done_count=0

fetch_one() {
  local code="$1"
  local outfile="$TMPDIR/${code}.json"
  bash "$SCRIPT_DIR/fetch_packages.sh" \
    --hotel-code "$code" \
    --check-in "$CHECK_IN" \
    --check-out "$CHECK_OUT" \
    --adults "$ADULTS" \
    --children "$CHILDREN" \
    --infants "$INFANTS" \
    > "$outfile" 2>/dev/null && echo "OK:$code" || echo "ERR:$code"
}

export -f fetch_one
export SCRIPT_DIR CHECK_IN CHECK_OUT ADULTS CHILDREN INFANTS TMPDIR

# Run in batches of CONCURRENCY
for ((i=0; i<total; i+=CONCURRENCY)); do
  batch=("${codes_array[@]:$i:$CONCURRENCY}")
  pids=()
  for code in "${batch[@]}"; do
    fetch_one "$code" &
    pids+=($!)
  done
  for pid in "${pids[@]}"; do
    wait "$pid"
  done
  # Polite delay between batches
  if (( i + CONCURRENCY < total )); then
    sleep 0.3
  fi
done

# ── Parse and print all results ───────────────────────────────────────────────
for code in "${codes_array[@]}"; do
  outfile="$TMPDIR/${code}.json"
  hotel_name="${HOTEL_NAMES[$code]:-$code}"
  if [[ -f "$outfile" && -s "$outfile" ]]; then
    cat "$outfile" | python3 "$SCRIPT_DIR/parse_packages.py" \
      --hotel-name "$hotel_name" \
      --check-in "$CHECK_IN" \
      --check-out "$CHECK_OUT" \
      --adults "$ADULTS"
  else
    echo
    echo "🏨 $hotel_name — fetch failed or no availability"
    echo
  fi
done
