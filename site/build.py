#!/usr/bin/env python3
"""
Static site build. Reads data/pagemap.json plus content/*.json and writes dist/.

No framework, no runtime, no database. Output is plain HTML that an Apache or Nginx
document root serves directly, which is what the Cloudways PHP app will host.
"""
import json, pathlib, re, html, sys, os, datetime, collections

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "site" / "lib"))
import diagrams, schema as pschema

CFG = json.loads((ROOT / "site" / "config.json").read_text())
SITE, URL = CFG["site_name"], CFG["site_url"].rstrip("/")
TODAY = datetime.date.today().isoformat()

# A page's dates come from the day its wave went live, never from the day the build
# happened. Stamping today's date on every page every morning tells search engines all
# 252 pages changed daily when nothing did, which is both untrue and the kind of
# freshness signal that gets discounted. It also made the build output differ every day,
# so the deploy branch churned and there was no clean way to tell a real release from a
# rebuild. Populated by main(); PUB_DATE maps slug -> ISO date, LATEST is the newest
# live wave's date and covers hubs, the home page and anything not tied to one wave.
PUB_DATE, LATEST, URL_DATE = {}, TODAY, {}
E = lambda s: html.escape(str(s if s is not None else ""), quote=True)

# Populated by main() once it knows which pages have content. The footer and any other
# site-wide navigation is rendered from this, so a link can never point at a page the
# build did not write.
NAV = {"appliances": [], "brands": []}

BRAND_LABEL = {"lg":"LG","ge":"GE","kitchenaid":"KitchenAid","kitchen aid":"KitchenAid",
               "speed queen":"Speed Queen","asko":"Asko","miele":"Miele","beko":"Beko"}
label_brand = lambda b: BRAND_LABEL.get(b, b.title())
label_appl = lambda a: a.title() if a != "air conditioner" else "Air Conditioner"

# Letters whose spoken name begins with a vowel sound, so "an LG" but "a GE" (jee).
_VOWEL_SOUND_LETTERS = set("AEFHILMNORSX")

def article(name):
    """'a' or 'an' for a brand name, judged on how the name is said aloud."""
    if not name:
        return "a"
    first = name[0].upper()
    # An all-caps initialism is spelled out letter by letter: LG is "el-gee".
    if len(name) <= 3 and name.isupper():
        return "an" if first in _VOWEL_SOUND_LETTERS else "a"
    return "an" if first in "AEIO" else "a"


# ----------------------------------------------------------------- layout

def layout(*, title, desc, canonical, body, jsonld=None, crumb=None, extra_head=""):
    ld = ""
    for blk in (jsonld or []):
        ld += ('\n<script type="application/ld+json">'
               + json.dumps(blk, ensure_ascii=False, separators=(",", ":")) + "</script>")
    crumbs = ""
    if crumb:
        items = "".join(
            f'<li><a href="{E(u)}">{E(t)}</a></li>' if u else f"<li>{E(t)}</li>"
            for t, u in crumb)
        crumbs = f'<nav class="crumb" aria-label="Breadcrumb"><div class="wrap"><ol>{items}</ol></div></nav>'
    foot_appliances = "".join(f'<li><a href="{E(u)}">{E(t)}</a></li>'
                              for t, u in NAV["appliances"]) or "<li>Coming soon</li>"
    foot_brands = "".join(f'<li><a href="{E(u)}">{E(t)}</a></li>'
                          for t, u in NAV["brands"]) or "<li>Coming soon</li>"
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)}</title>
<meta name="description" content="{E(desc)}">
<link rel="canonical" href="{E(canonical)}">
<meta name="theme-color" content="{E(CFG['theme_color'])}">
<meta property="og:type" content="article">
<meta property="og:title" content="{E(title)}">
<meta property="og:description" content="{E(desc)}">
<meta property="og:url" content="{E(canonical)}">
<meta property="og:site_name" content="{E(SITE)}">
<meta name="twitter:card" content="summary_large_image">
<meta name="robots" content="index,follow,max-snippet:-1,max-image-preview:large">
<link rel="stylesheet" href="/assets/main.css">
<link rel="icon" href="/assets/icon.svg" type="image/svg+xml">{extra_head}{ld}
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="site-head"><div class="wrap">
  <a class="logo" href="/"><span class="mark">E</span>{E(SITE)}</a>
  <nav class="site-nav" aria-label="Main">
    <a href="/brands/">Brands</a><a href="/codes/">All codes</a>
    <a href="/find-your-code/">Find your code</a><a href="/about/">About</a>
  </nav>
</div></header>
{crumbs}
<main id="main"><div class="wrap">
{body}
</div></main>
<footer class="site-foot"><div class="wrap">
  <div class="foot-grid">
    <div><h2>Appliances</h2><ul>{foot_appliances}</ul></div>
    <div><h2>Top brands</h2><ul>{foot_brands}</ul></div>
    <div><h2>Site</h2><ul>
      <li><a href="/about/">About and sources</a></li>
      <li><a href="/editorial-policy/">Editorial policy</a></li>
      <li><a href="/sitemap.xml">Sitemap</a></li></ul></div>
  </div>
  <div class="foot-base">
    <span>&copy; {datetime.date.today().year} {E(SITE)}. Diagrams are original work.</span>
    <span>Brand names belong to their owners. This site is not affiliated with any manufacturer.</span>
  </div>
