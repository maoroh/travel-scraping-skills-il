#!/usr/bin/env python3
"""
parse_packages.py
Reads raw Isrotel API output (an HTML fragment) from stdin and prints a clean,
sorted table of room offers.

The endpoint returns a rendered HTML partial, not JSON. The pricing data is
embedded in an inline script as `var AvailablePackages = [...]`. This script
extracts that array and flattens it to one row per room and board basis.

When the hotel is sold out, the HTML instead carries suggested alternative
dates, which this script surfaces so the caller can offer them.

Usage:
    bash fetch_packages.sh --hotel-code RB --check-in 2026-08-13 --check-out 2026-08-15 | \
        python3 parse_packages.py --hotel-name "Royal Beach Eilat" \
            --check-in 2026-08-13 --check-out 2026-08-15 --adults 2

    Add --json to emit machine-readable output instead of a table.
"""

import sys
import re
import json
import argparse
from datetime import date

BOARD_BASE_LABELS = {
    "BB": "B&B",
    "HB": "Half Board",
    "AI": "All Inclusive",
    "WBB": "B&B",
    "WHB": "Half Board",
    "WAI": "All Inclusive",
}

PACKAGES_RE = re.compile(r"var\s+AvailablePackages\s*=\s*(\[.*?\])\s*;", re.S)
ALT_DATE_RE = re.compile(
    r'data-alt-arrival-date=["\']?(\d{2}-\d{2}-\d{4})["\']?'
    r"[^>]*?"
    r'data-alt-departure-date=["\']?(\d{2}-\d{2}-\d{4})["\']?',
    re.S,
)
HAS_RESULTS_RE = re.compile(r'data-has-results=["\']?(True|False)', re.I)


def board_label(code: str) -> str:
    # Codes look like "INT33WBB", take the board suffix
    for suffix in ("WAI", "WHB", "WBB", "AI", "HB", "BB"):
        if code.endswith(suffix):
            return BOARD_BASE_LABELS[suffix]
    return code


def rack_price(price: dict, display: float) -> float:
    """Return the struck-through original price for a price tier.

    At package hotels (IsPackage true) `IlsOperaPrice` is the room-only rate
    excluding the package inclusions, so it can fall below the display price
    and yield a negative discount. `IlsDisplayOperaPrice` is the figure the
    site actually strikes through, so prefer it and fall back only if absent
    or implausible.
    """
    for key in ("IlsDisplayOperaPrice", "IlsOperaPrice"):
        value = price.get(key)
        if value and value >= display:
            return value
    return display


def nights_between(check_in: str, check_out: str) -> int:
    return (date.fromisoformat(check_out) - date.fromisoformat(check_in)).days


def fmt_date(iso: str) -> str:
    return date.fromisoformat(iso).strftime("%-d %b %Y")


def extract_packages_json(raw: str) -> list:
    """Pull the AvailablePackages array out of the inline script block."""
    m = PACKAGES_RE.search(raw)
    if not m:
        return []
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError:
        return []


def extract_alt_dates(raw: str) -> list:
    """Return suggested alternative date pairs as (check_in, check_out) ISO strings."""
    out = []
    for arrive, depart in ALT_DATE_RE.findall(raw):
        try:
            d1 = "-".join(reversed(arrive.split("-")))
            d2 = "-".join(reversed(depart.split("-")))
            date.fromisoformat(d1)
            date.fromisoformat(d2)
        except ValueError:
            continue
        if (d1, d2) not in out:
            out.append((d1, d2))
    return out


def parse_packages(raw: str) -> list:
    """Flatten AvailablePackages to one row per room and board basis."""
    rows = []
    for pkg in extract_packages_json(raw):
        rooms = pkg.get("Rooms") or []
        room_name = pkg.get("RoomTitle") or (rooms[0].get("RoomName") if rooms else "")
        room_code = rooms[0].get("RoomCode", "") if rooms else ""
        units = rooms[0].get("AvailableUnits") if rooms else None

        for sale in pkg.get("Sales") or []:
            sale_title = sale.get("SaleText") or sale.get("MarketingTitle") or ""
            for bb in sale.get("BoardBases") or []:
                guest = bb.get("GuestRoomPrice") or {}
                sun = bb.get("SunClubRoomPrice") or {}

                web = guest.get("IlsDisplayPrice") or 0
                sun_price = sun.get("IlsDisplayPrice") or 0
                rack = rack_price(guest, web)
                savings = max(rack - web, 0)
                pct = round((savings / rack) * 100) if rack else 0

                code = bb.get("BoardBaseCode", "")
                rows.append(
                    {
                        "room_type": room_name,
                        "room_code": room_code,
                        "available_units": units,
                        "board_code": code,
                        "board": board_label(code),
                        "board_he": bb.get("BoardBaseDictionaryText", ""),
                        "sale": sale_title,
                        "non_refundable": bool(sale.get("IsNonRefundable")),
                        "rack": rack,
                        "web": web,
                        "sun_club": sun_price,
                        "savings": savings,
                        "savings_pct": pct,
                    }
                )
    return rows


