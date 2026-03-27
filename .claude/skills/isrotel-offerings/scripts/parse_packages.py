#!/usr/bin/env python3
"""
parse_packages.py
Reads raw Isrotel API output (newline-delimited JSON) from stdin and prints
a clean, sorted table of room offers.

Usage:
    bash fetch_packages.sh --hotel-code RB --check-in 2026-04-10 --check-out 2026-04-12 | \
        python3 parse_packages.py --hotel-name "Royal Beach Eilat" --check-in 2026-04-10 --check-out 2026-04-12 --adults 2
"""

import sys
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

def board_label(code: str) -> str:
    # Codes look like "INT25WBB" — take the last 2-3 chars
    for suffix in ("WAI", "WHB", "WBB", "AI", "HB", "BB"):
        if code.endswith(suffix):
            return BOARD_BASE_LABELS[suffix]
    return code

def nights_between(check_in: str, check_out: str) -> int:
    d1 = date.fromisoformat(check_in)
    d2 = date.fromisoformat(check_out)
    return (d2 - d1).days

def fmt_date(iso: str) -> str:
    d = date.fromisoformat(iso)
    return d.strftime("%-d %b %Y")

def parse_packages(raw: str) -> list[dict]:
    packages = []
    for line in raw.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        for pkg in obj.get("packages", []):
            room_type = pkg.get("title", "")
            for sale in pkg.get("sales", []):
                sale_title = sale.get("sale_title", "")
                for bb in sale.get("board_bases", []):
                    gp = bb.get("GuestRoomPrice", {})
                    sc = bb.get("SunClubRoomPrice", {})
                    rack = gp.get("IlsOperaPrice", 0)
                    web  = gp.get("IlsDisplayPrice", 0)
                    sun  = sc.get("IlsDisplayPrice", 0)
                    savings = rack - web
                    pct = round((savings / rack) * 100) if rack else 0
                    packages.append({
                        "room_type":  room_type,
                        "board_code": bb.get("BoardBaseCode", ""),
                        "board":      board_label(bb.get("BoardBaseCode", "")),
                        "sale":       sale_title,
                        "rack":       rack,
                        "web":        web,
                        "sun_club":   sun,
                        "savings":    savings,
                        "savings_pct": pct,
                    })
    return packages

def print_table(packages: list[dict], hotel_name: str, check_in: str, check_out: str, adults: int):
    nights = nights_between(check_in, check_out)
    header = f"🏨 {hotel_name}  |  {fmt_date(check_in)} – {fmt_date(check_out)}  |  {nights} night{'s' if nights != 1 else ''}  |  {adults} adult{'s' if adults != 1 else ''}"
    print()
    print(header)
    print()

    if not packages:
        print("  No availability for these dates.")
        return

    # Sort cheapest first
    packages.sort(key=lambda x: x["web"])

    col = {
        "room":  max(len(p["room_type"]) for p in packages),
        "board": max(len(p["board"]) for p in packages),
    }
    col["room"]  = max(col["room"],  9)   # min width "ROOM TYPE"
    col["board"] = max(col["board"], 10)  # min width "BOARD BASE"

    header_row = (
        f"  {'ROOM TYPE':<{col['room']}}  "
        f"{'BOARD':<{col['board']}}  "
        f"{'WEB PRICE':>11}  "
        f"{'SUN CLUB':>10}  "
        f"{'SAVINGS':>14}"
    )
    divider = "  " + "─" * (len(header_row) - 2)

    print(header_row)
    print(divider)

    for p in packages:
        savings_str = f"₪{p['savings']:,.0f} ({p['savings_pct']}%)"
        print(
            f"  {p['room_type']:<{col['room']}}  "
            f"{p['board']:<{col['board']}}  "
            f"₪{p['web']:>9,.0f}  "
            f"₪{p['sun_club']:>8,.0f}  "
            f"{savings_str:>14}"
        )
    print()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--hotel-name", default="Isrotel Hotel")
    parser.add_argument("--check-in",   required=True)
    parser.add_argument("--check-out",  required=True)
    parser.add_argument("--adults",     type=int, default=2)
    args = parser.parse_args()

    raw = sys.stdin.read()
    packages = parse_packages(raw)
    print_table(packages, args.hotel_name, args.check_in, args.check_out, args.adults)

if __name__ == "__main__":
    main()
