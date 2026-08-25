# Moxfield / Archidekt API — verified working endpoints (no auth for public data)

Base: `https://api2.moxfield.com`

## Collection (public)
```
GET /v1/collections/search/{publicId}?pageNumber=N&pageSize=500
headers: User-Agent (browser), Accept: application/json, Referer: https://moxfield.com/
```
- Pagination param is **`pageNumber`** (NOT `page`/`offset`). pageSize up to 500.
- Response: `{totalResults, totalPages, pageNumber, pageSize, data: [{quantity,
  card: {name, mana_cost, cmc, type_line, colors, color_identity, oracle_text}}]}`
- Gives cmc/types/colors directly — no Scryfall enrichment needed.
- Script: `scripts/fetch_moxfield_collection.py <publicId> [out.csv]`.

## Decks (public)
```
GET /v3/decks/all/{publicId}
```
- Returns `{name, format, visibility, boards: {mainboard, sideboard, maybeboard,
  commanders, ...}}`.
- Each board: `{count, cards: {cardId: {quantity, finish, card: {...}}}}` — cards is a
  **DICT keyed by card id**, not a list.
- Used-card names: iterate mainboard+sideboard+commanders, collect
  `entry['card']['name'] × entry['quantity']`.
- Script: `scripts/fetch_decks.py <outDir> <publicId>...` writes per-deck JSON +
  combined `used_cards.json`.

## Cloudflare reality (IMPORTANT)
- **curl IS flaky, not impossible.** A first request in a burst returns JSON; rapid
  repeats within ~seconds get a 403/"blocked" HTML. Mitigate:
  - browser User-Agent + `Accept: application/json` + `Referer: https://moxfield.com/`
    + `Accept-Language: en-US,en;q=0.9`
  - ~2s sleep between requests (the scripts do this).
  - Probe page 1 (sleep 0) first to learn totalPages.
- 401 on `/v1/collections/search` or `/v2/cards/search/collection` = wrong endpoint or
  needs auth. Use the public `{publicId}` route to avoid auth entirely.
- 404 on `/v3/decks/{id}` = use `/v3/decks/all/{id}` (the `all/` variant is the public
  read path).

## Archidekt (alternative source)
- Deck: `GET https://archidekt.com/api/decks/{id}/` — open, full cards+JSON.
- Collection export (public): `POST /api/collection/export/v2/{user_id}/` with
  `{"fields":["quantity","card__oracleCard__name","card__manaCost","card__types","card__cmc"],"page":1,"game":1,"pageSize":2500}` → CSV `content`, `totalRows`, `moreContent`. Paged.

## Scryfall (card data, free)
`https://api.scryfall.com/` — oracle text, legality, printings, art. Use for P/T/types
if a source doesn't give them. Free, not heavily rate-limited.