</div></footer>
</body></html>'''


# ----------------------------------------------------------------- JSON-LD

def ld_breadcrumb(crumb):
    return {"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[
        {"@type":"ListItem","position":i+1,"name":t,
         **({"item":URL+u} if u else {})} for i,(t,u) in enumerate(crumb)]}

def ld_howto(d, page, canonical):
    steps = []
    for i, s in enumerate(d["steps"], 1):
        steps.append({"@type":"HowToStep","position":i,"name":s["name"],
                      "text":s["detail"],"url":f"{canonical}#step-{i}"})
    out = {"@context":"https://schema.org","@type":"HowTo",
        "name":d["h1"],"description":d["answer"],"url":canonical,
        "totalTime":_iso_duration(sum(s.get("minutes",0) for s in d["steps"])),
        "step":steps}
    if d.get("parts"):
        out["supply"] = [{"@type":"HowToSupply","name":p["name"]} for p in d["parts"]]
    tools = sorted({t.strip() for s in d["steps"] for t in (s.get("tools") or "").split(",") if t.strip()})
    if tools:
        out["tool"] = [{"@type":"HowToTool","name":t} for t in tools[:8]]
    return out

def _iso_duration(mins):
    mins = max(1, int(mins))
    return f"PT{mins//60}H{mins%60}M" if mins >= 60 else f"PT{mins}M"

def ld_faq(d):
    return {"@context":"https://schema.org","@type":"FAQPage","mainEntity":[
        {"@type":"Question","name":f["q"],
         "acceptedAnswer":{"@type":"Answer","text":f["a"]}} for f in d["faqs"]]}

def _pubdate(page):
    """The date this page went live, falling back to the newest live wave."""
    return PUB_DATE.get(page["slug"], LATEST)


def ld_article(d, page, canonical):
    return {"@context":"https://schema.org","@type":"TechArticle",
        "headline":d["h1"],"description":d["meta_description"],
        "mainEntityOfPage":{"@type":"WebPage","@id":canonical},
        "datePublished":_pubdate(page),"dateModified":_pubdate(page),
        "author":{"@type":"Organization","name":CFG["publisher"],"url":URL+"/about/"},
        "publisher":{"@type":"Organization","name":CFG["publisher"],"url":URL},
        "about":{"@type":"Thing",
                 "name":f'{label_brand(page["brand"])} {page["appliance"]} '
                        f'{page["code"] or "error"} code'},
        "speakable":{"@type":"SpeakableSpecification","cssSelector":[".answer",".facts"]},
        "proficiencyLevel":"Beginner"}


# ----------------------------------------------------------------- code page

def render_code_page(page, d, index):
    canonical = URL + page["url"]
    brand, appl = label_brand(page["brand"]), label_appl(page["appliance"])
    crumb = [("Home","/"), (brand, f'/{slugify(page["brand"])}/'),
             (f"{brand} {appl}", f'/{slugify(page["brand"])}/{slugify(page["appliance"])}/'),
             (page["code"] or "Error codes", None)]

    facts = f'''<dl class="facts">
  <div><dt>Severity</dt><dd class="sev-{E(d["severity"])}">{E(d["severity"].replace("-"," ").title())}</dd></div>
  <div><dt>Fix it yourself</dt><dd>{E(d["can_diy"].title())}</dd></div>
  <div><dt>Time</dt><dd>{E(d["time_estimate"])}</dd></div>
  <div><dt>DIY cost</dt><dd>{E(d["cost_estimate"]["diy"])}</dd></div>
  <div><dt>Technician</dt><dd>{E(d["cost_estimate"]["technician"])}</dd></div>
