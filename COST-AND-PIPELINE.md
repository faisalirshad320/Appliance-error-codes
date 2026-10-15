# Building the pages without burning Claude tokens

Date: 2026-10-15
Short answer: generating all 177 pages costs **$0.18 to $18 one time**, depending on model, and
**none of it has to come out of your Claude Code allowance**. Build the pages with the scripts in
`pipeline/`, run them against the Anthropic API from your own machine, and this chat is only ever
used to design the pipeline, not to run it.

## 1. crawl4ai

crawl4ai is **not** installed on "this pc". This session runs in a remote Linux container in
Anthropic's cloud, not on your computer, and it starts with a fresh checkout and nothing else.

I installed crawl4ai here (0.8.x, Python 3.13) and it runs: the library imports, Chromium
launches after relinking the container's pre-installed browser to the revision Playwright
expects. What it cannot do here is reach the sites we need. Every request to `bosch-home.com`,
`ifixit.com` and `hoffmannbros.com` came back `ERR_TUNNEL_CONNECTION_FAILED` because this
environment's network policy denies those hosts.

You can change that: open the cloud environment menu in the session title bar, choose Edit, and
either raise Network access to a broader level or add those hosts under Allowed domains, leaving
"Allow package managers" ticked. Steps: https://code.claude.com/docs/en/cloud-environments#network-access

Either way, **the crawl belongs on your PC**, because that is free. `pipeline/01_harvest.py` is
written to run there. It costs zero Claude tokens: it is a browser fetching pages and saving
markdown, with no model in the loop.

```bash
pip install crawl4ai && crawl4ai-setup
python pipeline/01_harvest.py --pagemap data/pagemap.json --out research/
```

## 2. What the pages actually cost

Measured with `pipeline/03_generate.py --estimate`, not guessed. 177 pages, each with about
8,000 tokens of crawled reference material fed in as grounding and about 2,200 tokens of
structured output coming back.

| Model | Live API | Batch API (-50%) | Per page |
|---|---|---|---|
| Haiku 5.5 | $0.36 | **$0.18** | $0.0010 |
| Sonnet 5.5 | $7.28 | **$3.64** | $0.0206 |
| Opus 5.5 | $14.57 | **$7.28** | $0.0411 |
| Fable 5.1 | $36.41 | **$18.21** | $0.1029 |

Scaled up, still on the Batch API:

| Pages | Haiku 5.5 | Sonnet 5.5 | Opus 5.5 |
|---|---|---|---|
| 177 (every page the keyword data supports today) | $0.18 | $3.64 | $7.28 |
| 500 | $0.51 | $10.29 | $20.57 |
| 1,000 | $1.03 | $20.57 | $41.14 |
| 2,000 | $2.06 | $41.14 | $82.29 |

**Recommendation: Sonnet 5.5 on the Batch API, about $4 for the whole site.** Haiku is twenty
times cheaper but these pages are the product; the difference between a page that reads like a
technician wrote it and one that reads like filler is the entire business. Opus doubles the
Sonnet cost for a smaller gain on writing this formulaic. Reprice with `--model` before you
commit to one, and generate 20 pages on each of two models first and read them side by side.

## 3. Why not just do it in this chat

Because a chat is stateful and the API is not. Every turn in a conversation resends the whole
transcript, so page 150 pays again to reread pages 1 through 149. One isolated API request per
page pays for that page once.

The estimator models both. Same 177 pages, same model, same output:

| Model | Generated turn-by-turn in chat | Batch API | Multiple |
|---|---|---|---|
| Haiku 5.5 | $3.11 | $0.18 | 17x |
| Sonnet 5.5 | $62.12 | $3.64 | 17x |
| Opus 5.5 | $124.23 | $7.28 | 17x |
| Fable 5.1 | $310.58 | $18.21 | 17x |

That 17x is the generous case. It assumes context gets compacted at 160k tokens and stays flat
after that; without compaction the growth is quadratic and the multiple is far worse. It also
ignores that chat turns carry the Claude Code system prompt and tool definitions on every single
request, and that compaction loses detail, so quality drifts as the run goes on.

The other half of the answer is which wallet pays. Chat turns draw on your Claude Code plan
allowance. Batch API calls are billed per token against API credit. Moving generation to the API
means a 1,000-page build costs about $21 of credit and **zero** of your plan allowance.

## 4. The pipeline

Four steps. Only step 3 costs money, and it runs headless on your machine.

| Step | Script | Claude tokens | What it does |
|---|---|---|---|
| 1 | `pipeline/01_harvest.py` | none | crawl4ai pulls the manufacturer page and the pages currently ranking, saves clean markdown to `research/` |
| 2 | `pipeline/02_pagemap.py` | none | collapses 409 keywords into 177 unique pages, picks the primary keyword, sums cluster volume, orders by demand |
| 3 | `pipeline/03_generate.py` | API credit only | submits one isolated Batch request per page, returns validated JSON |
| 4 | your site build | none | renders the JSON into pages with your own template and schema markup |

Step 2 is already run. `data/pagemap.json` holds the 177 pages: 144 single-code pages and 33
brand list pages, covering 196,670 searches a month. The ten biggest:

| Volume/mo | URL |
|---|---|
| 18,150 | `/samsung/washer/4c-error-code/` |
| 17,450 | `/lg/dryer/d80-error-code/` |
| 12,550 | `/lg/washer/ue-error-code/` |
| 9,800 | `/lg/washer/oe-error-code/` |
| 8,100 | `/samsung/dishwasher/lc-error-code/` |
| 6,400 | `/lg/dishwasher/ae-error-code/` |
| 6,150 | `/samsung/washer/sc-error-code/` |
| 5,950 | `/samsung/washer/sud-error-code/` |
| 5,750 | `/whirlpool/washer/error-codes/` |
| 5,700 | `/bosch/dishwasher/e15-error-code/` |

Run it:

```bash
python pipeline/02_pagemap.py                       # done, rerun when you add keywords
python pipeline/01_harvest.py                       # on your PC, free, slowest step
python pipeline/03_generate.py --estimate --assume-research 8000
export ANTHROPIC_API_KEY=sk-ant-...
python pipeline/03_generate.py --submit --model claude-sonnet-5-5 --limit 20
python pipeline/03_generate.py --collect <batch_id> --out content/
```

Start with `--limit 20`. Read all twenty before spending the other $3.

## 5. The thing that actually costs you, and it is not tokens

Generation is the cheap part. At $4 for 177 pages, cost is not the constraint on this project and
should not drive any decision. The constraint is that publishing 177 machine-written pages at
once is the exact pattern Google's recent core updates target, and the niche validation already
has the evidence: beaconsaves.com went from 230 to 61,386 monthly visits in seven months on this
model, then lost 62% of it in the three months after.

So spend the money you saved on the parts a model cannot produce:

- **Publish in waves.** 20 to 30 pages a month, highest volume first. A site that goes from 0 to
  1,000 pages in a fortnight looks like exactly what it is.
- **Put something first-hand on every page.** Your own photo of the code on the display, your own
  photo of the part. This is what the ranking low-DR sites have that the dead ones did not, and
  what AI Overviews cite.
- **Have someone who repairs appliances read them.** A technician spotting one wrong part name
  per page is worth more than any model upgrade.
- **Build the lead path before the traffic.** The niche report found repair-lead generation is
  where the money is, not display ads. Ship the "book a technician" and "order this part" paths
  with the first twenty pages.

The pipeline makes pages cost nothing. That makes it tempting to publish a thousand. Do not.
