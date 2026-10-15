#!/usr/bin/env python3
"""
Step 2 - collapse the keyword list into one page per real topic. Costs zero Claude tokens.

"lg washer ue code", "ue code on lg washer" and "ue error code lg washer" are three
phrasings of one page. This script groups them, picks the highest-volume phrasing as the
primary keyword, and sums the cluster volume so you can publish in demand order.

    python pipeline/02_pagemap.py --in data/keywords-us-full.csv --out data/pagemap.json
"""
import argparse, csv, json, re, collections, pathlib

BRANDS = ["samsung","lg","whirlpool","maytag","bosch","ge","kenmore","frigidaire",
          "kitchenaid","kitchen aid","electrolux","amana","miele","asko","hisense",
          "hotpoint","speed queen","beko"]
APPLIANCES = {
    "washing machine":"washer","washer":"washer","dryer":"dryer","dishwasher":"dishwasher",
    "refrigerator":"refrigerator","fridge":"refrigerator","freezer":"freezer","oven":"oven",
    "range":"range","stove":"range","microwave":"microwave","dehumidifier":"dehumidifier",
    "air conditioner":"air conditioner","coffee machine":"coffee machine"}
# A code is a short alphanumeric token, optionally a paired form like "f5 e3" / "f8e4".
CODE = re.compile(r"\b((?:[a-z]{1,3}\d{1,3}|\d{1,2}[a-z]{1,2}|[a-z]{2}\d?)"
                  r"(?:\s?e\s?\d{1,2})?|h2o|sud|loc|po|dr|ftd|nd|nf|cl|ue|oe|ie|le|de|fe|se|sc|ur|ub|dc|hc|af|pf|lf|sd|be|ae|oc|tcl)\b")
STOP = {"code","codes","error","errors","fault","list","pdf","chart","on","a","the","my",
        "what","does","mean","how","to","fix","reset","download","top","front","load",
        "loader","washing","machine","elite","series","diagnostic","binary","combo","in",
        "is","why","for","and","no","not","of","it","still"}
# Tokens that look like codes but are really words in these queries.
NOT_A_CODE = {"he","xl","4t","e9"} - {"e9"}

def parse(kw):
    k = kw.lower()
    brand = next((b for b in sorted(BRANDS, key=len, reverse=True) if re.search(rf"\b{re.escape(b)}\b", k)), None)
    appliance = None
    for phrase in sorted(APPLIANCES, key=len, reverse=True):
        if re.search(rf"\b{re.escape(phrase)}\b", k):
            appliance = APPLIANCES[phrase]; break
    rest = k
    if brand: rest = re.sub(rf"\b{re.escape(brand)}\b", " ", rest)
    for phrase in APPLIANCES: rest = re.sub(rf"\b{re.escape(phrase)}\b", " ", rest)
    rest = " ".join(w for w in rest.split() if w not in STOP)
    m = CODE.search(rest)
    code = re.sub(r"\s+", "", m.group(1)).upper() if m else None
    if code and code.lower() in NOT_A_CODE: code = None
    return brand, appliance, code

def slug(*parts):
    return re.sub(r"[^a-z0-9]+","-","-".join(p for p in parts if p).lower()).strip("-")

def main(src, dst, min_volume):
    rows = list(csv.DictReader(open(src)))
    groups, unmapped = collections.defaultdict(list), []
    for r in rows:
        kw, vol = r["keyword"], int(r["volume"] or 0)
        brand, appliance, code = parse(kw)
        if not (brand and appliance):
            unmapped.append((kw, vol)); continue
        groups[(brand, appliance, code)].append((kw, vol))

    pages = []
    for (brand, appliance, code), kws in groups.items():
        kws.sort(key=lambda x: -x[1])
        total = sum(v for _, v in kws)
        if total < min_volume: continue
        kind = "code" if code else "list"
        s = slug(brand, appliance, code) if code else slug(brand, appliance, "error-codes")
        pages.append({
            "slug": s,
            "url": f"/{slug(brand)}/{slug(appliance)}/" + (f"{slug(code)}-error-code/" if code else "error-codes/"),
            "page_type": kind, "brand": brand, "appliance": appliance, "code": code,
            "primary_keyword": kws[0][0], "cluster_volume": total,
            "secondary_keywords": [k for k, _ in kws[1:12]],
            "source_urls": [],
        })
    pages.sort(key=lambda p: -p["cluster_volume"])
    pathlib.Path(dst).write_text(json.dumps(pages, indent=2))

    code_pages = [p for p in pages if p["page_type"] == "code"]
    print(f"{len(rows)} keywords -> {len(pages)} pages "
          f"({len(code_pages)} code pages, {len(pages)-len(code_pages)} brand list pages)")
    print(f"covered volume: {sum(p['cluster_volume'] for p in pages):,}/mo")
    print(f"unmapped keywords: {len(unmapped)} ({sum(v for _,v in unmapped):,}/mo)")
    print("\ntop 15 pages by clustered volume:")
    for p in pages[:15]:
        print(f"  {p['cluster_volume']:>6}/mo  {p['url']:<46} {p['primary_keyword']}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="src", default="data/keywords-us-full.csv")
    ap.add_argument("--out", dest="dst", default="data/pagemap.json")
    ap.add_argument("--min-volume", type=int, default=0)
    a = ap.parse_args()
    main(a.src, a.dst, a.min_volume)
