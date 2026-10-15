#!/usr/bin/env python3
"""
Enforce the writing rules in pipeline/WRITER-BRIEF.md that the schema cannot express.

The schema checks shape: are the fields present, are the types right, are there enough
causes. It cannot check whether a page says "simply" or opens with "you're not alone", and
relying on each writer to self-police that produced exactly the drift you would expect: a
dozen pages carrying banned vocabulary while every one of them passed validation.

So the rules live here instead, and CI runs them. Everything flagged is a real rule from the
brief, not a style preference invented in this file.
"""
import json, glob, pathlib, re, sys

BANNED = {
    # Only the condescending instructional use: "simply unplug it". The adverbial sense
    # ("the dryer simply stopped", "fair to call simply because") is ordinary English and
    # flagging it would push writers into worse prose to satisfy a linter.
    (r"\bsimply (remove|press|check|clean|turn|open|close|pull|push|unplug|replace|run|"
     r"hold|lift|slide|unscrew|disconnect|reconnect|reset|wipe|clear|drain|empty|call|"
     r"follow|try|use|put|take|set|swap|order|fit)\b"):
        "'simply <do X>' — if it were simple they would not be searching",
    r"\bdon'?t worry\b": "says \"don't worry\" — reassurance instead of an answer",
    r"\byou'?re not alone\b": "opens with \"you're not alone\" filler",
    r"\bin today'?s world\b": "'in today's world' filler",
    r"\brest assured\b": "'rest assured' filler",
    r"\bneedless to say\b": "'needless to say' — then do not say it",
    r"\bit is important to note\b": "'it is important to note' padding",
    r"\bsimple as that\b": "'simple as that'",
    r"\bvoila\b|\bvoilà\b": "'voila'",
}
# American spelling is specified. "anticlockwise" is allowed: the exemplar uses it and it
# is unambiguous about which way the cap turns, which is the whole point of the sentence.
BRITISH = {
    r"\bbehaviour\b": "behavior", r"\bcolour\b": "color", r"\bcentre\b": "center",
    r"\bcentred\b": "centered", r"\bmetre\b": "meter", r"\bmetres\b": "meters",
    r"\bmillimetres\b": "millimeters", r"\bcentimetres\b": "centimeters",
    r"\blitre\b": "liter", r"\blitres\b": "liters", r"\bgrey\b": "gray",
    r"\bfibre\b": "fiber", r"\bodour\b": "odor", r"\bmoulded\b": "molded",
    r"\bauthorised\b": "authorized", r"\brecognise\b": "recognize",
    r"\bprogramme\b": "program",
}
TEXT_FIELDS = ["title", "meta_description", "h1", "answer", "still_showing",
               "when_to_call", "reset_procedure", "model_notes", "safety_warning"]

def page_text(d):
    """Every piece of prose on the page, as (where, text) pairs."""
    out = [(f, d[f]) for f in TEXT_FIELDS if isinstance(d.get(f), str) and d[f]]
    for i, c in enumerate(d.get("causes", [])):
        out += [(f"causes[{i}].cause", c.get("cause", "")),
                (f"causes[{i}].confirm", c.get("confirm", ""))]
    for i, s in enumerate(d.get("steps", [])):
        out += [(f"steps[{i}].name", s.get("name", "")),
                (f"steps[{i}].detail", s.get("detail", "")),
                (f"steps[{i}].warning", s.get("warning") or "")]
    for i, q in enumerate(d.get("faqs", [])):
        out += [(f"faqs[{i}].q", q.get("q", "")), (f"faqs[{i}].a", q.get("a", ""))]
    for i, p in enumerate(d.get("parts", [])):
        out += [(f"parts[{i}].note", p.get("note") or "")]
    return [(w, t) for w, t in out if t]

def check(slug, d):
    problems = []
    for where, text in page_text(d):
        low = text.lower()
        for pat, why in BANNED.items():
            if re.search(pat, low):
                problems.append(f"{where}: {why}")
        for pat, us in BRITISH.items():
            if re.search(pat, low):
                problems.append(f"{where}: British spelling, use '{us}'")
        if "!" in text and where != "safety_warning":
            problems.append(f"{where}: exclamation mark")

    t = d.get("title", "")
    if len(t) > 65:
        problems.append(f"title: {len(t)} chars, brief limit is 65")
    m = d.get("meta_description", "")
    if m and not (110 <= len(m) <= 155):
        problems.append(f"meta_description: {len(m)} chars, brief range is 110-155")
    if m and not m.rstrip().endswith((".", "!", "?")):
        problems.append("meta_description: does not end on a complete sentence")
    if len(d.get("h1", "")) > 80:
        problems.append(f"h1: {len(d['h1'])} chars, brief limit is 80")

    most = [c for c in d.get("causes", []) if c.get("frequency") == "most cases"]
    if len(most) > 2:
        problems.append(f"causes: {len(most)} marked 'most cases', brief allows at most 2")

    for i, q in enumerate(d.get("faqs", [])):
        n = len(q.get("a", "").split())
        if not (35 <= n <= 90):
            problems.append(f"faqs[{i}].a: {n} words, brief asks for 40-80")

    for i, s in enumerate(d.get("steps", [])):
        if len(s.get("detail", "")) < 40:
            problems.append(f"steps[{i}].detail: {len(s.get('detail',''))} chars, too thin")
    return problems

def main():
    files = sorted(glob.glob(str(pathlib.Path(__file__).parent.parent/"content"/"*.json")))
    total, bad = 0, 0
    for f in files:
        slug = pathlib.Path(f).stem
        try:
            d = json.loads(pathlib.Path(f).read_text())
        except json.JSONDecodeError:
            continue
        probs = check(slug, d)
        if probs:
            bad += 1; total += len(probs)
            print(f"{slug}")
            for p in probs: print("      ", p)
    print(f"\n{len(files)-bad}/{len(files)} pages clean, {total} prose issue(s)")
    return 1 if bad else 0

if __name__ == "__main__":
    sys.exit(main())
