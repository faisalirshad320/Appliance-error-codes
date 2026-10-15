#!/usr/bin/env python3
"""
Where the drip has got to. Read-only; safe to run any time.

    python3 tools/release_status.py
    python3 tools/release_status.py --on 2026-12-01    # what will be live that day
"""
import argparse, datetime, json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "site"))
import importlib.util
_spec = importlib.util.spec_from_file_location("build", ROOT / "site" / "build.py")
build = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(build)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--on", help="YYYY-MM-DD to evaluate instead of today")
    args = ap.parse_args()
    today = datetime.date.fromisoformat(args.on) if args.on else datetime.date.today()

    sched = json.loads((ROOT / "pipeline" / "release-schedule.json").read_text())
    launch = datetime.date.fromisoformat(sched["launch_date"])
    pm = {p["slug"]: p for p in json.loads((ROOT / "data" / "pagemap.json").read_text())}
    due, n, total = build.released(today)

    live_vol = sum(pm[s]["cluster_volume"] for s in due if s in pm)
    all_vol = sum(p["cluster_volume"] for p in pm.values())

    print(f"as of {today}   (launch {launch}, day {(today - launch).days})")
    print(f"waves live     {n}/{total}")
    print(f"pages live     {len(due)}/{len(pm)}  ({100 * len(due) // len(pm)}%)")
    print(f"demand live    {live_vol:,}/{all_vol:,} searches/mo "
          f"({100 * live_vol // all_vol}%)\n")

    for w in sched["waves"]:
        d = launch + datetime.timedelta(days=w["offset_days"])
        if d <= today:
            mark, when = "live", f"{d}"
        else:
            mark, when = "    ", f"{d}  (in {(d - today).days}d)"
        print(f"  [{mark}] wave {w['wave']:>2}  {w['pages']:>2} pages  "
              f"{w['volume']:>7,}/mo   {when}")

    nxt = next((w for w in sched["waves"]
                if launch + datetime.timedelta(days=w["offset_days"]) > today), None)
    print()
    if nxt:
        d = launch + datetime.timedelta(days=nxt["offset_days"])
        print(f"next: wave {nxt['wave']} on {d}, {nxt['pages']} pages "
              f"({(d - today).days} days away)")
        print("sample:", ", ".join(nxt["slugs"][:5]))
    else:
        print("every wave is live; the drip is finished.")


if __name__ == "__main__":
    main()
