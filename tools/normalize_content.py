#!/usr/bin/env python3
"""
Trim presentational fields to their limits before validation.

Title and meta-description length are presentation constraints, not content ones: a meta
description that runs 170 characters says the right thing, it just gets cut off in a search
result. Trimming it is a formatting fix, so it is done mechanically and reported rather than
failing a build over ten characters.

The one rule that matters: never cut mid-sentence. A description ending "...or a disposal
knockout plug left in" is user-facing search text and reads as broken. So this drops whole
trailing sentences, and when not even the first sentence fits it refuses to guess and flags
the page for a human rewrite instead of mangling it.

Fields that carry meaning — causes, steps, the escalation section — are never touched here.
Those are content problems and validate_content.py is right to fail on them.
"""
import json, glob, pathlib, sys, re

TITLE_MAX, META_MAX = 65, 155
# Below this a description is complete but wastes most of the snippet a search result
# would have given it. Reported, not auto-changed: padding it would be worse.
META_SHORT = 110
SENTENCE = re.compile(r'(?<=[.!?])\s+')

def trim_sentences(text, limit):
    """
    Keep as many whole sentences as fit. Returns (result, changed, needs_rewrite).
    needs_rewrite is True when the first sentence alone is over the limit, because any
    cut there would land mid-sentence.
    """
    text = text.strip()
    if len(text) <= limit:
        return text, False, False
    parts = [p for p in SENTENCE.split(text) if p.strip()]
    kept = []
    for part in parts:
        candidate = " ".join(kept + [part])
        if len(candidate) > limit:
            break
        kept.append(part)
    if kept:
        return " ".join(kept).strip(), True, False
    return text, False, True

def trim_title(text, limit):
    """Titles are fragments, not sentences, so a word boundary is the right cut here."""
    text = text.strip()
    if len(text) <= limit:
        return text, False
    cut = text[:limit + 1]
    i = cut.rfind(" ")
    return text[:i if i > 0 else limit].rstrip(" ,;:-—"), True

def main():
    changed, needs_rewrite, short = [], [], []
    for f in sorted(glob.glob(str(pathlib.Path(__file__).parent.parent/"content"/"*.json"))):
        p = pathlib.Path(f)
        try:
            d = json.loads(p.read_text())
        except json.JSONDecodeError:
            continue                      # validate_content.py reports this properly
        edits = []

        if isinstance(d.get("title"), str):
            new, did = trim_title(d["title"], TITLE_MAX)
            if did:
                edits.append(f"title {len(d['title'])}->{len(new)}")
                d["title"] = new

        if isinstance(d.get("meta_description"), str):
            new, did, rewrite = trim_sentences(d["meta_description"], META_MAX)
            if rewrite:
                needs_rewrite.append(
                    f"{p.stem}: first sentence is {len(d['meta_description'].split('. ')[0])} "
                    f"chars, over the {META_MAX} limit on its own — rewrite it by hand")
            elif did:
                edits.append(f"meta_description {len(d['meta_description'])}->{len(new)}")
                d["meta_description"] = new

        if edits:
            p.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n")
            changed.append(f"{p.stem}: {', '.join(edits)}")
        m = d.get("meta_description", "")
        if isinstance(m, str) and 0 < len(m) < META_SHORT:
            short.append(f"{p.stem}: {len(m)} chars")

    if changed:
        print(f"normalized {len(changed)} file(s):")
        for c in changed: print("   ", c)
    else:
        print("nothing to normalize")
    if short:
        print(f"\n{len(short)} description(s) under {META_SHORT} chars, worth lengthening:")
        for x in short: print("   ", x)
    if needs_rewrite:
        print(f"\n{len(needs_rewrite)} file(s) need a human rewrite, not a trim:")
        for n in needs_rewrite: print("   ", n)
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
