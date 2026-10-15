#!/usr/bin/env python3
"""
Find near-duplicate prose between pages.

Pages were written by independent writers working on related codes, which is exactly where
boilerplate creeps in: two suds codes on the same platform, a code and its renamed twin, a
hub and the page it links to. Google treats that as thin content and it is invisible to the
schema validator, so it gets measured here.

Compares shingled word sequences, which catches reworded duplication that an exact-sentence
match would miss.
"""
import json, glob, pathlib, re, sys, itertools, collections

SHINGLE = 8          # consecutive words; long enough that common phrasing does not match
REPORT_AT = 0.12     # fraction of shared shingles worth a look
FAIL_AT = 0.30       # fraction that means one page was written from the other

FIELDS = ["answer", "still_showing", "when_to_call", "reset_procedure", "model_notes"]

def prose(d):
    parts = [d.get(f) or "" for f in FIELDS]
    parts += [c.get("cause","") + " " + c.get("confirm","") for c in d.get("causes", [])]
    parts += [s.get("name","") + " " + s.get("detail","") for s in d.get("steps", [])]
    parts += [f.get("q","") + " " + f.get("a","") for f in d.get("faqs", [])]
    return re.sub(r"[^a-z0-9 ]", " ", " ".join(parts).lower())

def shingles(text):
    w = text.split()
    return {" ".join(w[i:i+SHINGLE]) for i in range(max(0, len(w) - SHINGLE + 1))}

def main():
    root = pathlib.Path(__file__).resolve().parent.parent
    docs = {}
    for f in sorted(glob.glob(str(root/"content"/"*.json"))):
        try:
            docs[pathlib.Path(f).stem] = shingles(prose(json.loads(pathlib.Path(f).read_text())))
        except json.JSONDecodeError:
            continue

    # Only compare pages likely to overlap: same brand, or same code across brands.
    buckets = collections.defaultdict(set)
    for slug in docs:
        bits = slug.split("-")
        buckets[bits[0]].add(slug)                       # same brand
        if len(bits) > 2: buckets["code:" + bits[-1]].add(slug)   # same code, any brand
    pairs = set()
    for group in buckets.values():
        pairs |= set(itertools.combinations(sorted(group), 2))

    hits = []
    for a, b in pairs:
        sa, sb = docs[a], docs[b]
        if not sa or not sb: continue
        overlap = len(sa & sb) / min(len(sa), len(sb))
        if overlap >= REPORT_AT:
            hits.append((overlap, a, b))
    hits.sort(reverse=True)

    print(f"compared {len(pairs):,} related page pairs out of {len(docs)} pages")
    bad = [h for h in hits if h[0] >= FAIL_AT]
    if hits:
        print(f"{len(hits)} pair(s) over {REPORT_AT:.0%} shared phrasing:")
        for ov, a, b in hits[:20]:
            flag = "FAIL" if ov >= FAIL_AT else "note"
            print(f"   {flag} {ov:5.1%}  {a}  <->  {b}")
        if len(hits) > 20: print(f"   ... and {len(hits)-20} more")
    else:
        print(f"no pair shares more than {REPORT_AT:.0%} of its phrasing")
    return 1 if bad else 0

if __name__ == "__main__":
    sys.exit(main())
