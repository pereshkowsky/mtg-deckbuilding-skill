---
name: mtg-deckbuilding
description: "Build MTG 60-card decks constrained to a real card collection (Moxfield/Archidekt). Use for deckbuilding from owned cards, excluding cards used in other decks."
version: 1.0.0
author: pereshkowsky
license: MIT
metadata:
  hermes:
    tags: [mtg, tcg, deckbuilding, moxfield, archidekt, scryfall]
---

# MTG Deckbuilding (collection-constrained)

Build/suggest Magic: The Gathering decks **constrained to a real card collection** — a
player's owned cards, not the whole card pool. Written for a player who keeps their
collection + decks on **Moxfield** (or Archidekt). Viability is the goal, not top-tier meta.

This skill works as a **Claude Code skill** and a **Hermes skill** (both read SKILL.md).

## When to Use

- Build a 60-card deck from a specific owned collection.
- Pull a user's deck or collection from Moxfield/Archidekt.
- Exclude cards already used in the user's other decks from a new build.
- Write a decklist the Obsidian `mtg-decklist` plugin can render (for vault workflows).

## Golden rule: don't read the whole collection into context

A 4k-card collection is DATA, not LLM text. Never feed all of it to the model.

1. Dump the collection to a CSV with a script (0 tokens).
2. When building, a script filters the collection by color/CMC/type so only a candidate
   pool (~a few hundred cards) enters context — NOT all of it.
3. Recompute the CSV when the collection changes (on request or a cron).

Cost therefore scales with number of build iterations, not collection size.

## Honest bar

Produced decks are **solid/mid-tier, not pro-meta**. Say so — don't oversell. The goal is a
coherent, legal deck built from what the player actually owns, not a tournament top-8 list.

## Data sources (verified working — no auth)

### Collection (public Moxfield)
```
GET https://api2.moxfield.com/v1/collections/search/{publicId}?pageNumber=N&pageSize=500
headers: User-Agent (browser), Accept: application/json, Referer: https://moxfield.com/
```
- Pagination param is **`pageNumber`** (NOT page/offset). pageSize up to 500.
- Response `data: [{quantity, card: {name, mana_cost, cmc, type_line, colors, ...}}]` —
  cmc/types/colors come directly, no Scryfall enrichment needed.
- **Cloudflare is flaky, not impossible:** a first request returns JSON, rapid repeats get
  blocked. Send browser UA + Referer, ~2s sleep between requests. Probe page 1 (sleep 0)
  first to learn totalPages.
- Script: `scripts/fetch_moxfield_collection.py` → `collection.csv`.

### Decks (public Moxfield)
```
GET https://api2.moxfield.com/v3/decks/all/{publicId}
```
- Boards keyed by card id: `boards.mainboard.cards = {cardId: {quantity, card: {...}}}`
  (cards is a DICT, not a list). Collect names from mainboard+sideboard+commanders.
