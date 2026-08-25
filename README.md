# MTG Deckbuilding (collection-constrained) — Claude Code / Hermes skill

Build **60-card Magic decks constrained to a real card collection** — your owned cards,
not the whole card pool. Keeps your collection + decks on **Moxfield** (or Archidekt),
excludes cards already used in your other decks, and writes results the Obsidian
`mtg-decklist` plugin can render.

This is a **SKILL.md** package: drop it into **Claude Code** (`~/.claude/skills/` or a
project's `.claude/skills/`) or **Hermes** (`~/AppData/Local/hermes/skills/`), and the
agent learns the workflow. It ships helper scripts in `scripts/` that talk to Moxfield's
public API (no auth — you just share a public collection/deck link).

## What it does

- Pull a **public Moxfield collection** → `collection.csv` (cmc/types/colors included).
- Pull your **public Moxfield decks** → per-deck JSON + a combined `used_cards.json`
  (all unique card names across your decks).
- Build a 60-card deck from the **available remainder** — cards not used in your other
  decks, max 4 copies, one coherent archetype, real (not nominal) synergy.
- Optionally accelerate the numeric pass with the **dungnotnull deck engine** (the skill
  documents the two hard lessons: it does not filter by archetype, and it hangs on large
  pools — you must feed it a small filtered pool).

## Install in Claude Code

```bash
# 1. clone somewhere
git clone https://github.com/pereshkowsky/mtg-deckbuilding-skill.git
# 2. put the skill where Claude Code sees it
#    (project-scoped or global — either works)
mkdir -p ~/.claude/skills && cp -r mtg-deckbuilding-skill ~/.claude/skills/mtg-deckbuilding
```

Then in Claude Code just say e.g.:

> Build me a mono-red aggro deck from my collection, but don't use cards from my other decks.

## Requirements

- Python 3 (for the scripts). No other dependencies.
- A **public** Moxfield collection (Settings → collection → make public), and public decks
  if you want the "don't reuse cards" rule.
- Optional: the `dungnotnull` engine repo (see `references/dungnotnull-engine.md`) for
  numeric draft/metrics.

## Files

- `SKILL.md` — the skill definition + workflow.
- `scripts/fetch_moxfield_collection.py <publicId>` — collection → CSV (atomic, silent if unchanged).
- `scripts/fetch_decks.py <outDir> <deckId>...` — decks → JSON + `used_cards.json`.
- `scripts/filter_pool.py` — shrink a collection to a small archetype pool for the engine.
- `scripts/build_deck.py` — verify a drafted deck against the collection + emit a decklist.
- `references/moxfield-archidekt-api.md`, `references/dungnotnull-engine.md`.

## License

MIT.