def print_no_availability(raw: str, hotel_name: str):
    print(f"  {hotel_name} has no availability for these dates.")
    alts = extract_alt_dates(raw)
    if alts:
        print()
        print("  The site suggests these alternative dates:")
        for d1, d2 in alts:
            n = nights_between(d1, d2)
            print(f"    {fmt_date(d1)} to {fmt_date(d2)}  ({n} night{'s' if n != 1 else ''})")


def print_table(rows, raw, hotel_name, check_in, check_out, adults):
    nights = nights_between(check_in, check_out)
    print()
    print(
        f"{hotel_name}  |  {fmt_date(check_in)} to {fmt_date(check_out)}  |  "
        f"{nights} night{'s' if nights != 1 else ''}  |  "
        f"{adults} adult{'s' if adults != 1 else ''}"
    )
    print()

    if not rows:
        print_no_availability(raw, hotel_name)
        print()
        return

    rows.sort(key=lambda x: x["web"])

    w_room = max(max(len(r["room_type"]) for r in rows), 9)
    w_board = max(max(len(r["board"]) for r in rows), 10)

    header = (
        f"  {'ROOM TYPE':<{w_room}}  {'BOARD':<{w_board}}  "
        f"{'WEB PRICE':>11}  {'SUN CLUB':>10}  {'SAVINGS':>16}"
    )
    print(header)
    print("  " + "-" * (len(header) - 2))

    for r in rows:
        savings_str = f"{r['savings']:,.0f} ILS ({r['savings_pct']}%)"
        print(
            f"  {r['room_type']:<{w_room}}  {r['board']:<{w_board}}  "
            f"{r['web']:>11,.0f}  {r['sun_club']:>10,.0f}  {savings_str:>16}"
        )
    print()
    print("  Prices are in ILS for the whole stay, not per night.")
    print("  Confirm on isrotel.co.il before booking.")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Parse Isrotel booking API HTML into a sorted price table."
    )
    parser.add_argument("--hotel-name", default="Isrotel Hotel", help="Label for the output header")
    parser.add_argument("--check-in", required=True, help="Check-in date, YYYY-MM-DD")
    parser.add_argument("--check-out", required=True, help="Check-out date, YYYY-MM-DD")
    parser.add_argument("--adults", type=int, default=2, help="Number of adults (default 2)")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a table")
    args = parser.parse_args()

    for field in ("check_in", "check_out"):
        try:
            date.fromisoformat(getattr(args, field))
        except ValueError:
            parser.error(f"--{field.replace('_', '-')} must be in YYYY-MM-DD format")
    if nights_between(args.check_in, args.check_out) < 1:
        parser.error("--check-out must be at least one day after --check-in")

    raw = sys.stdin.read()
    if not raw.strip():
        print("  No response received from the API. Check the fetch step.", file=sys.stderr)
        sys.exit(1)

    rows = parse_packages(raw)

    if args.json:
        has_results = HAS_RESULTS_RE.search(raw)
        print(
            json.dumps(
                {
                    "hotel": args.hotel_name,
                    "check_in": args.check_in,
                    "check_out": args.check_out,
                    "nights": nights_between(args.check_in, args.check_out),
                    "adults": args.adults,
                    "has_results": bool(has_results and has_results.group(1).lower() == "true"),
                    "offers": sorted(rows, key=lambda x: x["web"]),
                    "alternative_dates": [
                        {"check_in": a, "check_out": b} for a, b in extract_alt_dates(raw)
                    ],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    print_table(rows, raw, args.hotel_name, args.check_in, args.check_out, args.adults)


if __name__ == "__main__":
    main()
