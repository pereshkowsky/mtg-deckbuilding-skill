#!/usr/bin/env python3
"""Fetch a public Moxfield collection into a CSV.

Usage:
    python fetch_moxfield_collection.py <publicCollectionId> [output.csv] [game]

- publicCollectionId: the ID from a public Moxfield collection URL
  (https://moxfield.com/collection/<THIS>)
- output.csv: default "collection.csv" in cwd
- game: MTG game id, default 1

Writes CSV columns: Quantity,Name,ManaCost,Types,CMC
Atomic write + silent when unchanged (good for a no-agent cron).
"""
import csv, hashlib, io, json, os, sys, tempfile, time
import urllib.request

PAGE_SIZE = 500
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")


def fetch_page(api, page_number, sleep=2.0):
    time.sleep(sleep)
    url = f"{api}?pageNumber={page_number}&pageSize={PAGE_SIZE}"
    req = urllib.request.Request(url, headers={
        "User-Agent": UA, "Accept": "application/json",
        "Referer": "https://moxfield.com/", "Accept-Language": "en-US,en;q=0.9"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def main():
    if len(sys.argv) < 2:
        print(__doc__); return 1
    col_id = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else "collection.csv"
    api = f"https://api2.moxfield.com/v1/collections/search/{col_id}"
    d = fetch_page(api, 1, sleep=0)
    total_pages = int(d.get("totalPages") or 1)
    all_rows, seen = [], set()
    for pn in range(1, total_pages + 1):
        d = fetch_page(api, pn)
        for e in d.get("data") or []:
            card = e.get("card") or {}
            name = card.get("name")
            if not name: continue
            key = (name, e.get("quantity", 1))
            if key in seen: continue
            seen.add(key)
            all_rows.append([e.get("quantity", 1), name,
                             card.get("mana_cost") or "",
                             card.get("type_line") or "",
                             card.get("cmc", "")])
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["Quantity", "Name", "ManaCost", "Types", "CMC"])
    for r in sorted(all_rows, key=lambda x: (x[1].lower(), str(x[0]))):
        w.writerow(r)
    new_csv = buf.getvalue()
    new_hash = hashlib.sha256(new_csv.encode("utf-8")).hexdigest()
    old_hash = ""
    if os.path.exists(out):
        old_hash = hashlib.sha256(open(out, "rb").read()).hexdigest()
    if new_hash == old_hash:
        return 0  # silent — unchanged
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(os.path.abspath(out)) or ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
            f.write(new_csv)
        os.replace(tmp, out)
    finally:
        if os.path.exists(tmp): os.remove(tmp)
    uniq = len({r[1].lower() for r in all_rows})
    print(f"collection updated: {len(all_rows)} rows, {uniq} unique cards")
    return 0


if __name__ == "__main__":
    sys.exit(main())