</dl>'''

    safety = ""
    if d.get("safety_warning"):
        safety = (f'<div class="note danger"><strong>Safety first</strong>'
                  f'<p>{E(d["safety_warning"])}</p></div>')

    causes = "".join(
        f'<li><b>{E(c["cause"])}<span class="freq freq-{c["frequency"].split()[0]}">'
        f'{E(c["frequency"])}</span></b><span class="how">{E(c["confirm"])}</span></li>'
        for c in d["causes"])

    steps_html = ""
    for i, s in enumerate(d["steps"], 1):
        meta = [f'<span><b>{s["minutes"]}</b> min</span>']
        if s.get("tools"): meta.append(f'<span>Tools: <b>{E(s["tools"])}</b></span>')
        warn = (f'<p class="warn">{E(s["warning"])}</p>' if s.get("warning") else "")
        steps_html += (f'<li id="step-{i}"><h3>{E(s["name"])}</h3><p>{E(s["detail"])}</p>'
                       f'<div class="meta">{"".join(meta)}</div>{warn}</li>')

    parts = ""
    if d.get("parts"):
        rows = "".join(
            f'<tr><td>{E(p["name"])}</td><td>{E(p["cost"])}</td>'
            f'<td class="d-{p["difficulty"].replace(" ","")}">{E(p["difficulty"].title())}</td>'
            f'<td>{E(p.get("note") or "—")}</td></tr>' for p in d["parts"])
        parts = (f'<h2 id="parts">Parts you might need</h2><table class="tbl">'
                 f'<thead><tr><th>Part</th><th>Typical cost</th><th>Difficulty</th>'
                 f'<th>Note</th></tr></thead><tbody>{rows}</tbody></table>')

    faqs = "".join(
        f'<details><summary>{E(f["q"])}</summary><div class="a"><p>{E(f["a"])}</p></div></details>'
        for f in d["faqs"])

    diagram = diagrams.render(d["diagram"]["kind"], d["diagram"].get("labels", {}),
                              page["appliance"], d["diagram"].get("caption"))

    reset = (f'<h2 id="reset">How to reset it</h2><p>{E(d["reset_procedure"])}</p>'
             if d.get("reset_procedure") else "")
    models = (f'<h2 id="models">Differences between models</h2><p>{E(d["model_notes"])}</p>'
              if d.get("model_notes") else "")

    srcs = "".join(
        (f'<li><a href="{E(s["url"])}" rel="nofollow noopener" target="_blank">{E(s["title"])}</a>'
         f' — {E(s["publisher"])}</li>') if s.get("url")
        else f'<li>{E(s["title"])} — {E(s["publisher"])}</li>'
        for s in d["sources"])

    related = index.related(page)
    rel_html = ""
    if related:
        rel_html = '<section><h2>Related codes</h2><ul>' + "".join(
            f'<li><a href="{E(r["url"])}">{E(label_brand(r["brand"]))} '
            f'{E(r["appliance"])} <span class="code-chip">{E(r["code"] or "list")}</span></a></li>'
            for r in related) + '</ul></section>'

    toc = [("What it means", "#answer"), ("Why it happens", "#causes"),
           ("Fix it step by step", "#fix")]
    if reset: toc.append(("How to reset it", "#reset"))
    toc.append(("Still showing the code", "#still"))
    if parts: toc.append(("Parts you might need", "#parts"))
    toc += [("When to call someone", "#call"), ("Questions", "#faq")]
    toc_html = '<section><h2>On this page</h2><ul class="toc">' + "".join(
        f'<li><a href="{u}">{E(t)}</a></li>' for t, u in toc) + '</ul></section>'

    # Hubs exist only where the family has at least one written page.
    hub_links = ""
    if any(x["slug"] in index.built for x in index.by_brand[page["brand"]]):
        hub_links += (f'<li><a href="/{slugify(page["brand"])}/">All {E(brand)} codes</a></li>')
    if any(x["slug"] in index.built
           for x in index.by_ba[(page["brand"], page["appliance"])]):
        hub_links += (f'<li><a href="/{slugify(page["brand"])}/{slugify(page["appliance"])}/">'
                      f'{E(brand)} {E(appl.lower())} codes</a></li>')
    if any(x["slug"] in index.built for x in index.by_appl[page["appliance"]]):
        hub_links += (f'<li><a href="/codes/{slugify(page["appliance"])}/">'
                      f'Every {E(appl.lower())} code</a></li>')

    body = f'''<div class="page">
<article>
<h1>{E(d["h1"])}</h1>
<p class="updated">Last reviewed {_pubdate(page)} · {E(brand)} {E(appl.lower())}</p>
<div class="answer" id="answer"><span class="lede">What it means</span><p>{E(d["answer"])}</p></div>
{facts}
{safety}
{diagram}
<h2 id="causes">Why {article(brand)} {E(brand)} {E(appl.lower())} shows {E(page["code"] or "this code")}</h2>
<p>These are the causes in the order you are most likely to hit them. Work down the list,
do not skip to the expensive one.</p>
<ol class="causes">{causes}</ol>
<h2 id="fix">Fix it step by step</h2>
<ol class="steps">{steps_html}</ol>
{reset}
<h2 id="still">It still shows {E(page["code"] or "the code")}</h2>
<p>{E(d["still_showing"])}</p>
{models}
{parts}
<div class="cta">
  <h3>Need a part or a technician?</h3>
  <p>If the steps above pointed at a failed component, you can order the part and fit it
  yourself, or have someone local do the job.</p>
  <a class="btn" href="{E(CFG["parts_cta_url"])}">Find the part</a>
  <a class="btn ghost" href="{E(CFG["lead_cta_url"])}">Book a technician</a>
