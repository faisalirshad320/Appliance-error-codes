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

## When the sources disagree, or there are none

These rules came out of the first run and are now standard. They are the difference between
a page a technician would respect and one that just sounds confident.

1. **Two live readings of a code: write the test, not the verdict.** If reputable sources
   split on what a code means, do not pick one. Cover both and lead with the cheap
   observation that separates them. Samsung OE is read as an overflow by some and a level
   sensor fault by others, so that page leads with the dry-tub test, which settles it in five
   minutes. Whirlpool's own consumer page describes F5 E2 and F5 E3 interchangeably, so that
   page routes on symptom: cycle will not start means the lock side, cycle finished and the
   door will not open means the unlock side, same part either way.
2. **Say in the page where the documentation is thin.** A reader who cross-checks and finds
   contradictions should learn that from you first, otherwise they conclude your page is the
   wrong one. `model_notes` is the place for it.
3. **A number only secondary sources assert is an estimate, not a measurement.** Every page
   claiming "D80 means 80 percent blocked" is quoting another blog. Write it as what the
   sensor estimates, not what it measured.
4. **Replace an unsourceable reference value with a test that works without one.** Do not
   print a thermistor resistance you cannot source. Tell the reader to measure cold, warm the
   sensor, and confirm the resistance falls. That diagnoses the part with no reference value
   at all, and it cannot be wrong for their model.
5. **Do not name a control the manufacturer assigns inconsistently.** Whirlpool and Maytag put
   the control lock on different buttons across ranges, so the page says to find the padlock
   icon rather than naming a button that is wrong on half the panels.
6. **A non-fault gets a short page.** Child lock, control lock, a maintenance reminder and a
   power-failure notice are not faults. Say so in the first sentence and keep the page short.
   Padding a non-fault into a fault page is worse than brevity.
7. **Codes that look identical on the display need saying so.** On a seven-segment display a
   lowercase b and a 6 are nearly the same glyph, and S and 5 are the same glyph. Where two
   codes on a brand collide that way, say it plainly.

## How to read a briefing note

A batch note marks where its claims come from, so you know which need checking before you
can use them:

- **(documented)** — taken from the manufacturer's own support material. Still worth a look
  if something seems off, but it is grounded.
- **(circulating)** — from code lists, repair sites or field reports. Treat as a hypothesis.
  Verify before asserting it, and if it does not hold up, see the next section.
- **(context)** — not a claim about what a code means: platform relationships, which page is
  high-volume, what readers get confused by. Use freely.

An unmarked claim about a code's meaning is **(circulating)** by default. The orchestrator is
not a source.

## If a briefing note is wrong, say so and do not write it

Batch notes from the orchestrator are a starting point, not an instruction to assert
something false. One wave-one note claimed LG refrigerator CL E is usually demo mode and told
the writer to lead with that. LG's own help library documents CL E as a low-side refrigerant
leak. The writer refused the note, wrote the real meaning, and was right: a page telling
someone with a leaking sealed system that their fridge is probably fine would have been the
single most harmful thing on this site.

So: when a note conflicts with what you find, follow the sources, write the page correctly,
and say in your report that the note was wrong and why. Where the note's confusion is itself
a thing readers arrive with, address it on the page. CL on an LG dishwasher really is the
child lock, which is why the refrigerator confusion exists, so that page answers "could this
just be the child lock?" directly rather than ignoring it.

## Output

One file per page at `content/<slug>.json`, matching the schema in `site/lib/schema.py`
exactly. Field notes:

- `title` max 65 chars, leads with brand + appliance + code.
- `meta_description` 110 to 155 chars, states the meaning and the top fix, and **must end on
  a complete sentence**. It is user-facing search text, so a trailing fragment reads as
  broken. Write it to fit rather than relying on the normalizer to trim it.
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
