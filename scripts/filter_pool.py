#!/usr/bin/env python3
"""Filter an owned collection into a small candidate pool for the dungnotnull engine.

The engine works in seconds ONLY on small pools (~10-40 cards) — it does NOT scale to a
full collection (its local-search hangs on ~700 cards). This script shrinks the collection
to an archetype-constrained pool the engine can actually run on.

Usage:
    python filter_pool.py collection.csv used_cards.json pool.json <colorTag> [--maxcmc 5]

- collection.csv: columns Quantity,Name,ManaCost,Types,CMC
- used_cards.json: list of card names already used in other decks (excluded)
- pool.json: output, {"cards":[{name,cmc,power,toughness,types[],tags[],text}]}
- colorTag: comma colors e.g. "R" or "W,B" (cards whose color identity ⊆ this set)
- --maxcmc: exclude cards above this CMC (default 5)
"""
import csv, json, os, sys

LAND_TYPES = {"land", "basic"}


def cmc(r):
    try:
        return int(float(r["CMC"]))
    except Exception:
        return 0


def colors_of(mc):
    return {c for c in "WUBRG" if ("{" + c) in mc or (c + "}") in mc}


def power_toughness(r):
    t = (r.get("Types") or "")
    if "Creature" in t:
        # Moxfield/Archidekt export may not carry P/T; engine defaults 1/1 are fine.
        return 1, 1
    return 0, 0


def main():
    if len(sys.argv) < 5:
        print(__doc__); return 1
    collection, used_path, out, color_tag = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
    maxcmc = 5
    for a in sys.argv[5:]:
        if a.startswith("--maxcmc"):
            try: maxcmc = int(a.split("=")[1])
            except Exception: pass
    allowed = set(color_tag.upper())
    used = {u.lower() for u in json.load(open(used_path, encoding="utf-8"))} if os.path.exists(used_path) else set()
    rows = [r for r in csv.DictReader(open(collection, encoding="utf-8"))
            if r["Name"].lower() not in used]

    pool = {}
    for r in rows:
        t = r.get("Types") or ""
        if any(lt in t for lt in LAND_TYPES):
            continue  # basics handled separately by the engine's land budget
        c = colors_of(r.get("ManaCost") or "")
        if not c or not c.issubset(allowed):
            continue
        mv = cmc(r)
        if mv > maxcmc:
            continue
        pw, tu = power_toughness(r)
        pool[r["Name"]] = {
            "name": r["Name"], "cmc": mv, "power": pw, "toughness": tu,
            "types": [x.strip() for x in t.replace("—", "-").replace(" & ", " ").split()],
            "tags": [x.lower() for x in t.split()],
            "text": r.get("ManaCost") or "",
        }
    json.dump({"cards": list(pool.values())}, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"pool: {len(pool)} unique cards (colors={allowed}, cmc<= {maxcmc}) → {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
