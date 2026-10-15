#!/usr/bin/env python3
"""
Trim presentational fields to their limits before validation.

Title and meta-description length are presentation constraints, not content ones: a meta
description that runs 170 characters says the right thing, it just gets cut off in a search
result. Trimming it at a sentence or word boundary is a formatting fix, so it is done
mechanically and reported, rather than failing a build over ten characters.

Anything that would change meaning — causes, steps, the escalation section — is never touched
here. Those are content problems and validate_content.py is right to fail on them.
"""
import json, glob, pathlib, sys, re

TITLE_MAX, META_MAX = 65, 155

def trim(text, limit):
    """Cut at the last sentence end that fits; failing that, the last whole word."""
    if len(text) <= limit:
        return text, False
    window = text[:limit + 1]
    # A sentence boundary is the nicest cut, but only when it is close to the limit.
    # Falling back to one far earlier throws away usable characters: a 96-character
    # description wastes half the space a search result would have given it.
    for end in (". ", "? ", "! "):
        i = window.rfind(end)
        if i >= limit * 0.88:
            return text[:i + 1].strip(), True
    if text[:limit].rstrip().endswith((".", "?", "!")):
        return text[:limit].rstrip(), True
    i = window.rfind(" ")
    cut = text[:i if i > 0 else limit].rstrip(" ,;:-")
    return cut, True

def main():
    changed = []
    for f in sorted(glob.glob(str(pathlib.Path(__file__).parent.parent/"content"/"*.json"))):
        p = pathlib.Path(f)
        try:
            d = json.loads(p.read_text())
        except json.JSONDecodeError:
            continue                      # validate_content.py reports this properly
        edits = []
        for field, limit in (("title", TITLE_MAX), ("meta_description", META_MAX)):
            if field in d and isinstance(d[field], str):
                new, did = trim(d[field], limit)
                if did:
                    edits.append(f"{field} {len(d[field])}->{len(new)}")
                    d[field] = new
        if edits:
            p.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n")
            changed.append(f"{p.stem}: {', '.join(edits)}")
    if changed:
        print(f"normalized {len(changed)} file(s):")
        for c in changed: print("   ", c)
    else:
        print("nothing to normalize")
    return 0

if __name__ == "__main__":
    sys.exit(main())
