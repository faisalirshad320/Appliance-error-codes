#!/usr/bin/env python3
"""
Guard the release schedule against the page map.

A page that exists but appears in no wave is never published — the build simply holds
it, forever, and nothing else complains. That is a silent failure, so it is a CI error
here. Regenerate with tools/make_schedule.py after adding or removing pages.
"""
import collections, datetime, json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sched = json.loads((ROOT / "pipeline" / "release-schedule.json").read_text())
pages = json.loads((ROOT / "data" / "pagemap.json").read_text())

known = {p["slug"] for p in pages}
scheduled = [s for w in sched["waves"] for s in w["slugs"]]
counts = collections.Counter(scheduled)

errs = []
missing = sorted(known - set(scheduled))
if missing:
    errs.append(f"{len(missing)} page(s) in no wave, so they would never publish: "
                + ", ".join(missing[:8]) + (" ..." if len(missing) > 8 else ""))

unknown = sorted(set(scheduled) - known)
if unknown:
    errs.append(f"{len(unknown)} scheduled slug(s) with no page: "
                + ", ".join(unknown[:8]) + (" ..." if len(unknown) > 8 else ""))

dupes = sorted(s for s, n in counts.items() if n > 1)
if dupes:
    errs.append(f"{len(dupes)} slug(s) in more than one wave: " + ", ".join(dupes[:8]))

offsets = [w["offset_days"] for w in sched["waves"]]
if offsets != sorted(offsets) or len(set(offsets)) != len(offsets):
    errs.append(f"wave offsets are not strictly increasing: {offsets}")

try:
    datetime.date.fromisoformat(sched["launch_date"])
except (ValueError, KeyError) as e:
    errs.append(f"launch_date is not a usable date: {e}")

for w in sched["waves"]:
    if len(w["slugs"]) != w["pages"]:
        errs.append(f"wave {w['wave']}: pages={w['pages']} but {len(w['slugs'])} slugs")

print(f"pages in map:      {len(known)}")
print(f"pages scheduled:   {len(scheduled)} across {len(sched['waves'])} waves")
print(f"launch date:       {sched.get('launch_date')}")
for e in errs:
    print("  ERROR:", e)
print("\nSchedule:", "FAIL" if errs else "PASS")
sys.exit(1 if errs else 0)
