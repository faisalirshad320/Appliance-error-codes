# Appliance Error Codes

A static site answering "my appliance is showing this code, what do I do". One page per
brand × appliance × error code, built from keyword data rather than guesswork.

Current scope: **251 pages** across 20 brands, covering roughly **200,000 US searches a
month**. See `NICHE-VALIDATION-REPORT.md` for the research this was built on and
`COST-AND-PIPELINE.md` for what generating it costs.

## Publishing

Pages are not all live. They are released in 11 waves over ~3.5 months by a daily GitHub
Actions workflow, so a brand-new domain does not publish 252 pages in one afternoon.
See `RELEASE.md`; check status with `python3 tools/release_status.py`.

Build the whole site locally regardless of the schedule:

```bash
PUBLISH_ALL=1 python3 site/build.py
```

## Why it is shaped this way

Error-code pages are usually bad in three specific ways, and each one is a design decision
here:

| The usual failure | What this does instead |
|---|---|
| Six paragraphs before the answer | The answer is the first element on the page, in its own block, written to be lifted whole into an AI Overview |
| Five causes presented as equally likely | Causes carry a frequency label and are ordered by what actually happens |
| The page ends where the obvious fix failed | Every page has a "still showing the code" section with an ordered escalation, usually the longest section |
| Stock photo of a washing machine | Original labelled SVG schematics, drawn at build time, showing where the part actually is |

## Layout

```
content/              one JSON file per page, the source of truth
data/                 keyword exports and the derived page map
site/
  build.py            the static site generator
  config.json         site name, URL, CTA targets — set site_url before production
  lib/diagrams.py     the original SVG diagram library
  lib/schema.py       the page contract and its validator
  assets/main.css     the whole stylesheet, no framework
pipeline/
  01_harvest.py       crawl4ai reference gathering, runs locally, free
  02_pagemap.py       collapses keywords into unique pages
  025_enrich_pagemap.py  adds any missing brand+appliance hub pages
  03_generate.py      Anthropic Batch API generation with a dry-run cost estimate
  WRITER-BRIEF.md     the editorial contract every page is written against
tools/
  validate_content.py schema check, runs in CI
  qa.py               link integrity, structured data, metadata hygiene
dist/                 build output; this directory is the document root
```

## Build

```bash
python3 tools/validate_content.py     # every content file matches the contract
python3 site/build.py                 # writes dist/
python3 tools/qa.py                   # link and structured-data checks
```

No dependencies beyond the Python standard library. The build takes under a second.

## Adding pages

1. Add keywords to `data/keywords-all.csv`.
2. `python3 pipeline/02_pagemap.py --in data/keywords-all.csv --out data/pagemap.json`
3. `python3 pipeline/025_enrich_pagemap.py`
4. Write `content/<slug>.json` for the new slugs, following `pipeline/WRITER-BRIEF.md`.
   `pipeline/03_generate.py` does this through the Batch API for about two cents a page.
5. Rebuild.

## Structured data

Every code page emits four JSON-LD blocks: `TechArticle`, `HowTo` (with per-step anchors and
an ISO-8601 total time), `FAQPage`, and `BreadcrumbList`. The answer block and fact strip are
marked `speakable`. This is the main lever for answer-engine visibility, and `tools/qa.py`
fails the build if any of it is malformed.

## Deployment

See `DEPLOY.md`. Short version: GitHub Actions builds `dist/` and pushes it to a `deploy`
branch whose root is the document root; Cloudways pulls that branch into `public_html`.

## Licensing and trademarks

Diagrams and written content in this repository are original work. Brand names are the
property of their owners and are used only to identify which appliance a page applies to.
No manufacturer imagery, service-manual artwork or copied text is included, and none should
be added: attribution does not make third-party product photography safe to use on a
commercial page.
