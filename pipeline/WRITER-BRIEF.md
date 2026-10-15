# Writer brief: appliance error-code pages

You are writing for someone standing in front of a machine that is showing a code right now.
They are mildly stressed, they may be holding a phone in a dark laundry room, and they will
leave inside ten seconds if the page opens with filler. Everything below follows from that.

## The quality bar

Read `content/samsung-washer-4c.json` in full before you write anything. That is the standard.
Match its depth, its specificity and its tone. Do not match its length mechanically: a code with
one real cause gets a shorter page, and padding is worse than brevity.

## Hard rules

1. **Lead with the answer.** The `answer` field is the first thing on the page and the thing an
   AI Overview will lift. First sentence states what the code means in plain words. Never open
   with "Is your washer showing an error? You're not alone." Never restate the question.
2. **Never invent a number.** No made-up part numbers, resistance values, torque figures,
   voltages, model numbers, or capacities. Where a figure is needed and you are not certain,
   write "check the service sheet inside the machine" instead. A wrong resistance value sends
   someone to buy a part they did not need; a vague one costs nothing.
3. **Order causes by real frequency.** `frequency` must reflect what actually happens in the
   field. At most two causes may be "most cases". If you present five causes as equally likely
   you have written a useless page.
4. **Every step must be physically actionable.** Name the panel, the fastener, the direction a
   cap turns, roughly how much water to expect. "Check the drain pump" is a failure. "Unplug it,
   open the lower access panel with a Phillips #2, turn the filter cap anticlockwise, expect
   about a litre of water" is the standard.
5. **`still_showing` is the most valuable section on the page.** Minimum 150 characters, and
   realistically 600 to 1,200. This is where the reader actually is by the time they search.
   Give an ordered escalation: cheapest and most likely first, then the test that distinguishes
   each possibility, then the point where the cost jumps. Readers who get here have already
   done the obvious thing.
6. **Safety is not optional.** Any step involving mains wiring, a gas connection or a sealed
   refrigerant circuit gets `warning` on the step and, where the whole code implies it,
   `safety_warning` on the page. Never describe defeating a door interlock, a thermal cut-out
   or any other safety device. Gas and sealed-system work goes to a licensed technician, full
   stop.
7. **No copied text.** Write every sentence yourself. Do not reproduce manufacturer wording.

## Voice

Plain, direct, second person, American spelling. Short sentences. A technician explaining it to
a neighbour, not a blog post. Banned: "simply", "don't worry", "you're not alone", "in today's
world", exclamation marks, and any sentence that exists to reach a word count. Contractions are
fine. Dry humour is fine in small doses. Condescension is not.

## Accuracy

Work from what you actually know about these appliances. If you are genuinely unsure what a
specific code means on a specific brand, use WebSearch once to check it, then write. It is far
better to spend one search than to confidently describe the wrong fault. If after checking you
still cannot establish what a code means, write the page around the honest general case for
that brand and appliance and say plainly that the code is poorly documented, rather than
inventing a mechanism.

Where a code's meaning genuinely differs across model generations, say so in `model_notes`.
Where it does not, set `model_notes` to null rather than padding.

## Output

One file per page at `content/<slug>.json`, matching the schema in `site/lib/schema.py`
exactly. Field notes:

- `title` max 65 chars, leads with brand + appliance + code.
- `meta_description` max 158 chars, states the meaning and the top fix.
- `answer` 2 to 4 sentences, self-contained, no "as mentioned above".
- `severity` one of minor / moderate / serious / stop-using-it.
- `can_diy` one of yes / usually / sometimes / no.
- `cost_estimate` is an object with `diy` and `technician`, typical US dollars.
- `causes` 2 to 7, each with `cause`, `frequency`, `confirm`. `confirm` is the specific
  observation that proves it is this one, not a restatement of the cause.
- `steps` 3 to 10, each with `name`, `detail` (40+ chars, be specific), `minutes` (integer),
  optional `tools` and `warning`.
- `parts` up to 5 with `name`, `cost`, `difficulty` (easy / moderate / hard / technician only),
  optional `note`. Describe parts by common name; no invented part numbers.
- `faqs` 4 to 8. Each answer 40 to 80 words and answers in the first sentence. Use the real
  questions people ask, including the awkward ones ("can I still use it", "why did this happen
  suddenly", "is it worth repairing").
- `sources` 1 to 5. Cite the manufacturer's support documentation and service literature by
  description, and the repair community where that is genuinely where the field knowledge comes
  from. Set `url` to null unless you are certain of the exact URL. A wrong URL is worse than
  none.
- `related_codes` other codes on the same appliance a reader might also be seeing.

## Diagrams

Pick the `diagram.kind` that matches the fault, from exactly this list:

    washer-drain-filter      washer-inlet-valve      washer-unbalanced-load
    washer-drain-pump        washer-door-latch       dryer-vent-path
    dryer-thermistor         dishwasher-sump-float   dishwasher-drain
    control-board            water-supply            refrigerator-sensor
    generic-reset

`labels` takes `display` (the code as it appears on the panel, e.g. "4C") and `c1` to `c4`,
short callout labels of about 3 to 6 words each that match the numbered fix steps. Write a
`caption` of one short line. The diagram is drawn from these labels at build time, so the
labels are the content: make them specific to this fault, not generic.

## Brand list pages (`page_type` is "list")

Same schema, different emphasis. The `answer` explains how that brand's code system works
(letter-number conventions, where the display is, how codes are grouped). `causes` become the
broad categories of fault the brand's codes cover. `steps` become the general diagnostic
sequence that applies to any code on that brand. `related_codes` lists the specific codes
covered elsewhere on the site. These pages exist to rank for "brand appliance error codes" and
to hand readers off to the specific page, so they must be genuinely useful rather than a table
of contents in prose.

## Before you finish

Run this and fix anything it reports:

    python3 -c "
    import sys,json,glob; sys.path.insert(0,'site/lib'); import schema
    bad=0
    for f in glob.glob('content/*.json'):
        try: d=json.load(open(f))
        except Exception as e: print(f,'INVALID JSON',e); bad+=1; continue
        e=schema.validate(d,f)
        if e: bad+=1; print(f); [print('   ',x) for x in e]
    print('files with problems:',bad)"

Then report: how many pages you wrote, any code whose meaning you could not establish, and
anything you deliberately left vague because you were not certain of a figure.