</div>
<h2 id="call">When to stop and call someone</h2>
<p>{E(d["when_to_call"])}</p>
<h2 id="faq">Questions people ask</h2>
<div class="faq">{faqs}</div>
<div class="sources"><h2>Sources</h2><ul>{srcs}</ul></div>
<p class="disclaimer">Diagrams on this page are original schematics drawn for this site and are
not manufacturer drawings. Costs are typical United States figures and vary by region and model.
Work within your competence: anything involving mains wiring, gas or a sealed refrigerant
circuit belongs to a qualified technician.</p>
</article>
<aside class="side">{toc_html}{rel_html}
<section><h2>More {E(brand)}</h2><ul>{hub_links}</ul></section>
</aside>
</div>'''

    return layout(title=d["title"], desc=d["meta_description"], canonical=canonical,
                  body=body, crumb=crumb,
                  jsonld=[ld_article(d,page,canonical), ld_howto(d,page,canonical),
                          ld_faq(d), ld_breadcrumb(crumb)])


def slugify(s):
    return re.sub(r"[^a-z0-9]+","-",str(s).lower()).strip("-")


# ----------------------------------------------------------------- index / hubs

class Index:
    def __init__(self, pages, built=None):
        # `built` is the set of slugs that have content. Everything this class hands back
        # for linking is filtered through it, so a hub or sidebar can never link into a 404.
        self.built = built if built is not None else {p["slug"] for p in pages}
        self.pages = pages
        self.by_brand = collections.defaultdict(list)
        self.by_appl = collections.defaultdict(list)
        self.by_ba = collections.defaultdict(list)
        for p in pages:
            self.by_brand[p["brand"]].append(p)
            self.by_appl[p["appliance"]].append(p)
            self.by_ba[(p["brand"], p["appliance"])].append(p)
        for d in (self.by_brand, self.by_appl, self.by_ba):
            for v in d.values():
                v.sort(key=lambda p: -p["cluster_volume"])

    def related(self, page, n=6):
        ok = lambda p: p["slug"] in self.built and p["slug"] != page["slug"]
        same = [p for p in self.by_ba[(page["brand"], page["appliance"])] if ok(p)][:n]
        for pool in (self.by_brand[page["brand"]], self.by_appl[page["appliance"]]):
            if len(same) >= n: break
            same += [p for p in pool if ok(p) and p not in same][:n - len(same)]
        return same[:n]


def card(p, built):
    """Renders nothing for a page that has no content yet, so hubs never link into a 404."""
    if p["slug"] not in built:
        return ""
    d = built[p["slug"]]
    chip = f'<span class="code-chip">{E(p["code"])}</span> ' if p["code"] else ""
    sub = d.get("answer", "")[:92].rsplit(" ", 1)[0] + "…" if d.get("answer") else "Error code"
    return (f'<li><a class="card" href="{E(p["url"])}">'
            f'<b>{chip}{E(label_brand(p["brand"]))} {E(p["appliance"])}</b>'
            f'<span>{E(sub)}</span></a></li>')


def hub(title, h1, intro, groups, canonical, crumb, desc):
    blocks = ""
    for heading, items in groups:
        if not items: continue
        blocks += f'<h2>{E(heading)}</h2><ul class="grid">{items}</ul>'
    body = (f'<div class="hero"><h1>{E(h1)}</h1><p>{E(intro)}</p></div>'
            f'<div class="page"><article style="max-width:none">{blocks}</article></div>')
    return layout(title=title, desc=desc, canonical=canonical, body=body, crumb=crumb,
                  jsonld=[ld_breadcrumb(crumb)])


def render_home(idx, built):
    live = [p for p in idx.pages if p["slug"] in built]
    top = sorted(live, key=lambda p: -p["cluster_volume"])[:12]
    nb = {b: len([p for p in ps if p["slug"] in built]) for b, ps in idx.by_brand.items()}
    na = {a: len([p for p in ps if p["slug"] in built]) for a, ps in idx.by_appl.items()}
    brand_cards = "".join(
        f'<li><a class="card" href="/{slugify(b)}/"><b>{E(label_brand(b))}</b>'
        f'<span>{nb[b]} code{"s" if nb[b]!=1 else ""} covered</span></a></li>'
        for b, ps in sorted(idx.by_brand.items(), key=lambda kv: -nb[kv[0]]) if nb[b])
    appl_cards = "".join(
        f'<li><a class="card" href="/codes/{slugify(a)}/"><b>{E(label_appl(a))}</b>'
        f'<span>{na[a]} code{"s" if na[a]!=1 else ""}</span></a></li>'
        for a, ps in sorted(idx.by_appl.items(), key=lambda kv: -na[kv[0]]) if na[a])
    body = f'''<div class="hero">
<h1>Your appliance is showing a code. Here is what it means.</h1>
<p>Plain explanations and step-by-step fixes for {len(built)} error codes across
{len(idx.by_brand)} brands. Written to get you to the answer in the first sentence,
not the fifth paragraph.</p>
<form class="search-box" action="/find-your-code/" method="get" role="search">
  <label class="skip" for="q">Search an error code</label>
  <input id="q" name="q" type="search" placeholder="Try 4C, UE, E15, D80…" autocomplete="off">
  <button class="btn" type="submit">Find the fix</button>
</form>
</div>
<div class="page"><article style="max-width:none">
<h2>Most searched codes</h2>
<ul class="grid">{"".join(card(p, built) for p in top)}</ul>
<h2>By appliance</h2><ul class="grid">{appl_cards}</ul>
<h2>By brand</h2><ul class="grid">{brand_cards}</ul>
<h2>How this site works</h2>
<p>Every page answers the same four questions in the same order: what the code means,
why it happens, what to do about it, and what to do when that did not work. The last one
is the question most pages on this subject never answer, and it is usually the one that
matters.</p>
<p>Diagrams are drawn for this site rather than taken from manufacturer manuals, so they
show the part you actually need to find rather than an exploded parts view. Costs are
typical United States figures. Where a job involves mains wiring, gas or a sealed
refrigerant circuit, the page says so and tells you to stop.</p>
</article></div>'''
    return layout(title=f"{SITE} — {CFG['tagline']}",
                  desc=("Find what your washer, dryer, dishwasher or fridge error code means "
                        "and how to clear it. Step-by-step fixes for Samsung, LG, Whirlpool, "
                        "Bosch and more."),
                  canonical=URL + "/", body=body,
                  jsonld=[{"@context":"https://schema.org","@type":"WebSite","name":SITE,
                           "url":URL+"/","potentialAction":{"@type":"SearchAction",
                           "target":{"@type":"EntryPoint",
                                     "urlTemplate":URL+"/find-your-code/?q={search_term_string}"},
                           "query-input":"required name=search_term_string"}},
                          {"@context":"https://schema.org","@type":"Organization","name":SITE,
                           "url":URL+"/"}])


def render_finder(pages, built):
    rows = [{"c": p["code"] or "", "b": label_brand(p["brand"]), "a": p["appliance"],
             "u": p["url"]} for p in pages if p["slug"] in built]
    data = json.dumps(rows, separators=(",", ":"))
    body = f'''<div class="hero"><h1>Find your error code</h1>
