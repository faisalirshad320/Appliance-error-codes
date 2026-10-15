#!/usr/bin/env python3
"""Fail the build if any content file breaks the page contract."""
import sys, json, glob, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT/"site"/"lib"))
import schema

files = sorted(glob.glob(str(ROOT/"content"/"*.json")))
bad = 0
for f in files:
    name = pathlib.Path(f).stem
    try:
        d = json.loads(pathlib.Path(f).read_text())
    except json.JSONDecodeError as e:
        print(f"FAIL {name}: invalid JSON — {e}"); bad += 1; continue
    errs = schema.validate(d, name)
    if errs:
        bad += 1
        print(f"FAIL {name}")
        for e in errs: print("      ", e)
print(f"\n{len(files)-bad}/{len(files)} content files valid")
sys.exit(1 if bad else 0)