- Script `scripts/fetch_decks.py` writes per-deck JSON + a combined `used_cards.json`
  (all unique card names across the user's decks) — drives the "don't reuse cards" rule.

### Archidekt (alternative)
- Deck: `GET https://archidekt.com/api/decks/{id}/` — open, full cards+JSON.
- Collection export (public): `POST /api/collection/export/v2/{user_id}/` with
  `{"fields":["quantity","card__oracleCard__name","card__manaCost","card__types","card__cmc"],"page":1,"game":1,"pageSize":2500}` → CSV content. Paged.

### Card data (optional, Scryfall)
`https://api.scryfall.com/` — oracle text, legality, printings, art. Free, reliable,
not heavily rate-limited. Use for P/T/types if a source doesn't provide them.

## How to build a "decent" deck

Engineering task, not a genius guess:

1. **Rules are fixed** — encode hard (60 cards, 15 sideboard, max 4 copies of a non-basic,
   format bans, color identity).
2. **Choose ONE archetype** — never mix two strategies in one deck. The user's earlier
   mistake: putting prowess creatures (which want cheap spells) next to lifegain creatures
   (which want lifegain triggers) made BOTH weaker. Pick one coherent plan.
3. **Synergy must be REAL, not nominal** — check the actual trigger chain (e.g. Soul Warden
   + Ajani's Pridemate + lifelink creatures; or burn spells + prowess creatures). If the
   archetype's key enablers are missing from the available pool, honestly switch archetype.
4. **Check availability per card** — sum all collection rows for a card; cap at 4 copies;
   never include a card beyond what's owned.
5. **Balance** — 60 cards ≈ 24 creatures + 14 spells + 22 lands (tune per archetype).
6. **Exclude used cards** — remove any card already in the user's other decks.
7. **Write result** in a mtg-decklist-renderable block so Obsidian renders it:

```decklist
# Creatures
4 Healer's Hawk
...
# Spells
...
# Lands
22 Mountain
```

## The dungnotnull engine (optional accelerator)

`github.com/dungnotnull/tcg-ccg-deck-building-optimization-agent-skill` — pure-Python deck
builder, MIT, no Docker/Redis. Drive via terminal:
```
python tools/deck_cli.py build pool.json --archetype aggro --land-budget 22 --max-copies 4 --deck-size 60
```
pool.json = `{"cards":[{name,cmc,power,toughness,types[],tags[],text}]}`.

**CRITICAL — two hard lessons learned:**
1. **The engine optimizes within the GIVEN pool; it does NOT filter by archetype.** In a
   tiny pool it will happily put a CMC-12 creature into "aggro". YOU must filter/size the
   pool by archetype BEFORE feeding it. That's the division of labor: agent picks archetype
   + filters pool; engine answers "given this pool, what's optimal".
2. **The engine does NOT scale to large pools.** Its local-search is
   O(iter × deck × pool × deck). On a ~700-card pool it hangs (no timeout, >160s per iter).
   It works in seconds ONLY on small pools (~10-40 cards). So: filter the collection to a
   small archetype pool (~30 cards), run the engine on THAT, then critically review.
   Do NOT run it on the full collection.

## Workflow: pull → filter → build → record

1. Get the collection/deck IDs from the user.
2. Run `scripts/fetch_moxfield_collection.py` (and `fetch_decks.py` for used-cards) to
   produce `collection.csv` + `used_cards.json`.
3. Pick archetype (see Building pipeline). If user has no preference, choose the one with
   the most synergy in the available pool — check enablers exist.
4. Filter the available pool; build the deck (script or the engine on a small pool).
5. Cross-check every card qty ≤ available and ≤ 4 copies.
6. Write the decklist in the mtg-decklist block; report total = 60.
7. Optionally, review against the mana curve + synergy, iterate once if clearly broken.

## Pitfalls

- Moxfield/Archidekt collections are PRIVATE by default. The public `{publicId}` route
  avoids auth — the user must share a public collection link/ID.
- Moxfield's API returns 401/403 for wrong endpoints. Use the `{publicId}` route; don't
  hammer curl expecting success on `/api/moxfield.com/v2/cards/search/collection`.
- Cloudflare blocks rapid curl bursts — pace requests.
- Basic lands (Plains/Swamp/Mountain...) have no 4-copy limit; exclude them from the
  max-4 rule. The collection may list hundreds of basics — use them freely.
- A card may appear in several rows (different sets) — sum quantities by name.
- Don't claim a deck is "synergy-rich" without checking the actual trigger chain exists in
  the available pool. One or two enablers alone do not make a strategy.

## Files

- `SKILL.md` — this.
- `scripts/fetch_moxfield_collection.py` — pull collection → CSV (atomic, silent if unchanged).
- `scripts/fetch_decks.py` — pull decks → JSON + `used_cards.json`.
- `references/moxfield-collection-deck-api.md` — endpoint details, Cloudflare reality.
- `references/dungnotnull-engine.md` — engine behavior + integration notes.
