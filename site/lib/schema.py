"""The contract every generated page must satisfy. Validated before a page is rendered."""

DIAGRAM_KINDS = ["washer-drain-filter","washer-inlet-valve","washer-unbalanced-load",
    "washer-drain-pump","washer-door-latch","dryer-vent-path","dryer-thermistor",
    "dishwasher-sump-float","dishwasher-drain","control-board","water-supply",
    "refrigerator-sensor","generic-reset"]

PAGE_SCHEMA = {
  "type":"object","additionalProperties":False,
  "required":["title","meta_description","h1","answer","severity","can_diy","time_estimate",
              "cost_estimate","causes","steps","still_showing","parts","when_to_call",
              "faqs","diagram","sources"],
  "properties":{
    "title":{"type":"string","maxLength":65},
    "meta_description":{"type":"string","maxLength":158},
    "h1":{"type":"string","maxLength":80},
    "answer":{"type":"string","description":"2-4 sentences. What the code means and the single likeliest fix. Written to be lifted whole into an AI Overview or featured snippet."},
    "severity":{"enum":["minor","moderate","serious","stop-using-it"]},
    "can_diy":{"enum":["yes","usually","sometimes","no"]},
    "time_estimate":{"type":"string"},
    "cost_estimate":{"type":"object","additionalProperties":False,
      "required":["diy","technician"],
      "properties":{"diy":{"type":"string"},"technician":{"type":"string"}}},
    "safety_warning":{"type":["string","null"],"description":"Mains voltage, gas or sealed refrigerant. null when none applies."},
    "causes":{"type":"array","minItems":2,"maxItems":7,"items":{
      "type":"object","additionalProperties":False,
      "required":["cause","frequency","confirm"],
      "properties":{"cause":{"type":"string"},
        "frequency":{"enum":["most cases","common","occasional","rare"]},
        "confirm":{"type":"string"}}}},
    "steps":{"type":"array","minItems":3,"maxItems":10,"items":{
      "type":"object","additionalProperties":False,
      "required":["name","detail","minutes"],
      "properties":{"name":{"type":"string"},"detail":{"type":"string"},
        "minutes":{"type":"integer"},"tools":{"type":["string","null"]},
        "warning":{"type":["string","null"]}}}},
    "still_showing":{"type":"string","description":"The path when the steps above did not clear it. The most valuable section on the page."},
    "reset_procedure":{"type":["string","null"]},
    "model_notes":{"type":["string","null"],"description":"How behaviour differs across model series, where it genuinely does."},
    "parts":{"type":"array","maxItems":5,"items":{
      "type":"object","additionalProperties":False,
      "required":["name","cost","difficulty"],
      "properties":{"name":{"type":"string"},"cost":{"type":"string"},
        "difficulty":{"enum":["easy","moderate","hard","technician only"]},
        "note":{"type":["string","null"]}}}},
    "when_to_call":{"type":"string"},
    "faqs":{"type":"array","minItems":4,"maxItems":8,"items":{
      "type":"object","additionalProperties":False,"required":["q","a"],
      "properties":{"q":{"type":"string"},"a":{"type":"string"}}}},
    "diagram":{"type":"object","additionalProperties":False,"required":["kind","labels"],
      "properties":{"kind":{"enum":DIAGRAM_KINDS},"caption":{"type":["string","null"]},
        "labels":{"type":"object","additionalProperties":True}}},
    "sources":{"type":"array","minItems":1,"maxItems":5,"items":{
      "type":"object","additionalProperties":False,"required":["title","publisher"],
      "properties":{"title":{"type":"string"},"publisher":{"type":"string"},
        "url":{"type":["string","null"]}}}},
    "related_codes":{"type":"array","maxItems":6,"items":{"type":"string"}}
  }
}

def validate(d, slug=""):
    """Minimal dependency-free validation. Returns a list of problems."""
    errs = []
    def need(obj, key, path):
        if key not in obj or obj[key] in ("", None) and key not in (
                "safety_warning","reset_procedure","model_notes"):
            errs.append(f"{path}.{key} missing/empty")
    for k in PAGE_SCHEMA["required"]:
        need(d, k, slug)
    if errs: return errs
    if len(d["title"]) > 70: errs.append(f"{slug}.title too long ({len(d['title'])})")
    if len(d["meta_description"]) > 165:
        errs.append(f"{slug}.meta_description too long ({len(d['meta_description'])})")
    if d["severity"] not in ["minor","moderate","serious","stop-using-it"]:
        errs.append(f"{slug}.severity invalid: {d['severity']}")
    if d["can_diy"] not in ["yes","usually","sometimes","no"]:
        errs.append(f"{slug}.can_diy invalid: {d['can_diy']}")
    if not isinstance(d.get("cost_estimate"), dict) or "diy" not in d["cost_estimate"]:
        errs.append(f"{slug}.cost_estimate malformed")
    if not (2 <= len(d["causes"]) <= 7): errs.append(f"{slug}.causes count {len(d['causes'])}")
    for i, c in enumerate(d["causes"]):
        if c.get("frequency") not in ["most cases","common","occasional","rare"]:
            errs.append(f"{slug}.causes[{i}].frequency invalid: {c.get('frequency')}")
    if not (3 <= len(d["steps"]) <= 10): errs.append(f"{slug}.steps count {len(d['steps'])}")
    for i, s in enumerate(d["steps"]):
        if not isinstance(s.get("minutes"), int):
            errs.append(f"{slug}.steps[{i}].minutes not an int")
        if len(s.get("detail","")) < 40:
            errs.append(f"{slug}.steps[{i}].detail too thin")
    if not (4 <= len(d["faqs"]) <= 8): errs.append(f"{slug}.faqs count {len(d['faqs'])}")
    if d["diagram"].get("kind") not in DIAGRAM_KINDS:
        errs.append(f"{slug}.diagram.kind invalid: {d['diagram'].get('kind')}")
    if len(d["still_showing"]) < 150:
        errs.append(f"{slug}.still_showing too thin ({len(d['still_showing'])})")
    if not d.get("sources"): errs.append(f"{slug}.sources empty")
    return errs
