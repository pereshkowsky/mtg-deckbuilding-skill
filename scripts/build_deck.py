#!/usr/bin/env python3
"""Assemble a 60-card deck from an owned collection, constrained by archetype.

This is a TEMPLATE/helper. The real archetype choice + card selection must be done by the
agent (LLM) against the actual collection — see SKILL.md. This script takes an explicit
draft (name -> copies) the agent has already chosen, verifies it against collection.csv +
used_cards.json, balances to 60, and emits a mtg-decklist block.

Usage:
    python build_deck.py collection.csv used_cards.json out.md <colorTag> [--draft "Name:4,Other:3"] ...
"""
import csv, json, os, re, sys


def load_avail(collection_path):
    rows = list(csv.DictReader(open(collection_path, encoding="utf-8")))
    avail = {}
    for r in rows:
        n = r["Name"].lower()
        avail[n] = avail.get(n, 0) + int(r["Quantity"] or 1)
    return avail


def load_used(used_path):
    if not os.path.exists(used_path):
        return set()
    return {u.lower() for u in json.load(open(used_path, encoding="utf-8"))}


def verify(avail, used, draft):
    """Return (deck, problems). deck = name->copies after clamping to avail/4. """
    deck, problems = {}, []
    for name, c in draft.items():
        key = name.lower()
        if key in used:
            problems.append(f"USED elsewhere: {name}"); continue
        a = avail.get(key, 0)
        if a == 0:
            problems.append(f"NOT OWNED: {name}"); continue
        deck[name] = min(c, a, 4)
        if c > 4:
            problems.append(f"cap 4: {name}")
    return deck, problems


def emit_block(nonland, lands, creatures=None, spells=None):
    if creatures is None or spells is None:
        # split by available type info — caller should pass lists
        creatures, spells = nonland, {}
    L = ["```decklist", "# Creatures"]
    for nm in sorted(creatures, key=lambda x: -creatures[x]):
        L.append(f"{creatures[nm]} {nm}")
    if spells:
        L.append("")
        L.append("# Spells")
        for nm in sorted(spells, key=lambda x: -spells[x]):
            L.append(f"{spells[nm]} {nm}")
    L.append("")
    L.append("# Lands")
    for nm, q in lands.items():
        L.append(f"{q} {nm}")
    L.append("```")
    return "\n".join(L)


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print(__doc__); sys.exit(1)
    collection, used, out = sys.argv[1], sys.argv[2], sys.argv[3]
    avail = load_avail(collection)
    used_set = load_used(used)
    # The draft is passed as --draft "Name:4,..."; the agent supplies it.
    # If absent, print guidance. (The real drafting is an LLM task.)
    print("agent: supply the draft via --draft 'Name:4,Name2:3' to assemble. Available colors/archetype:")
    # quick archetype scan helper
    rows = list(csv.DictReader(open(collection, encoding="utf-8")))
    print(f"collection cards: {len(rows)} rows, {len(avail)} unique, used-set {len(used_set)}")
