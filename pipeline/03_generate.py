#!/usr/bin/env python3
"""
Step 3 - generate the pages on the Anthropic API, outside any Claude Code session.

This is the step that costs money, and it is the step you want OUT of a chat session.
In a chat, the whole transcript is resent on every turn, so page 200 pays for pages
1-199 again. Here each page is one isolated request: it pays for its own tokens once.

    # See the bill before spending anything. Needs no API key.
    python pipeline/03_generate.py --estimate

    # Submit for real. 50% cheaper than live calls, returns within 24h (usually minutes).
    export ANTHROPIC_API_KEY=sk-ant-...
    python pipeline/03_generate.py --submit --model claude-haiku-5-5 --limit 20
    python pipeline/03_generate.py --collect <batch_id> --out content/
"""
import argparse, json, pathlib, sys, textwrap

# $ per million tokens. Cache-read figures Anthropic publishes per model; where it does not,
# this uses the usual 0.1x of base input and the estimator marks the row approximate.
PRICES = {
    "claude-haiku-5-5":  {"in": 0.10, "out": 0.50, "cache_read": 0.01, "exact_cache": False},
    "claude-sonnet-5-5": {"in": 2.00, "out": 10.00, "cache_read": 0.20, "exact_cache": True},
    "claude-opus-5-5":   {"in": 4.00, "out": 20.00, "cache_read": 0.20, "exact_cache": True},
    "claude-fable-5-1":  {"in": 10.00, "out": 50.00, "cache_read": 0.25, "exact_cache": True},
}
BATCH_DISCOUNT = 0.50
OUT_TOKENS_PER_PAGE = 2200   # ~1,200 words of structured JSON body

def approx_tokens(s: str) -> int:
    return max(1, int(len(s) / 3.6))

def build_user_prompt(page, research):
    sources = ""
    for i, s in enumerate(research.get("sources", []), 1):
        sources += f"\n\n--- SOURCE {i}: {s['url']} ---\n{s['markdown']}"
    secondary = ", ".join(page["secondary_keywords"][:10]) or "none"
    return textwrap.dedent(f"""\
        Write the error-code page for:

          Brand:      {page['brand']}
          Appliance:  {page['appliance']}
          Code:       {page['code'] or '(brand-wide list page)'}
          Page type:  {page['page_type']}
          URL:        {page['url']}

        Primary keyword: {page['primary_keyword']}
        Also answer these phrasings naturally in the body, never as a keyword list:
        {secondary}

        Reference material crawled from the manufacturer and from pages that currently
        rank. Use it for facts: what the code means, which parts are involved, what
        actually fixed it for people. Do not copy any sentence from it. Where sources
        disagree, say so. Where they are all vague, say the honest thing rather than
        inventing detail.{sources if sources else chr(10) + "(No reference material was harvested. Stay general and do not invent specifics.)"}
        """)

def load(pagemap_p, research_d, limit):
    pages = json.loads(pathlib.Path(pagemap_p).read_text())[:limit]
    research_d = pathlib.Path(research_d)
    out = []
    for p in pages:
        f = research_d / f"{p['slug']}.json"
        out.append((p, json.loads(f.read_text()) if f.exists() else {"sources": []}))
    return out

def session_cost(n, per_page_in, per_page_out, base_ctx, cap):
    """
    Model the cost of generating the same pages turn-by-turn inside a chat session.

    A chat is stateful: every turn resends the whole transcript, so page N pays to
    reread pages 1..N-1. Context grows by (prompt + answer) each turn until it hits
    the compaction ceiling, after which it stays flat at `cap`. That flat ceiling is
    the optimistic case and is what this returns.
    """
    total_in = grown = 0
    for _ in range(n):
        ctx = min(base_ctx + grown, cap)
        total_in += ctx + per_page_in
        grown += per_page_in + per_page_out
    return total_in, per_page_out * n


