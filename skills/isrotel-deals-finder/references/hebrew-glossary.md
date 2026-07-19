# Hebrew Hotel Booking Glossary

Terminology for interpreting Hebrew user requests and Hebrew API responses.
Consult when the user writes in Hebrew or transliterated Hebrew, or when you
need to translate a room type or board basis returned by the API.

## Booking Terms

| Hebrew | Transliteration | English |
|--------|-----------------|---------|
| מלון | malon | hotel |
| בית מלון | beit malon | hotel (formal) |
| חדר | cheder | room |
| חדרים פנויים | chadarim pnuyim | available rooms |
| הזמנה | hazmana | reservation |
| לילה | layla | night |
| לילות | leylot | nights |
| כניסה | knisa | check-in |
| יציאה | yetzia | check-out |
| תפוסה | tfusa | occupancy |
| מבצע | mivtza | deal, promotion |
| הנחה | hanacha | discount |
| מחיר | mechir | price |
| חופשה | chufsha | vacation |
| סוף שבוע | sof shavua | weekend |
| חג | chag | holiday |

## Guest Types

| Hebrew | Transliteration | English |
|--------|-----------------|---------|
| מבוגר | mevugar | adult |
| מבוגרים | mevugarim | adults |
| ילד | yeled | child (2 to 12) |
| ילדים | yeladim | children |
| תינוק | tinok | infant (under 2) |
| זוג | zug | couple |
| משפחה | mishpacha | family |

## Board Basis

| Hebrew | Transliteration | English |
|--------|-----------------|---------|
| לינה בלבד | lina bilvad | room only |
| לינה וארוחת בוקר | lina ve-aruchat boker | bed and breakfast |
| חצי פנסיון | chatzi pension | half board |
| פנסיון מלא | pension male | full board |
| הכל כלול | ha-kol kalul | all inclusive |

## Room Types

These appear as the `title` field in API responses.

| Hebrew | Transliteration | English |
|--------|-----------------|---------|
| חדר זוגי | cheder zugi | double room |
| חדר משפחה | cheder mishpacha | family room |
| חדר דלוקס | cheder deluxe | deluxe room |
| סוויטה | suita | suite |
| סוויטת יוקרה | suitat yukra | luxury suite |
| חדר נשיאותי | cheder nesiuti | presidential room |
| נוף לים | nof la-yam | sea view |
| נוף לבריכה | nof la-bricha | pool view |
| נוף לגן | nof la-gan | garden view |
| מרפסת | mirpeset | balcony |
| בריכה פרטית | bricha pratit | private pool |

## Isrotel Specific

| Hebrew | Transliteration | English |
|--------|-----------------|---------|
| ישרוטל | Isrotel | Isrotel |
| מועדון חוג השמש | moadon chug ha-shemesh | Sun Club, the Isrotel loyalty programme |
| חבר מועדון | chaver moadon | club member |
| מחיר מחירון | mechir mechiron | rack rate |
| הנחת אתר | hanachat atar | website discount |

"Sun Club" is branded in Hebrew as **מועדון חוג השמש**. Use that form in Hebrew
output rather than transliterating "סאן קלאב". The API field names stay English
(`SunClubRoomPrice`).

Note that the booking API's own tooltip text drops the definite article and
reads "חברי מועדון חוג שמש נהנים מהנחה מיוחדת". Treat that as site copy, not as
the brand name, and do not copy it verbatim into output.

## Common Request Phrasings

Recognise these as triggers for this skill.

- "תמצא לי מלון בישרוטל" (find me an Isrotel hotel)
- "כמה עולה בראשית לסופ״ש" (how much is Beresheet for a weekend)
- "חדרים פנויים באילת" (available rooms in Eilat)
- "mivtzaim be-Isrotel" (Isrotel promotions)
- "chufsha be-Eilat le-zug" (Eilat vacation for a couple)
- "ha-malon ha-zol be-yoter shel Isrotel" (the cheapest Isrotel hotel)

## Date Handling Note

Israeli users often say "sof shavua" (weekend) meaning Thursday or Friday
check-in through Saturday check-out, not the Friday to Sunday pattern common
elsewhere. When a user says "this weekend" without dates, assume Friday
check-in and Saturday check-out, and state the assumption so they can correct it.
