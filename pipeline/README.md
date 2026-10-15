# pipeline/

Four steps that turn a keyword list into finished page content. Only step 3 spends money,
and none of it spends Claude Code plan allowance. Full costing in `../COST-AND-PIPELINE.md`.

| File | Runs where | Cost |
|---|---|---|
| `01_harvest.py` | your PC (needs `pip install crawl4ai && crawl4ai-setup`) | free |
| `02_pagemap.py` | anywhere, pure Python | free |
| `03_generate.py` | anywhere with `ANTHROPIC_API_KEY` | API credit, ~$4 for 177 pages on Sonnet 5.5 |
| `prompts/system.md` | the writing rules the model follows | - |
| `prompts/page_schema.json` | the JSON structure every page comes back in | - |

Edit `prompts/system.md` first. It is the only lever that changes how the pages read, it costs
nothing to change, and a bad version wastes the whole batch. Generate 20 pages, read them, edit
the prompt, regenerate those same 20. Repeat until they are right, then run the rest.

```bash
python 02_pagemap.py                                       # 409 keywords -> 177 pages
python 01_harvest.py --limit 20                            # on your PC
python 03_generate.py --estimate --assume-research 8000    # see the bill, no key needed
python 03_generate.py --submit --model claude-sonnet-5-5 --limit 20
python 03_generate.py --collect <batch_id> --out ../content/
```

`source_urls` in `data/pagemap.json` is empty. Fill it per page with the manufacturer support
URL and two or three currently-ranking pages before running step 1, otherwise there is nothing
to crawl and the model writes unsourced, which is how wrong part names get published.
