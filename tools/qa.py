#!/usr/bin/env python3
"""Post-build checks: link integrity, structured data, metadata hygiene."""
import sys, re, json, pathlib, collections
ROOT = pathlib.Path(__file__).resolve().parent.parent
dist = ROOT/"dist"
if not dist.exists(): sys.exit("dist/ does not exist; run site/build.py first")

pages = sorted(dist.rglob("*.html"))
have = {("/"+p.relative_to(dist).parent.as_posix().strip(".")+"/").replace("//","/")
        for p in pages if p.name == "index.html"}
have |= {"/"+p.relative_to(dist).as_posix() for p in pages}
have |= {"/"+p.relative_to(dist).as_posix() for p in dist.rglob("*") if p.is_file()}

fail = 0
broken = collections.defaultdict(list)
titles, descs, canons = {}, {}, collections.Counter()
no_ld, bad_ld = [], []

for p in pages:
    rel = p.relative_to(dist).as_posix()
    h = p.read_text()
    for href in re.findall(r'href="(/[^"#?]*)"', h):
        if href not in have: broken[href].append(rel)
    t = re.search(r"<title>(.*?)</title>", h, re.S)
    d = re.search(r'<meta name="description" content="(.*?)"', h, re.S)
    c = re.search(r'<link rel="canonical" href="(.*?)"', h)
    if t: titles.setdefault(t.group(1), []).append(rel)
    if d: descs.setdefault(d.group(1), []).append(rel)
    if c: canons[c.group(1)] += 1
    blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', h, re.S)
    if not blocks and rel != "404.html": no_ld.append(rel)
    for b in blocks:
        try: json.loads(b)
        except json.JSONDecodeError as e: bad_ld.append(f"{rel}: {e}")

print(f"pages:                 {len(pages)}")
print(f"broken internal links: {sum(len(v) for v in broken.values())} "
      f"across {len(broken)} distinct targets")
for tgt, srcs in sorted(broken.items())[:12]:
    print(f"    {tgt}  <- {len(srcs)} page(s), e.g. {srcs[0]}")
dup_t = {k: v for k, v in titles.items() if len(v) > 1}
dup_d = {k: v for k, v in descs.items() if len(v) > 1}
dup_c = {k: v for k, v in canons.items() if v > 1}
print(f"duplicate titles:      {len(dup_t)}")
for k, v in list(dup_t.items())[:5]: print(f"    {k[:60]!r} x{len(v)}")
print(f"duplicate descriptions:{len(dup_d)}")
print(f"duplicate canonicals:  {len(dup_c)}")
print(f"pages with no JSON-LD: {len(no_ld)}")
print(f"malformed JSON-LD:     {len(bad_ld)}")
for b in bad_ld[:5]: print("   ", b)
long_t = [(k, len(k)) for k in titles if len(k) > 70]
print(f"titles over 70 chars:  {len(long_t)}")

if broken: fail = 1
if bad_ld: fail = 1
if dup_c: fail = 1
print("\nQA:", "FAIL" if fail else "PASS")
sys.exit(fail)
