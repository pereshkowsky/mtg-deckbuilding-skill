#!/usr/bin/env python3
"""Fetch public Moxfield decks into JSON snapshots + a combined used-cards set.

Usage:
    python fetch_decks.py <outputDir> <publicDeckId1> [publicDeckId2 ...]

Writes, per deck: <outputDir>/<deckSlug>.json (full snapshot) and .used.json (card->qty).
Writes <outputDir>/../used_cards.json (all unique card names across all decks).
Used-cards list drives the "don't reuse cards from other decks" rule.
"""
import json, os, re, sys, time
import urllib.request

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")


def fetch_deck(public_id, sleep=2.0):
    time.sleep(sleep)
    url = f"https://api2.moxfield.com/v3/decks/all/{public_id}"
    req = urllib.request.Request(url, headers={
        "User-Agent": UA, "Accept": "application/json",
        "Referer": "https://moxfield.com/", "Accept-Language": "en-US,en;q=0.9"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def extract_used(d):
    used = {}
    for bn in ("mainboard", "sideboard", "commanders"):
        b = (d.get("boards") or {}).get(bn) or {}
        for e in (b.get("cards") or {}).values():
            c = e.get("card") or {}
            name = c.get("name")
            if not name: continue
            used[name] = used.get(name, 0) + (e.get("quantity") or 1)
    return used


def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def main():
    if len(sys.argv) < 3:
        print(__doc__); return 1
    out_dir = sys.argv[1]
    ids = sys.argv[2:]
    os.makedirs(out_dir, exist_ok=True)
    all_used, reports = {}, []
    for pid in ids:
        try:
            d = fetch_deck(pid)
        except Exception as ex:
            reports.append(f"{pid}: ERROR {ex}"); continue
        name = d.get("name") or pid
        used = extract_used(d)
        all_used.update(used)
        slug = slugify(name) or pid
        with open(os.path.join(out_dir, f"{slug}.json"), "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=1)
        with open(os.path.join(out_dir, f"{slug}.used.json"), "w", encoding="utf-8") as f:
            json.dump({k: used[k] for k in sorted(used)}, f, ensure_ascii=False, indent=1)
        reports.append(f"{slug} ({name}): {len(used)} unique cards used")
    with open(os.path.join(out_dir, "..", "used_cards.json"), "w", encoding="utf-8") as f:
        json.dump({k: all_used[k] for k in sorted(all_used)}, f, ensure_ascii=False, indent=1)
    print("; ".join(reports))
    print(f"total used unique: {len(all_used)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
