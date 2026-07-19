# Isrotel Hotel Directory

Maps hotel names to the codes used by the booking API. Consult when the user
names a hotel or a city and you need the `hotel_code` for a request, or when
building a multi-hotel search for a whole region.

Verified against isrotel.co.il, July 2026.

## Eilat

| Code | Name | Hebrew |
|------|------|--------|
| `RB` | Royal Beach Eilat | רויאל ביץ' אילת |
| `KS` | King Solomon Eilat | מלך שלמה אילת |
| `RG` | Royal Garden Eilat | רויאל גארדן אילת |
| `AG` | Agamim Eilat | אגמים אילת |
| `AM` | Yam Suf Eilat | ים סוף אילת |
| `SP` | Sport Club Eilat All Inclusive | ספורט קלאב אילת |
| `LG` | Lagoona Eilat All Inclusive | לגונה אילת |
| `RC` | Riviera Eilat | ריביירה אילת |

## Dead Sea

| Code | Name | Hebrew |
|------|------|--------|
| `DS` | Nebo | נבו |
| `GA` | Noga | נוגה |

## Mitzpe Ramon and the Negev

| Code | Name | Hebrew |
|------|------|--------|
| `BR` | Beresheet | בראשית |
| `RI` | Daroma (formerly Ramon Inn) | דרומה |
| `KD` | Kedma | קדמה |

## Jerusalem

| Code | Name | Hebrew |
|------|------|--------|
| `CR` | Cramim | כרמים |
| `OR` | Orient | אוריינט |

## Tel Aviv and Herzliya

| Code | Name | Hebrew |
|------|------|--------|
| `RT` | Royal Beach Tel Aviv | רויאל ביץ' תל אביב |
| `TT` | Sea Tower Tel Aviv | סי טאואר תל אביב |
| `PT` | Port Tower Tel Aviv | פורט טאואר תל אביב |
| `AL` | Alberto Tel Aviv | אלברטו תל אביב |
| `TLVTX` | Gymnasya Tel Aviv | גימנסיה תל אביב |
| `TLVAK` | Publica Herzliya | פובליקה הרצליה |

## North and Kinneret

| Code | Name | Hebrew |
|------|------|--------|
| `AY` | Ayla | איילה |
| `MH` | Mizpe Hayamim | מצפה הימים |
| `YM` | Goma Kinneret | גומא כנרת |
| `CF` | Carmel Forest Estate | יערות הכרמל |

## Brand Segments

Isrotel splits its properties into three brand tiers. Use these when the user
asks for "luxury Isrotel" or "the cheap Isrotel hotels".

| Segment | Codes | Character |
|---------|-------|-----------|
| exclusive | RB, BR, CR, OR, RT, MH, CF | Top tier, highest rack rates |
| collection | KS, RG, AG, AM, SP, LG, RC, DS, GA, RI, KD, AY, YM | Mainstream family and resort |
| design | TT, PT, AL, TLVTX, TLVAK | Urban boutique, Tel Aviv focused |

## Region Groupings for Multi-Hotel Search

Paste these directly into `fetch_all.sh --codes`.

| Region | Codes |
|--------|-------|
| Eilat | `RB KS RG AG AM SP LG RC` |
| Dead Sea | `DS GA` |
| Negev | `BR RI KD` |
| Jerusalem | `CR OR` |
| Tel Aviv | `RT TT PT AL TLVTX TLVAK` |
| North | `AY MH YM CF` |

## Naming Gotchas

- "Royal Beach" is ambiguous: `RB` is Eilat, `RT` is Tel Aviv. Ask which one.
- Daroma (`RI`) was renamed from Ramon Inn. Users may still say "Ramon Inn".
- Sport Club (`SP`) and Lagoona (`LG`) are the only all-inclusive properties,
  so a request for "all inclusive Isrotel" narrows to those two.
- Yam Suf (`AM`) is sometimes written "Yam Suf" or "Ambassador", its former name.
