#!/usr/bin/env python3
"""
Step 1 - harvest reference material with crawl4ai. Costs zero Claude tokens.

Crawls the manufacturer support page and the top-ranking competitor pages for each
error code, strips them to clean markdown, and writes one JSON file per page into
research/. Step 3 feeds these to the model as grounding so it does not invent facts.

Run on your own machine:
    pip install crawl4ai && crawl4ai-setup
    python pipeline/01_harvest.py --pagemap data/pagemap.json --out research/

Notes
  - crawl4ai drives a real Chromium, so it renders JS-heavy support sites.
  - --concurrency 4 is polite. Raise it only for sites you own.
  - Already-harvested pages are skipped, so the script is resumable.
"""
import argparse, asyncio, json, pathlib, sys, time

def md_of(result):
    m = getattr(result, "markdown", None)
    if m is None:
        return ""
    for attr in ("fit_markdown", "raw_markdown"):
        v = getattr(m, attr, None)
        if isinstance(v, str) and v.strip():
            return v
    return m if isinstance(m, str) else str(m)

async def harvest(pagemap, outdir, concurrency, limit, max_chars):
    try:
        from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
    except ImportError:
        sys.exit("crawl4ai is not installed. Run: pip install crawl4ai && crawl4ai-setup")

    outdir.mkdir(parents=True, exist_ok=True)
    todo = [p for p in pagemap if not (outdir / f"{p['slug']}.json").exists()][:limit]
    if not todo:
        print("Nothing to harvest; every page already has a research file.")
        return

    print(f"Harvesting sources for {len(todo)} pages (concurrency {concurrency})")
    run_cfg = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, word_count_threshold=40,
                               excluded_tags=["nav", "footer", "header", "aside", "form"],
                               exclude_external_links=True, page_timeout=45000)
    sem = asyncio.Semaphore(concurrency)

    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        async def one(page):
            async with sem:
                sources = []
                for url in page.get("source_urls", []):
                    try:
                        r = await crawler.arun(url=url, config=run_cfg)
                        if getattr(r, "success", False):
                            text = md_of(r).strip()
                            if len(text) > 300:
                                sources.append({"url": url, "markdown": text[:max_chars]})
                    except Exception as e:
                        print(f"  ! {url}: {type(e).__name__}", file=sys.stderr)
                rec = {"slug": page["slug"], "brand": page["brand"],
                       "appliance": page["appliance"], "code": page["code"],
                       "harvested_at": time.strftime("%Y-%m-%d"), "sources": sources}
                (outdir / f"{page['slug']}.json").write_text(json.dumps(rec, indent=2))
                print(f"  {page['slug']}: {len(sources)} sources")
        await asyncio.gather(*(one(p) for p in todo))

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pagemap", default="data/pagemap.json")
    ap.add_argument("--out", default="research/")
    ap.add_argument("--concurrency", type=int, default=4)
    ap.add_argument("--limit", type=int, default=10**6)
    ap.add_argument("--max-chars", type=int, default=12000,
                    help="Per-source cap. Lower this to cut step-3 input token cost.")
    a = ap.parse_args()
    pm = json.loads(pathlib.Path(a.pagemap).read_text())
    asyncio.run(harvest(pm, pathlib.Path(a.out), a.concurrency, a.limit, a.max_chars))
