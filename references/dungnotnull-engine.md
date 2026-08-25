# dungnotnull/tcg-ccg-deck-building-optimization — engine notes

Repo: `https://github.com/dungnotnull/tcg-ccg-deck-building-optimization-agent-skill`
License: MIT. A pure-Python deck-building engine for MTG (also handles Hearthstone/YGO).

## Why it's optional
The engine is a **constraint optimizer**, not an autonomous deckbuilder. The agent (LLM)
does the real work: pick archetype, filter the pool, critically review. Use the engine only
as a fast numeric draft + metrics helper. See SKILL.md for the two hard lessons.

## Install / run
```
cd repo
python -m pip install -e .       # or run tools/deck_cli.py directly from the repo
python tools/deck_cli.py build pool.json --archetype aggro --land-budget 22 --max-copies 4 --deck-size 60
```
Deps: requests, feedparser, python-dateutil (crawl4ai optional; not needed for build).

## CLI
```
build <pool.json>        build optimized deck from a card-pool JSON
analyze <deck.json>      analyze a deck + print report
consistency <deck.json>  land-drop + mulligan math
demo --archetype aggro|control
```
`build` flags: --deck-size, --sideboard-size, --max-copies, --land-budget, --archetype,
--must-include, --banned, --iter.

## Card model (pool.json)
`{"cards":[{name,cmc,power,toughness,types[],tags[],text}]}`
`types`: "land","creature","instant","sorcery","enchantment",...
`tags` drive synergy/archetype scoring.

## Verified behavior + the two critical lessons
1. **The engine optimizes within the GIVEN pool — it does NOT filter by archetype.**
   In a tiny pool it will happily put a CMC-12 creature into "aggro" if nothing better
   exists. YOU must filter/size the pool by archetype BEFORE feeding it. Division of
   labor: agent picks archetype + filters pool; engine answers "given this pool, optimal".
2. **The engine does NOT scale to large pools.** Its local-search is
   O(iter × deck × pool × deck). On a ~700-card pool it hangs (>160s, no timeout).
   It runs in seconds ONLY on small pools (~10-40 cards). So filter the collection to a
   small archetype pool (~30 cards) with `scripts/filter_pool.py`, run the engine on that,
   then critically review. Do NOT run it on the full collection.

## Integration
`scripts/filter_pool.py` shrinks a collection CSV to a small archetype-constrained pool
the engine can run on. Feed the output pool.json to `deck_cli.py build`.