<p>Type the code on the display, or the brand. {len(rows)} codes indexed.</p>
<div class="search-box"><label class="skip" for="f">Filter codes</label>
<input id="f" type="search" placeholder="4C, UE, E15, Samsung washer…" autocomplete="off"></div>
</div>
<div class="page"><article style="max-width:none">
<ul class="grid" id="results"></ul>
<p id="empty" hidden>Nothing matches that yet. Try just the letters or just the brand.</p>
</article></div>
<script>
const DATA={data};
const inp=document.getElementById('f'),out=document.getElementById('results'),
      empty=document.getElementById('empty');
function esc(s){{return s.replace(/[&<>"]/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}})[c]);}}
function draw(list){{
  out.innerHTML=list.slice(0,120).map(r=>
    `<li><a class="card" href="${{r.u}}"><b>${{r.c?`<span class="code-chip">${{esc(r.c)}}</span> `:''}}`
    +`${{esc(r.b)}} ${{esc(r.a)}}</b><span>View the fix</span></a></li>`).join('');
  empty.hidden=list.length>0;
}}
function run(){{
  const q=inp.value.trim().toLowerCase();
  draw(!q?DATA:DATA.filter(r=>(r.c+' '+r.b+' '+r.a).toLowerCase().includes(q)));
}}
inp.addEventListener('input',run);
const pre=new URLSearchParams(location.search).get('q');
if(pre){{inp.value=pre;}}
run();
</script>'''
    crumb = [("Home","/"),("Find your code",None)]
    return layout(title=f"Find your appliance error code | {SITE}",
                  desc="Search every washer, dryer, dishwasher and refrigerator error code "
                       "covered on this site by code, brand or appliance.",
                  canonical=URL+"/find-your-code/", body=body, crumb=crumb,
                  jsonld=[ld_breadcrumb(crumb)])


STATIC_PAGES = {
 "about": ("About and how we source this", """
<p>This site exists because error-code pages are usually bad. The manufacturer page tells you
the code means "water supply error" and stops. A forum thread gives you nine conflicting
answers. A content farm gives you six paragraphs of preamble before the one sentence you
needed.</p>
<h2>What we do differently</h2>
<p>Every page leads with the answer. Causes are ordered by how often they actually occur rather
than presented as an undifferentiated list. Every fix step names the tool, the part and roughly
how long it takes. And every page has a section for the case where the obvious fix did not
work, because that is where most people actually are by the time they are searching.</p>
<h2>Where the information comes from</h2>
<p>Each page lists its sources. In practice that means manufacturer support documentation and
service literature for what a code signifies, and the repair community for what actually fixes
it in the field. Where sources disagree, the page says so rather than picking one silently.</p>
<h2>Diagrams</h2>
<p>Every diagram is original work, drawn as vector graphics specifically for this site. None are
scanned, traced or copied from a service manual or a product photograph. They are schematic
rather than photographic on purpose: when you are looking for a drain filter behind a kick
panel, a labelled drawing of where it sits beats a glamour shot of the appliance.</p>
<h2>Corrections</h2>
<p>If a page is wrong, it should be fixed. Appliance platforms change between model years and a
procedure that is right for one series can be wrong for the next. Tell us which page, which
model and what actually happened.</p>"""),
 "editorial-policy": ("Editorial policy", """
<h2>Accuracy over completeness</h2>
<p>We would rather a page say "check the service sheet inside the machine for the resistance
value" than print a number we are not certain of. Specific figures, part numbers and torque
settings are only stated where they are verifiable, and pages are explicit about model-series
variation where it exists.</p>
<h2>Safety</h2>
<p>Any procedure touching mains wiring, a gas connection or a sealed refrigerant circuit is
marked and handed to a qualified technician. We do not publish workarounds that defeat a door
interlock, a thermal cut-out or any other safety device, no matter how often they are asked
about.</p>
<h2>Commercial relationships</h2>
<p>Pages may link to parts retailers and to repair services, and those links may earn a
commission. This never changes the diagnosis. If the likeliest cause of your code is a blocked
filter you can clear in ten minutes with no parts, that is what the page says, because a page
that sells you a pump you did not need is a page nobody comes back to.</p>
<h2>Trademarks</h2>
<p>Samsung, LG, Whirlpool, Bosch, GE, Maytag, KitchenAid, Frigidaire, Kenmore, Miele and other
brand names are the property of their respective owners. This site is independent and is not
affiliated with, endorsed by, or authorised by any appliance manufacturer. Brand names are used
only to identify the appliances the guidance applies to.</p>"""),
 "find-a-technician": ("Find an appliance technician", """
<p>Some jobs are not worth doing yourself. If the page you came from sent you here, it is
because the likely fix involves a sealed system, mains wiring, a gas connection, or a part that
costs more than half the price of replacing the machine.</p>
<h2>Before you book</h2>
<p>Have the model and serial number ready, usually on a sticker inside the door, behind the kick
panel or on the back. Tell them the exact code and what you have already tried. A technician who
arrives knowing the filter is already clear and the pump already spins freely will diagnose
faster and charge you less.</p>
<h2>What a call usually costs</h2>
<p>In the United States, a diagnostic visit typically runs 80 to 150 dollars, often credited
against the repair if you go ahead. A completed repair on a washer or dishwasher commonly lands
between 150 and 400 dollars depending on the part. If the quote approaches half the cost of a
new machine and the appliance is over eight years old, replacing is usually the better call.</p>"""),
 "parts": ("Finding the right part", """
<p>The single most expensive mistake in appliance repair is ordering a part for the wrong model.
Error codes are shared across platforms; parts almost never are.</p>
<h2>Find your model number first</h2>
<p>Washers and dryers: inside the door frame, or on the back panel. Dishwashers: on the edge of
the inner door, visible when the door is open. Refrigerators: inside, usually on a side wall or
behind a crisper drawer. Ovens and ranges: on the frame behind the door, or in a drawer.</p>
<h2>Confirm the part before you buy</h2>
<p>Check the part number printed on the component you are replacing against the listing, not just
the model compatibility list. Manufacturers revise parts mid-production and a supersession can
mean the part that fits your serial range is not the one the chart shows.</p>
<h2>Test before you replace</h2>
<p>Most of the components error codes point at can be tested with a multimeter for a few dollars
of effort rather than guessed at for a hundred. Each page says what reading to expect where that
is knowable. Swapping parts until the code clears is the expensive way to repair an
appliance.</p>"""),
}


def render_static(slug, title, html_body):
    crumb = [("Home","/"),(title,None)]
    body = (f'<div class="page"><article><h1>{E(title)}</h1>{html_body}</article></div>')
    return layout(title=f"{title} | {SITE}",
                  desc=re.sub(r"\s+"," ",re.sub(r"<[^>]+>","",html_body)).strip()[:155],
                  canonical=f"{URL}/{slug}/", body=body, crumb=crumb,
                  jsonld=[ld_breadcrumb(crumb)])


HTACCESS = """# Served by the Cloudways Apache stack. Static site, so everything here is
# caching, compression and tidy URLs. No PHP is involved.

Options -Indexes
DirectoryIndex index.html
ErrorDocument 404 /404.html

<IfModule mod_rewrite.c>
  RewriteEngine On

  # Force HTTPS. Cloudways terminates TLS upstream, so trust the forwarded header.
  RewriteCond %{HTTP:X-Forwarded-Proto} =http
  RewriteRule ^(.*)$ https://%{HTTP_HOST}/$1 [R=301,L]

  # One canonical host. Uncomment and set once the domain is attached.
  # RewriteCond %{HTTP_HOST} ^www\\.(.+)$ [NC]
  # RewriteRule ^(.*)$ https://%1/$1 [R=301,L]

  # Every page lives at a directory with a trailing slash. Add it when missing
  # so /samsung/washer/4c-error-code and /samsung/washer/4c-error-code/ are not
  # two URLs with the same content.
  RewriteCond %{REQUEST_FILENAME} -d
  RewriteCond %{REQUEST_URI} !/$
  RewriteRule ^(.*)$ /$1/ [R=301,L]

  # Strip index.html if anyone links to it directly.
  RewriteCond %{THE_REQUEST} \\s/+(.*/)?index\\.html[\\s?] [NC]
  RewriteRule ^(.*/)?index\\.html$ /$1 [R=301,L]
</IfModule>

<IfModule mod_deflate.c>
  AddOutputFilterByType DEFLATE text/html text/css text/plain text/xml
  AddOutputFilterByType DEFLATE application/javascript application/json
  AddOutputFilterByType DEFLATE image/svg+xml application/xml
</IfModule>

<IfModule mod_brotli.c>
  AddOutputFilterByType BROTLI_COMPRESS text/html text/css application/javascript
  AddOutputFilterByType BROTLI_COMPRESS image/svg+xml application/json
</IfModule>

<IfModule mod_expires.c>
  ExpiresActive On
  # Fingerprint-free asset names, so a week with revalidation rather than a year.
  ExpiresByType text/css                 "access plus 7 days"
  ExpiresByType image/svg+xml            "access plus 7 days"
  ExpiresByType application/javascript   "access plus 7 days"
  # HTML changes whenever content is rebuilt; let the browser revalidate.
  ExpiresByType text/html                "access plus 0 seconds"
</IfModule>

<IfModule mod_headers.c>
  Header always set X-Content-Type-Options "nosniff"
  Header always set Referrer-Policy "strict-origin-when-cross-origin"
  Header always set X-Frame-Options "SAMEORIGIN"
  Header always set Permissions-Policy "geolocation=(), microphone=(), camera=()"
  <FilesMatch "\\.html$">
    Header set Cache-Control "public, max-age=0, must-revalidate"
  </FilesMatch>
  <FilesMatch "\\.(css|svg|js)$">
    Header set Cache-Control "public, max-age=604800, stale-while-revalidate=86400"
  </FilesMatch>
</IfModule>
"""


# ----------------------------------------------------------------- main

def released(today=None):
    """Slugs whose release wave is due, and the waves themselves.

    Returns (due_slugs, waves_due, waves_total). A missing schedule releases
    everything, so the build still works for anyone who just cloned the repo.
    Set PUBLISH_ALL=1 to ignore the schedule and build the whole site, which is what
    CI does when it validates content and checks for duplicate prose.
    """
    f = ROOT/"pipeline"/"release-schedule.json"
    if os.environ.get("PUBLISH_ALL") == "1" or not f.exists():
        # Whole-site build: every page dated from its own wave anyway, so the dates
        # stay stable between a full build and a released one.
        if f.exists():
            s = json.loads(f.read_text())
            d0 = datetime.date.fromisoformat(s["launch_date"])
            for w in s["waves"]:
                day = (d0 + datetime.timedelta(days=w["offset_days"])).isoformat()
                for sl in w["slugs"]:
                    PUB_DATE[sl] = day
        return None, 0, 0
    sched = json.loads(f.read_text())
    launch = datetime.date.fromisoformat(sched["launch_date"])
    today = today or datetime.date.today()
    due, n = set(), 0
    for w in sched["waves"]:
        day = (launch + datetime.timedelta(days=w["offset_days"]))
        for sl in w["slugs"]:
            PUB_DATE[sl] = day.isoformat()
        if day <= today:
            due |= set(w["slugs"]); n += 1
    if not n:
        # launch_date is still in the future. Ship the seed wave anyway: whatever is on
        # the deploy branch is what the document root serves, and an empty site is a
        # worse outcome than starting the drip a few days early.
        due, n = set(sched["waves"][0]["slugs"]), 1
    return due, n, len(sched["waves"])


def main():
    pages = json.loads((ROOT/"data"/"pagemap.json").read_text())
    content_dir = ROOT/"content"
    dist = ROOT/"dist"
    due, waves_due, waves_total = released()
    global LATEST
    live_dates = [d for s, d in PUB_DATE.items() if due is None or s in due]
    LATEST = max(live_dates) if live_dates else TODAY

    loaded, problems, held = {}, [], 0
    for p in pages:
        f = content_dir/f'{p["slug"]}.json'
        if not f.exists(): continue
        try:
            d = json.loads(f.read_text())
        except json.JSONDecodeError as e:
            problems.append(f'{p["slug"]}: invalid JSON ({e})'); continue
        errs = pschema.validate(d, p["slug"])
        if errs: problems.extend(errs); continue
        # Validate every page even when it is not due, so a broken file fails the
        # build that writes it rather than the one three weeks later that releases it.
        if due is not None and p["slug"] not in due:
            held += 1; continue
        loaded[p["slug"]] = d

    idx = Index(pages, built=set(loaded))
    # Footer navigation: the four biggest appliance hubs and brand hubs that have content.
    na = [(a, len([p for p in ps if p["slug"] in loaded])) for a, ps in idx.by_appl.items()]
    nb = [(b, len([p for p in ps if p["slug"] in loaded])) for b, ps in idx.by_brand.items()]
    NAV["appliances"] = [(f"{label_appl(a)} codes", f"/codes/{slugify(a)}/")
                         for a, n in sorted(na, key=lambda x: -x[1])[:5] if n]
    NAV["brands"] = [(label_brand(b), f"/{slugify(b)}/")
                     for b, n in sorted(nb, key=lambda x: -x[1])[:5] if n]

    if dist.exists():
        import shutil; shutil.rmtree(dist)
    dist.mkdir(parents=True)
    (dist/"assets").mkdir()
    (dist/"assets"/"main.css").write_text((ROOT/"site"/"assets"/"main.css").read_text())
    (dist/"assets"/"icon.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
        '<rect width="64" height="64" rx="14" fill="#1b4fd8"/>'
        '<text x="32" y="45" font-family="system-ui,sans-serif" font-size="38" font-weight="700"'
        ' fill="#fff" text-anchor="middle">E</text></svg>')

    def write(rel, text):
        leaf = rel.rstrip("/").rsplit("/", 1)[-1]
        is_file = "." in leaf          # .htaccess, sitemap.xml, robots.txt, 404.html
        path = dist/rel.strip("/") if is_file else dist/rel.strip("/")/"index.html"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    urls = []
    for p in pages:
        if p["slug"] not in loaded: continue
        write(p["url"], render_code_page(p, loaded[p["slug"]], idx))
        urls.append((p["url"], "0.9"))
        URL_DATE[p["url"]] = PUB_DATE.get(p["slug"], LATEST)

    # brand hubs and brand+appliance hubs
    for brand, ps in idx.by_brand.items():
        if not any(x["slug"] in loaded for x in ps): continue
        b = label_brand(brand)
        groups = []
        for appl in sorted({x["appliance"] for x in ps}):
            items = "".join(card(x, loaded) for x in ps if x["appliance"] == appl)
            groups.append((f"{b} {label_appl(appl).lower()} codes", items))
        u = f"/{slugify(brand)}/"
        write(u, hub(f"{b} error codes explained | {SITE}", f"{b} error codes",
              f"Every {b} error code covered here, grouped by appliance. Each page gives the "
              f"meaning, the likeliest causes in order, and the fix.",
              groups, URL+u, [("Home","/"),(b,None)],
              f"What every {b} washer, dryer, dishwasher and refrigerator error code means, "
              f"and how to clear it."))
        urls.append((u, "0.7"))

        for appl in sorted({x["appliance"] for x in ps}):
            sub = [x for x in ps if x["appliance"] == appl]
            if not any(x["slug"] in loaded for x in sub): continue
            au = f"/{slugify(brand)}/{slugify(appl)}/"
            al = label_appl(appl)
            write(au, hub(f"{b} {al.lower()} error codes | {SITE}",
                  f"{b} {al.lower()} error codes",
                  f"Codes a {b} {al.lower()} can display, what each one means and what to do.",
                  [(f"{b} {al.lower()} codes", "".join(card(x, loaded) for x in sub))],
                  URL+au, [("Home","/"),(b,f"/{slugify(brand)}/"),(al,None)],
                  f"Every {b} {al.lower()} error code with its meaning and step-by-step fix."))
            urls.append((au, "0.7"))

    # appliance hubs
    for appl, ps in idx.by_appl.items():
        if not any(x["slug"] in loaded for x in ps): continue
        al = label_appl(appl)
        groups = []
        for brand in sorted({x["brand"] for x in ps}):
            items = "".join(card(x, loaded) for x in ps if x["brand"] == brand)
            groups.append((f"{label_brand(brand)} {al.lower()} codes", items))
        u = f"/codes/{slugify(appl)}/"
        write(u, hub(f"{al} error codes, every brand | {SITE}", f"{al} error codes",
              f"{al} error codes across every brand covered here.", groups, URL+u,
              [("Home","/"),("All codes","/codes/"),(al,None)],
              f"Look up any {al.lower()} error code by brand and find out what it means."))
        urls.append((u, "0.7"))

    # all-codes index
    all_groups = [(label_appl(a) + " codes",
                   "".join(card(x, loaded) for x in sorted(ps, key=lambda z:-z["cluster_volume"])))
                  for a, ps in sorted(idx.by_appl.items(), key=lambda kv:-len(kv[1]))]
    write("/codes/", hub(f"All appliance error codes | {SITE}", "Every code on this site",
          f"{len(loaded)} error codes across {len(idx.by_brand)} brands.", all_groups,
          URL+"/codes/", [("Home","/"),("All codes",None)],
          "A complete index of the appliance error codes covered on this site."))
    urls.append(("/codes/", "0.8"))

    # brands index
    brand_items = "".join(
        f'<li><a class="card" href="/{slugify(b)}/"><b>{E(label_brand(b))}</b>'
        f'<span>{len([x for x in ps if x["slug"] in loaded])} pages</span></a></li>'
        for b, ps in sorted(idx.by_brand.items(), key=lambda kv: kv[0])
        if any(x["slug"] in loaded for x in ps))
    write("/brands/", hub(f"Appliance brands | {SITE}", "Brands covered",
          "Pick a brand to see every code we cover for it.",
          [("All brands", brand_items)], URL+"/brands/",
          [("Home","/"),("Brands",None)],
          "Appliance error code guides by brand: Samsung, LG, Whirlpool, Bosch, GE and more."))
    urls.append(("/brands/", "0.7"))

    write("/find-your-code/", render_finder(pages, loaded)); urls.append(("/find-your-code/","0.8"))
    write("/", render_home(idx, loaded)); urls.append(("/", "1.0"))
    for slug, (title, bodyhtml) in STATIC_PAGES.items():
        write(f"/{slug}/", render_static(slug, title, bodyhtml)); urls.append((f"/{slug}/","0.4"))

    sm = ('<?xml version="1.0" encoding="UTF-8"?>\n'
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
          + "".join(f"<url><loc>{URL}{u}</loc>"
                    f"<lastmod>{URL_DATE.get(u, LATEST)}</lastmod>"
                    f"<priority>{pr}</priority></url>\n" for u, pr in sorted(set(urls)))
          + "</urlset>\n")
    write("/sitemap.xml", sm)
    write("/robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {URL}/sitemap.xml\n")

    # IndexNow ownership proof. The protocol wants a file at the site root named
    # <key>.txt whose only content is the key; the release workflow then pushes each
    # wave's URLs to Bing, Yandex, Seznam, Naver and Yep without anyone clicking
    # anything. Google does not use IndexNow and reads the sitemap instead.
    write(f"/{CFG['indexnow_key']}.txt", CFG["indexnow_key"])
    write("/.htaccess", HTACCESS)
    write("/404.html", layout(title=f"Page not found | {SITE}",
          desc="That page does not exist.", canonical=URL+"/404.html",
          body='<div class="hero"><h1>That page does not exist</h1>'
               '<p>The code you want is probably still here under a different address.</p>'
               '<p><a class="btn" href="/find-your-code/">Search every code</a></p></div>'))

    print(f"built {len(loaded)}/{len(pages)} code pages, {len(urls)} urls total -> dist/")
    if held:
        print(f"release schedule: wave {waves_due}/{waves_total} live, "
              f"{held} pages not due yet (PUBLISH_ALL=1 builds all of them)")
    if problems:
        print(f"\n{len(problems)} content problems (those pages were skipped):")
        for pr in problems[:40]: print("  -", pr)
        if len(problems) > 40: print(f"  ... and {len(problems)-40} more")
    return 0 if loaded else 1


if __name__ == "__main__":
    sys.exit(main())
