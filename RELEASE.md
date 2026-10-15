# How the site publishes itself

252 pages do not go live at once. They go out in 11 waves over about three and a half
months, and the whole thing runs on GitHub's servers without anyone's machine being on.

```
python3 tools/release_status.py          # where the drip has got to
python3 tools/release_status.py --on 2026-12-01
```

## Why not publish all of it on day one

A brand-new domain with no backlinks and no history that publishes 252 pages in an
afternoon is the exact shape of the thing recent core updates are built to catch. The
research behind this niche found a comparable site reach 61,000 monthly visits in seven
months and then lose 62 percent of it over the next three. Gradual publication is not a
guarantee against that, but a standing start into 252 pages is a good way to invite it.

The schedule below averages about three pages a day. That is a pace a small team could
plausibly sustain, which is the point.

## The schedule

| Wave | Day | Pages | Why it is where it is |
|---|---|---|---|
| 0 | 0 | 16 | Seed. One page from each of 16 brands, across 7 appliance types |
| 1–9 | 10 → 90 | 24 each | Round-robin across brands, highest volume first |
| 10 | 101 | 20 | The tail |

Two decisions are worth knowing about.

**Round-robin across brands.** Each wave contains pages from many brands rather than
completing one brand at a time. Twenty-four Samsung pages landing in one day looks like a
scrape; twenty-four pages spread over sixteen brands looks like editorial work. It also
means every brand hub has something in it from the first day.

**Highest volume first, within each brand.** The valuable pages go out early so they get
the longest time to age. Nothing ranks in month one regardless, so there is no early win
being given up by not leading with the easy long-tail.

**The gaps are 9, 10 or 11 days, not a flat 10.** A strict metronome is itself a
footprint. The jitter is derived from the wave number, so regenerating the file produces
the same dates rather than reshuffling them.

## Why a missed day costs nothing

The gate is a date, not an event. `site/build.py` asks "which waves are due as of today?"
and builds exactly those. It does not ask "did a job fire on the right day?"

So if the daily workflow is delayed, skipped, or does not run for a week, the next run
publishes precisely what should be live by then. Nothing is lost and nothing is
double-published. For the same reason catching up can never run *ahead*: a run on day 35
publishes waves 0–3 because that is what day 35 is owed, no matter how many runs were
missed before it.

This is also why publishing does not depend on this repository's Claude session, your PC,
or anything you have to remember to do.

## Changing the pacing

Everything lives in `pipeline/release-schedule.json`. Edit the constants at the top of
`tools/make_schedule.py` and regenerate:

```bash
# slower: 20 pages every 2 weeks
# (edit WAVE_SIZE = 20 and BASE_GAP = 14 first)
python3 tools/make_schedule.py
```

To push the whole run back — say the host is not connected until November:

```bash
python3 tools/make_schedule.py --launch 2026-11-05
```

Re-anchoring is the right move if the site is not reachable on launch day. Without it the
first run publishes several waves at once, because by then they are genuinely due.

`tools/check_schedule.py` runs in CI and fails the build if the schedule and the page map
disagree. That matters because a page in no wave is never published, and nothing else
would tell you.

## Adding pages later

1. Write the content file and add the page to `data/pagemap.json`.
2. Run `python3 tools/make_schedule.py` — it keeps the existing launch date and places
   the new pages in the ordering.
3. Commit. CI checks it; the daily workflow releases it when its wave comes up.

## The one thing that can quietly stop

GitHub disables scheduled workflows in a repository with no activity for 60 days. The
waves are at most 11 days apart and each publishes a commit, so in normal operation this
never triggers. If the drip finishes and the repository then goes quiet, the schedule
will eventually be disabled — harmless at that point, since everything is already live,
but worth knowing before you add new pages months later. GitHub emails the repository
owner before it does this, and re-enabling is one button in the Actions tab.
