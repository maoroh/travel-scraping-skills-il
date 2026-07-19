#!/usr/bin/env bash
# fetch_all.sh
# Fetches packages for multiple hotels in parallel (max 4 concurrent).
# Outputs one HTML file per hotel in a temp directory, then prints a summary.
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

# Lookups use case statements rather than associative arrays, because macOS
# ships bash 3.2 and `declare -A` requires bash 4 or newer.

KNOWN_LOCATIONS="eilat, dead sea, negev, mitzpe ramon, jerusalem, tel aviv, herzliya, north, kinneret"

codes_for_location() {
  case "$1" in
    eilat)                 echo "RB KS RG AG AM SP LG RC" ;;
    "dead sea"|deadsea)    echo "DS GA" ;;
    "mitzpe ramon")        echo "BR RI" ;;
    negev)                 echo "BR RI KD" ;;
    jerusalem)             echo "CR OR" ;;
    "tel aviv"|telaviv)    echo "RT TT PT AL TLVTX" ;;
    herzliya)              echo "TLVAK" ;;
    north)                 echo "AY MH CF" ;;
    kinneret)              echo "YM" ;;
    *)                     echo "" ;;
  esac
}

name_for_code() {
  case "$1" in
    RB)    echo "Royal Beach Eilat" ;;
    KS)    echo "King Solomon Eilat" ;;
    RG)    echo "Royal Garden Eilat" ;;
    AG)    echo "Agamim Eilat" ;;
    AM)    echo "Yam Suf Eilat" ;;
    SP)    echo "Sport Club Eilat All Inclusive" ;;
    LG)    echo "Lagoona Eilat All Inclusive" ;;
    RC)    echo "Riviera Eilat" ;;
    DS)    echo "Nebo (Dead Sea)" ;;
    GA)    echo "Noga (Dead Sea)" ;;
    BR)    echo "Beresheet" ;;
    RI)    echo "Daroma" ;;
    KD)    echo "Kedma" ;;
    CR)    echo "Cramim" ;;
    OR)    echo "Orient Jerusalem" ;;
    RT)    echo "Royal Beach Tel Aviv" ;;
    TT)    echo "Sea Tower Tel Aviv" ;;
    PT)    echo "Port Tower Tel Aviv" ;;
    AL)    echo "Alberto Tel Aviv" ;;
    TLVTX) echo "Gymnasya Tel Aviv" ;;
    TLVAK) echo "Publica Herzliya" ;;
    AY)    echo "Ayla" ;;
    MH)    echo "Mizpe Hayamim" ;;
    YM)    echo "Goma Kinneret" ;;
    CF)    echo "Carmel Forest Estate" ;;
    *)     echo "$1" ;;
  esac
}

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
  CODES=$(codes_for_location "$LOC_KEY")
  if [[ -z "$CODES" ]]; then
    echo "Unknown location: $LOCATION" >&2
    echo "Known locations: $KNOWN_LOCATIONS" >&2
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
  local outfile="$TMPDIR/${code}.html"
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
  outfile="$TMPDIR/${code}.html"
  hotel_name=$(name_for_code "$code")
  if [[ -f "$outfile" && -s "$outfile" ]]; then
    cat "$outfile" | python3 "$SCRIPT_DIR/parse_packages.py" \
      --hotel-name "$hotel_name" \
      --check-in "$CHECK_IN" \
      --check-out "$CHECK_OUT" \
      --adults "$ADULTS"
  else
    echo
    echo "$hotel_name: fetch failed"
    echo
  fi
done
