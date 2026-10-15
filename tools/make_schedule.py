#!/usr/bin/env python3
"""
Generate pipeline/release-schedule.json: which pages go live, and how long after launch.

The schedule stores DAY OFFSETS FROM LAUNCH, not calendar dates. The clock starts at
`launch_date`, so a delay in connecting the host shifts the whole run rather than
collapsing several waves onto the first day the site is reachable.

Ordering is round-robin across brands, each brand's own pages in descending search
volume. Two reasons. Round-robin keeps any single wave from being twenty pages of one
brand, which is what a scraped dump looks like. Volume-descending inside a brand gives
the pages worth the most the longest time to age, and nothing ranks in month one anyway,
so there is no early win being traded away.

    python3 tools/make_schedule.py                      # regenerate, keep launch date
    python3 tools/make_schedule.py --launch 2026-11-01  # re-anchor the whole run
"""
import argparse, collections, datetime, hashlib, json, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "pipeline" / "release-schedule.json"

SEED_SIZE = 16      # launch-day wave: broad enough that the hubs are not one brand deep
WAVE_SIZE = 24      # every wave after that
BASE_GAP = 10       # days between waves, before jitter


def gap_for(wave):
    """9, 10 or 11 days, decided by the wave number so the file regenerates identically.

    A strict ten-day metronome is itself a footprint. This keeps the average at ten
    while the actual dates stay slightly irregular.
    """
    h = int(hashlib.sha256(f"wave-{wave}".encode()).hexdigest(), 16)
    return BASE_GAP + (h % 3) - 1


def order_pages(pages):
    """Round-robin across brands, each brand sorted by volume descending."""
    by_brand = collections.defaultdict(list)
    for p in pages:
        by_brand[p["brand"]].append(p)
    for group in by_brand.values():
        group.sort(key=lambda p: (-p["cluster_volume"], p["slug"]))

    # Busiest brands first, so each rotation leads with the pages that matter most.
    brands = sorted(by_brand, key=lambda b: -sum(p["cluster_volume"] for p in by_brand[b]))
    out, cursor = [], 0
    while len(out) < len(pages):
        progressed = False
        for b in brands:
            if cursor < len(by_brand[b]):
                out.append(by_brand[b][cursor])
                progressed = True
        if not progressed:
            break
        cursor += 1
    return out


def build_waves(ordered):
    sizes, remaining = [SEED_SIZE], len(ordered) - SEED_SIZE
    while remaining > 0:
        sizes.append(min(WAVE_SIZE, remaining))
        remaining -= sizes[-1]

    waves, start, offset = [], 0, 0
    for n, size in enumerate(sizes):
        if n:
            offset += gap_for(n)
        chunk = ordered[start:start + size]
        waves.append({
            "wave": n,
            "offset_days": offset,
            "pages": len(chunk),
            "volume": sum(p["cluster_volume"] for p in chunk),
            "slugs": [p["slug"] for p in chunk],
        })
        start += size
    return waves


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--launch", help="YYYY-MM-DD the site goes live; defaults to today "
                                     "on a first run, otherwise keeps the current value")
    args = ap.parse_args()

    pages = json.loads((ROOT / "data" / "pagemap.json").read_text())
    waves = build_waves(order_pages(pages))

    launch = args.launch
    if not launch and OUT.exists():
        launch = json.loads(OUT.read_text()).get("launch_date")
    launch = launch or datetime.date.today().isoformat()
    datetime.date.fromisoformat(launch)   # reject a malformed date here, not at build time

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "launch_date": launch,
        "generated": datetime.date.today().isoformat(),
        "note": "Offsets are days after launch_date. Re-anchor with "
                "tools/make_schedule.py --launch YYYY-MM-DD if the site goes live later.",
        "seed_size": SEED_SIZE,
        "wave_size": WAVE_SIZE,
        "waves": waves,
    }, indent=2) + "\n")

    d0 = datetime.date.fromisoformat(launch)
    last = waves[-1]
    print(f"{len(waves)} waves, {sum(w['pages'] for w in waves)} pages, "
          f"launch {launch} -> {d0 + datetime.timedelta(days=last['offset_days'])}")
    for w in waves:
        print(f"  wave {w['wave']:>2}  day {w['offset_days']:>3}  "
              f"{d0 + datetime.timedelta(days=w['offset_days'])}  "
              f"{w['pages']:>2} pages  {w['volume']:>7,}/mo")


if __name__ == "__main__":
    main()
