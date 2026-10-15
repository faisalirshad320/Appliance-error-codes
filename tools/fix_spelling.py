#!/usr/bin/env python3
"""
Convert British spellings to American across content files.

Pure substitution of whole words, case preserved. Safe to run repeatedly. Separate from
the linter so the linter stays read-only and CI-friendly: this one edits, that one reports.
"""
import json, glob, pathlib, re, sys

PAIRS = {
    "behaviour":"behavior","colour":"color","centre":"center","centred":"centered",
    "metre":"meter","metres":"meters","millimetre":"millimeter","millimetres":"millimeters",
    "centimetre":"centimeter","centimetres":"centimeters","litre":"liter","litres":"liters",
    "grey":"gray","fibre":"fiber","odour":"odor","odours":"odors","moulded":"molded",
    "mould":"mold","authorised":"authorized","recognise":"recognize",
    "recognised":"recognized","programme":"programme_KEEP","organised":"organized",
    "favourite":"favorite","neighbour":"neighbor","practise":"practice",
}
# "programme" means a wash cycle on European machines and some writers use it deliberately;
# American English for that sense is "program", so convert it but keep the word.
PAIRS["programme"] = "program"
PAIRS["programmes"] = "programs"

def match_case(src, dst):
    if src.isupper(): return dst.upper()
    if src[0].isupper(): return dst.capitalize()
    return dst

def main():
    changed = []
    for f in sorted(glob.glob(str(pathlib.Path(__file__).parent.parent/"content"/"*.json"))):
        p = pathlib.Path(f)
        text = p.read_text()
        original = text
        counts = {}
        for br, us in PAIRS.items():
            pat = re.compile(rf"\b{br}\b", re.IGNORECASE)
            n = len(pat.findall(text))
            if n:
                text = pat.sub(lambda m: match_case(m.group(0), us), text)
                counts[f"{br}->{us}"] = n
        if text != original:
            json.loads(text)                      # never write syntactically broken JSON
            p.write_text(text)
            changed.append(f"{p.stem}: " + ", ".join(f"{k} x{v}" for k, v in counts.items()))
    print(f"updated {len(changed)} file(s)")
    for c in changed[:25]: print("   ", c)
    if len(changed) > 25: print(f"    ... and {len(changed)-25} more")
    return 0

if __name__ == "__main__":
    sys.exit(main())
