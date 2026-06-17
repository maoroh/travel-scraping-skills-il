# hotels-scraping-skills

A collection of [Claude Code](https://claude.ai/code) skills for fetching live pricing and availability from hotel chain booking systems — no MCP server or API key required.

> **Status:** Early stage. Currently contains one skill (Isrotel). More hotel chains coming.

---

## Available Skills

| Skill | Chain | Hotels Covered | Status |
|-------|-------|----------------|--------|
| [`isrotel-offerings`](.claude/skills/isrotel-offerings/) | [Isrotel](https://www.isrotel.co.il) | Royal Beach, Beresheet, Cramim, Goma, Alberto, Orient, Lagoona, and more | ✅ Active |

---

## Installation

**Claude Code CLI:**
```bash
claude plugin marketplace add maoroh/hotels-scraping-skills
claude plugin install isrotel-offerings@marketplace
```

**Claude Desktop:** Customize → Skills → + → `maoroh/hotels-scraping-skills` → Sync → Install

**Requirements:** `curl` and `python3` must be available in your shell.

---

## Usage

Once installed, just ask Claude naturally:

- "Find me the cheapest room at Beresheet for next weekend"
- "Check Isrotel deals in Eilat for 2 nights, 2 adults"
- "What's available at Goma Kinneret in June?"

---

## Policy & Disclaimer

> **Please read before using.**

1. **Unofficial tool** — This project is not affiliated with, endorsed by, or connected to Isrotel or any other hotel chain. Hotel names and trademarks belong to their respective owners.

2. **Personal use only** — This skill is intended for personal, non-commercial use (e.g. finding a vacation deal for yourself). Do not use it for bulk data collection, competitive intelligence, or any commercial purpose.

3. **Rate limiting** — The skill fetches data directly from hotel booking APIs. Please avoid running excessive parallel requests or automating repeated searches, to avoid placing unnecessary load on their servers.

4. **No warranty on pricing** — Prices and availability are fetched live and may differ from what you see on the hotel's website due to timing, caching, or session-specific pricing. Always confirm on the official website before booking.

5. **Terms of service** — Use of this skill may be subject to the hotel chain's website terms of service. By using this skill, you accept responsibility for ensuring your use complies with applicable terms.

---

## Contributing

Pull requests welcome — especially for adding new hotel chains. Each skill lives in its own folder under `.claude/skills/`.
