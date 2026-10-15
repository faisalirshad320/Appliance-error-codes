#!/usr/bin/env python3
"""
Reconcile the page map, the batch assignments and the content on disk.

Three things can drift apart: a page can exist in the map with nobody assigned to write it,
a writer can be assigned a slug that is no longer in the map, and a page can be written
without ever appearing in a batch. All three happened during the first run. This reports
each one so the gap is visible before it ships as a missing page or a dead link.
"""
import json, glob, pathlib, sys, collections

ROOT = pathlib.Path(__file__).resolve().parent.parent
pm = {p["slug"]: p for p in json.loads((ROOT/"data"/"pagemap.json").read_text())}
written = {p.stem for p in (ROOT/"content").glob("*.json")}
assigned = collections.defaultdict(list)
for f in sorted(glob.glob(str(ROOT/"pipeline"/"batches*"/"*.json"))):
    for p in json.loads(pathlib.Path(f).read_text()):
        assigned[p["slug"]].append(pathlib.Path(f).name)

unwritten    = sorted(set(pm) - written)
unassigned   = sorted(set(pm) - written - set(assigned))
orphan_files = sorted(written - set(pm))
stale_assign = sorted(set(assigned) - set(pm))
dupes        = {k: v for k, v in assigned.items() if len(v) > 1}

vol = lambda s: pm[s]["cluster_volume"] if s in pm else 0
total = sum(p["cluster_volume"] for p in pm.values())
done  = sum(p["cluster_volume"] for s, p in pm.items() if s in written)

print(f"page map:        {len(pm)} pages, {total:,} searches/mo")
print(f"written:         {len(written & set(pm))} pages, {done:,}/mo "
      f"({done/total*100:.0f}% of mapped demand)")
print(f"still to write:  {len(unwritten)} pages, {total-done:,}/mo")
print(f"  of those, assigned to a batch: {len(unwritten) - len(unassigned)}")
print(f"  of those, assigned to nobody:  {len(unassigned)}")

if unassigned:
    print("\nin the map, not written, not assigned to anyone:")
    for s in sorted(unassigned, key=lambda s: -vol(s))[:25]:
        print(f"   {vol(s):>5}/mo  {s}")
    if len(unassigned) > 25: print(f"   ... and {len(unassigned)-25} more")
if orphan_files:
    print(f"\nwritten but not in the page map ({len(orphan_files)}) — these build nothing:")
    for s in orphan_files: print("   ", s)
if stale_assign:
    print(f"\nassigned but no longer in the page map ({len(stale_assign)}):")
    for s in stale_assign: print("   ", s)
if dupes:
    print(f"\nassigned to more than one batch ({len(dupes)}):")
    for k, v in dupes.items(): print(f"   {k}: {v}")

# Orphans and duplicates are real defects; an unwritten page is just work remaining.
sys.exit(1 if (orphan_files or dupes) else 0)
