#!/usr/bin/env python3
"""
parse_html.py
Parses Isrotel HTML response (which embeds price JSON) and prints a clean table.

Usage:
    bash fetch_packages.sh --hotel-code RB --check-in 2026-08-01 --check-out 2026-08-04 \
        | python3 parse_html.py --hotel-name "Royal Beach Eilat" \
            --check-in 2026-08-01 --check-out 2026-08-04 --adults 2
"""

import sys, re, json, argparse
from datetime import date

BOARD_LABELS = {
    "WAI": "All Inclusive",
    "WHB": "Half Board",
    "WBB": "B&B",
    "AI":  "All Inclusive",
    "HB":  "Half Board",
    "BB":  "B&B",
}

def board_label(code: str) -> str:
    for suffix in ("WAI", "WHB", "WBB", "AI", "HB", "BB"):
        if code.endswith(suffix):
            return BOARD_LABELS[suffix]
    return code

def nights_between(check_in: str, check_out: str) -> int:
    d1 = date.fromisoformat(check_in)
    d2 = date.fromisoformat(check_out)
    return (d2 - d1).days

def fmt_date(iso: str) -> str:
    d = date.fromisoformat(iso)
    return d.strftime("%-d %b %Y")

def extract_packages(html: str) -> list[dict]:
    has_results = 'data-has-results=True' in html
    if not has_results:
        return []

    # Extract room titles paired with their BoardBases
    packages = []

    # Find room titles (Hebrew room names)
    room_titles = re.findall(r'"RoomTitle"\s*:\s*"([^"]+)"', html)
    board_bases_raw = re.findall(r'"BoardBases"\s*:\s*(\[(?:[^[\]]|\[(?:[^[\]]|\[[^\[\]]*\])*\])*\])', html)

    if not room_titles or not board_bases_raw:
        # Fallback: try to find prices directly
        bb_matches = re.findall(r'"BoardBases"\s*:\s*(\[.*?\])', html)
        for bb_raw in bb_matches:
            try:
                bbs = json.loads(bb_raw)
                for bb in bbs:
                    gp = bb.get("GuestRoomPrice", {})
                    sc = bb.get("SunClubRoomPrice", {})
                    rack = gp.get("IlsOperaPrice", 0)
                    web = gp.get("IlsDisplayPrice", 0)
                    sun = sc.get("IlsDisplayPrice", 0)
                    packages.append({
                        "room_type": "חדר",
                        "board": board_label(bb.get("BoardBaseCode", "")),
                        "rack": rack,
                        "web": web,
                        "sun_club": sun,
                        "savings": rack - web,
                        "savings_pct": round(((rack - web) / rack) * 100) if rack else 0,
                    })
            except json.JSONDecodeError:
                continue
        return packages

    for i, bb_raw in enumerate(board_bases_raw):
        room_title = room_titles[i] if i < len(room_titles) else f"חדר {i+1}"
        try:
            bbs = json.loads(bb_raw)
        except json.JSONDecodeError:
            continue
        for bb in bbs:
            gp = bb.get("GuestRoomPrice", {})
            sc = bb.get("SunClubRoomPrice", {})
            rack = gp.get("IlsOperaPrice", 0)
            web = gp.get("IlsDisplayPrice", 0)
            sun = sc.get("IlsDisplayPrice", 0)
            if web == 0:
                continue
            packages.append({
                "room_type": room_title,
                "board": board_label(bb.get("BoardBaseCode", "")),
                "rack": rack,
                "web": web,
                "sun_club": sun,
                "savings": rack - web,
                "savings_pct": round(((rack - web) / rack) * 100) if rack else 0,
            })

    # Deduplicate by (room_type, board, web)
    seen = set()
    unique = []
    for p in packages:
        key = (p["room_type"], p["board"], p["web"])
        if key not in seen:
            seen.add(key)
            unique.append(p)
    return unique

def print_table(packages, hotel_name, check_in, check_out, adults):
    nights = nights_between(check_in, check_out)
    print()
    print(f"🏨 {hotel_name}  |  {fmt_date(check_in)} – {fmt_date(check_out)}  |  {nights} nights  |  {adults} adults + 2 children")
    print()

    if not packages:
        print("  אין זמינות לתאריכים אלו.")
        return

    packages.sort(key=lambda x: x["web"])

    col_room = max((len(p["room_type"]) for p in packages), default=9)
    col_room = max(col_room, 9)
    col_board = max((len(p["board"]) for p in packages), default=10)
    col_board = max(col_board, 10)

    header = (
        f"  {'ROOM TYPE':<{col_room}}  "
        f"{'BOARD':<{col_board}}  "
        f"{'WEB PRICE':>11}  "
        f"{'SUN CLUB':>10}  "
        f"{'SAVINGS':>14}"
    )
    print(header)
    print("  " + "─" * (len(header) - 2))

    for p in packages:
        savings_str = f"₪{p['savings']:,.0f} ({p['savings_pct']}%)"
        print(
            f"  {p['room_type']:<{col_room}}  "
            f"{p['board']:<{col_board}}  "
            f"₪{p['web']:>9,.0f}  "
            f"₪{p['sun_club']:>8,.0f}  "
            f"{savings_str:>14}"
        )
    print()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--hotel-name", default="Isrotel Hotel")
    parser.add_argument("--check-in", required=True)
    parser.add_argument("--check-out", required=True)
    parser.add_argument("--adults", type=int, default=2)
    args = parser.parse_args()

    html = sys.stdin.read()
    packages = extract_packages(html)
    print_table(packages, args.hotel_name, args.check_in, args.check_out, args.adults)

if __name__ == "__main__":
    main()