def estimate(jobs, system, schema_chars, assume_research=0, scale=None):
    n = len(jobs)
    sys_t = approx_tokens(system) + schema_chars // 4
    user_t = [approx_tokens(build_user_prompt(p, r)) for p, r in jobs]
    if assume_research:
        user_t = [t + assume_research for t in user_t]
    in_t = sum(user_t) + sys_t * n
    out_t = OUT_TOKENS_PER_PAGE * n
    harvested = sum(1 for _, r in jobs if r.get("sources"))

    print(f"\n  Pages:                 {n}")
    print(f"  With crawled research: {harvested}  ({n - harvested} would be written unsourced)")
    print(f"  Shared system+schema:  {sys_t:,} tokens, resent per request")
    print(f"  Input tokens total:    {in_t:,}")
    print(f"  Output tokens total:   {out_t:,}  (at {OUT_TOKENS_PER_PAGE:,}/page)\n")
    w = 20
    print(f"  {'model':<{w}} {'live':>10} {'batch -50%':>12} {'per page':>10}")
    print("  " + "-" * (w + 34))
    for m, pr in PRICES.items():
        live = in_t / 1e6 * pr["in"] + out_t / 1e6 * pr["out"]
        batch = live * BATCH_DISCOUNT
        print(f"  {m:<{w}} {'$%.2f' % live:>10} {'$%.2f' % batch:>12} {'$%.4f' % (batch / n):>10}")
    print("\n  Caching is not modelled: the shared prefix here is only "
          f"~{sys_t:,} tokens, at or under the minimum cacheable prefix on most models, "
          "and the per-page research text is unique so it can never be cached. The batch\n"
          "  discount is the reliable 50%; model choice is the other big lever.")

    # ---- the same work done turn-by-turn in a chat session, for contrast ----
    per_in = in_t // n
    sin, sout = session_cost(n, per_in, OUT_TOKENS_PER_PAGE,
                             base_ctx=20_000, cap=160_000)
    print(f"\n  Same {n} pages generated turn-by-turn in a chat session instead:")
    print(f"    input tokens:  {sin:,}   ({sin / in_t:.0f}x the batch pipeline)")
    print(f"    output tokens: {sout:,}")
    print(f"    {'model':<20} {'chat session':>14} {'batch API':>12} {'multiple':>10}")
    print("    " + "-" * 58)
    for m, pr in PRICES.items():
        chat = sin / 1e6 * pr["in"] + sout / 1e6 * pr["out"]
        batch = (in_t / 1e6 * pr["in"] + out_t / 1e6 * pr["out"]) * BATCH_DISCOUNT
        print(f"    {m:<20} {'$%.2f' % chat:>14} {'$%.2f' % batch:>12} {'%.0fx' % (chat / batch):>10}")
    print("    Assumes a 160k-token compaction ceiling, which is the generous case.")

    if scale:
        print(f"\n  Scaled to a larger site, batch API, same per-page token profile:")
        print(f"    {'pages':>7} " + " ".join(f"{m.replace('claude-',''):>16}" for m in PRICES))
        for npages in scale:
            row = f"    {npages:>7} "
            for m, pr in PRICES.items():
                c = (per_in * npages / 1e6 * pr["in"]
                     + OUT_TOKENS_PER_PAGE * npages / 1e6 * pr["out"]) * BATCH_DISCOUNT
                row += f" {'$%.2f' % c:>16}"
            print(row)

def submit(jobs, system, schema, model, effort):
    from anthropic import Anthropic
    from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
    from anthropic.types.messages.batch_create_params import Request
    client = Anthropic()

    out_cfg = {"effort": effort, "format": schema}
    kwargs = {}
    if model.startswith("claude-haiku"):
        kwargs["thinking"] = {"type": "disabled"}   # bulk writing gains nothing from thinking

    reqs = [
        Request(
            custom_id=p["slug"][:64],
            params=MessageCreateParamsNonStreaming(
                model=model, max_tokens=8000,
                system=[{"type": "text", "text": system,
                         "cache_control": {"type": "ephemeral"}}],
                output_config=out_cfg,
                messages=[{"role": "user", "content": build_user_prompt(p, r)}],
                **kwargs),
        ) for p, r in jobs
    ]
    batch = client.messages.batches.create(requests=reqs)
    print(f"submitted {len(reqs)} pages\nbatch id: {batch.id}\nstatus:   {batch.processing_status}")
    print(f"\ncollect with:\n  python pipeline/03_generate.py --collect {batch.id} --out content/")

def collect(batch_id, outdir):
    from anthropic import Anthropic
    client = Anthropic()
    b = client.messages.batches.retrieve(batch_id)
    if b.processing_status != "ended":
        print(f"status {b.processing_status}; not ready yet"); return
    outdir = pathlib.Path(outdir); outdir.mkdir(parents=True, exist_ok=True)
    ok = err = 0
    tin = tout = 0
    for res in client.messages.batches.results(batch_id):
        if res.result.type != "succeeded":
            print(f"  ! {res.custom_id}: {res.result.type}"); err += 1; continue
        msg = res.result.message
        tin += msg.usage.input_tokens; tout += msg.usage.output_tokens
        text = "".join(b.text for b in msg.content if b.type == "text")
        (outdir / f"{res.custom_id}.json").write_text(text)
        ok += 1
    print(f"wrote {ok} pages to {outdir}/ ({err} failed)")
    print(f"actual tokens: {tin:,} in / {tout:,} out")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pagemap", default="data/pagemap.json")
    ap.add_argument("--research", default="research/")
    ap.add_argument("--limit", type=int, default=10**6)
    ap.add_argument("--model", default="claude-haiku-5-5", choices=list(PRICES))
    ap.add_argument("--effort", default="low", choices=["low","medium","high"])
    ap.add_argument("--estimate", action="store_true")
    ap.add_argument("--assume-research", type=int, default=0, metavar="TOKENS",
                    help="Model N tokens of crawled research per page when research/ is "
                         "still empty. 8000 ~= three sources of 10k characters each.")
    ap.add_argument("--submit", action="store_true")
    ap.add_argument("--collect", metavar="BATCH_ID")
    ap.add_argument("--out", default="content/")
    a = ap.parse_args()

    if a.collect:
        collect(a.collect, a.out); sys.exit()

    root = pathlib.Path(__file__).parent
    system = (root / "prompts/system.md").read_text()
    schema_raw = (root / "prompts/page_schema.json").read_text()
    schema = json.loads(schema_raw)
    jobs = load(a.pagemap, a.research, a.limit)

    if a.submit:
        submit(jobs, system, schema, a.model, a.effort)
    else:
        estimate(jobs, system, len(schema_raw), a.assume_research,
                 scale=[177, 500, 1000, 2000])
