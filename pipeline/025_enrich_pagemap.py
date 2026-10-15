#!/usr/bin/env python3
"""
Step 2b - make sure every brand+appliance family that has code pages also has a hub page.

"maytag dryer error codes" is a real query with real volume, and the hub it lands on is what
passes authority down to the individual code pages. Deriving these from the family structure
rather than from whether the exact phrase happened to appear in a keyword export means the
internal linking is complete by construction.
"""
import json, pathlib, re, collections, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
pm = json.loads((ROOT/"data"/"pagemap.json").read_text())
slug = lambda s: re.sub(r"[^a-z0-9]+","-",str(s).lower()).strip("-")

fams = collections.defaultdict(list)
for p in pm: fams[(p["brand"], p["appliance"])].append(p)

added = []
for (brand, appl), ps in fams.items():
    codes = [p for p in ps if p["page_type"] == "code"]
    if len(codes) < 2: continue
    if any(p["page_type"] == "list" for p in ps): continue
    s = slug(f"{brand}-{appl}-error-codes")
    added.append({
        "slug": s,
        "url": f"/{slug(brand)}/{slug(appl)}/error-codes/",
        "page_type": "list", "brand": brand, "appliance": appl, "code": None,
        "primary_keyword": f"{brand} {appl} error codes",
        # Conservative: a hub earns a fraction of the family's demand, it does not own it.
        "cluster_volume": max(40, int(sum(p["cluster_volume"] for p in codes) * 0.06)),
        "secondary_keywords": [f"{brand} {appl} error code list",
                               f"{brand} {appl} fault codes",
                               f"{brand} {appl} codes"],
        "source_urls": [],
    })

pm += added
pm.sort(key=lambda p: -p["cluster_volume"])
(ROOT/"data"/"pagemap.json").write_text(json.dumps(pm, indent=2))
print(f"added {len(added)} missing brand+appliance hub pages -> {len(pm)} pages total")
for a in sorted(added, key=lambda x: -x["cluster_volume"])[:12]:
    print(f'   {a["cluster_volume"]:>5}/mo  {a["url"]}')
