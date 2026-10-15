"""
Original technical diagrams, drawn as SVG at build time.

Every diagram here is generated from these coordinates. Nothing is traced from a
manufacturer drawing, photographed from a product, or downloaded. The site owns the
output outright, which is the only way to use imagery on a commercial page without a
licence. As a bonus they are a few kB each, scale to any screen, need no CLS-causing
width/height guessing, and adapt to dark mode through currentColor and CSS variables.

Each builder returns the inner SVG for an 800x500 viewBox. Callouts are numbered to
match the numbered fix steps on the page, so "step 3" on the page is "3" on the drawing.
"""

VIEWBOX_W, VIEWBOX_H = 800, 500


def _callout(n, x, y, tx, ty, label, anchor="start"):
    """A numbered marker at (x,y) with a leader line to a label at (tx,ty)."""
    return f'''
  <g class="callout">
    <line x1="{x}" y1="{y}" x2="{tx}" y2="{ty}" />
    <circle class="dot" cx="{x}" cy="{y}" r="13" />
    <text class="num" x="{x}" y="{y + 5}" text-anchor="middle">{n}</text>
    <text class="lbl" x="{tx + (8 if anchor == 'start' else -8)}" y="{ty + 4}"
          text-anchor="{anchor}">{label}</text>
  </g>'''


def _esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


# ---------------------------------------------------------------- washer, front load

def washer_drain_filter(labels):
    l = labels
    return f'''
  <rect class="body" x="150" y="60" width="330" height="390" rx="14" />
  <circle class="glass" cx="315" cy="240" r="105" />
  <circle class="glass-inner" cx="315" cy="240" r="86" />
  <rect class="panel" x="168" y="78" width="294" height="46" rx="8" />
  <circle class="led" cx="196" cy="101" r="8" />
  <rect class="screen" x="330" y="88" width="112" height="26" rx="5" />
  <text class="code" x="386" y="107" text-anchor="middle">{_esc(l.get("display", "- - -"))}</text>
  <rect class="hatch" x="168" y="382" width="294" height="52" rx="8" />
  <circle class="part" cx="232" cy="408" r="20" />
  <path class="thread" d="M222 408 h20 M232 398 v20" />
  <rect class="hose" x="276" y="398" width="54" height="20" rx="10" />
  {_callout(1, 232, 408, 560, 390, _esc(l.get("c1", "Filter cap, turn anticlockwise")))}
  {_callout(2, 303, 408, 560, 432, _esc(l.get("c2", "Drain hose behind the cap")))}
  {_callout(3, 386, 101, 560, 110, _esc(l.get("c3", "Code shown here")))}
  {_callout(4, 315, 240, 560, 250, _esc(l.get("c4", "Drum, check for trapped items")))}'''


def washer_inlet_valve(labels):
    l = labels
    return f'''
  <rect class="body" x="90" y="70" width="330" height="370" rx="14" />
  <rect class="panel" x="108" y="88" width="294" height="40" rx="8" />
  <rect class="vent" x="140" y="170" width="230" height="200" rx="8" />
  <path class="grid" d="M140 220 h230 M140 270 h230 M140 320 h230" />
  <rect class="part" x="430" y="150" width="74" height="46" rx="8" />
  <rect class="part" x="430" y="236" width="74" height="46" rx="8" />
  <path class="pipe" d="M504 173 H610 a18 18 0 0 1 18 18 V330" />
  <path class="pipe" d="M504 259 H580 a16 16 0 0 1 16 16 V330" />
  <rect class="tap" x="596" y="330" width="52" height="34" rx="6" />
  <circle class="screen-mesh" cx="466" cy="173" r="9" />
  <circle class="screen-mesh" cx="466" cy="259" r="9" />
  {_callout(1, 466, 173, 300, 120, _esc(l.get("c1", "Hot inlet valve + mesh screen")), "end")}
  {_callout(2, 466, 259, 300, 470, _esc(l.get("c2", "Cold inlet valve + mesh screen")), "end")}
  {_callout(3, 622, 347, 700, 420, _esc(l.get("c3", "Supply tap, must be fully open")), "end")}
  {_callout(4, 628, 250, 700, 190, _esc(l.get("c4", "Check hose for kinks")), "end")}'''


def washer_unbalanced_load(labels):
    l = labels
    return f'''
  <rect class="body" x="120" y="60" width="340" height="390" rx="14" />
  <circle class="glass" cx="290" cy="250" r="128" />
  <circle class="glass-inner" cx="290" cy="250" r="108" />
  <path class="laundry" d="M215 300 q35 -70 85 -40 q50 30 70 -10 q14 58 -30 78 q-70 32 -125 -28 z" />
  <path class="arrow-spin" d="M290 128 a122 122 0 0 1 112 74" />
  <path class="arrow-head" d="M398 196 l12 14 l-20 4 z" />
  <rect class="foot" x="150" y="450" width="36" height="22" rx="5" />
  <rect class="foot" x="394" y="450" width="36" height="22" rx="5" />
  <path class="level" d="M120 486 H460" />
  {_callout(1, 268, 318, 560, 250, _esc(l.get("c1", "Load bunched on one side")))}
  {_callout(2, 168, 461, 560, 400, _esc(l.get("c2", "Levelling feet, lock the nuts")))}
  {_callout(3, 290, 250, 560, 180, _esc(l.get("c3", "Redistribute, then restart spin")))}
  {_callout(4, 412, 461, 560, 440, _esc(l.get("c4", "Floor must not flex")))}'''


def washer_drain_pump(labels):
    l = labels
    return f'''
  <rect class="body" x="90" y="80" width="300" height="340" rx="14" />
  <circle class="pump-housing" cx="470" cy="290" r="78" />
  <circle class="pump-inner" cx="470" cy="290" r="50" />
  <path class="impeller" d="M470 252 v76 M436 271 l68 38 M436 309 l68 -38" />
  <path class="pipe" d="M390 290 H392" />
  <rect class="pipe-box" x="366" y="272" width="30" height="36" rx="6" />
  <path class="pipe" d="M548 290 H640 a16 16 0 0 1 16 16 V210" />
  <path class="pipe-open" d="M640 210 h32" />
  <rect class="part" x="430" y="392" width="80" height="34" rx="7" />
  {_callout(1, 470, 290, 300, 160, _esc(l.get("c1", "Pump impeller, must spin freely")), "end")}
  {_callout(2, 470, 409, 300, 470, _esc(l.get("c2", "Pump filter housing")), "end")}
  {_callout(3, 656, 250, 716, 140, _esc(l.get("c3", "Standpipe, 60-100cm high")), "end")}
  {_callout(4, 381, 290, 300, 330, _esc(l.get("c4", "Sump hose, check for blockage")), "end")}'''


def washer_door_latch(labels):
    l = labels
    return f'''
  <rect class="body" x="110" y="60" width="300" height="390" rx="14" />
  <circle class="glass" cx="270" cy="250" r="112" />
  <circle class="glass-inner" cx="270" cy="250" r="92" />
  <rect class="latch-plate" x="372" y="218" width="30" height="64" rx="6" />
  <path class="hook" d="M402 240 h34 a10 10 0 0 1 10 10 v12 a10 10 0 0 1 -10 10 h-34" />
  <rect class="part" x="452" y="206" width="96" height="88" rx="9" />
  <circle class="solenoid" cx="500" cy="250" r="22" />
  <path class="wire" d="M548 232 h70 M548 268 h70" />
  {_callout(1, 418, 250, 640, 160, _esc(l.get("c1", "Latch hook, check for wear")), "end")}
  {_callout(2, 500, 250, 640, 330, _esc(l.get("c2", "Door lock assembly")), "end")}
  {_callout(3, 270, 250, 640, 410, _esc(l.get("c3", "Press door firmly until it clicks")), "end")}'''


# ---------------------------------------------------------------- dryer

def dryer_vent_path(labels):
    l = labels
    return f'''
  <rect class="body" x="70" y="150" width="250" height="280" rx="14" />
  <circle class="glass" cx="195" cy="290" r="88" />
  <rect class="panel" x="88" y="168" width="214" height="36" rx="7" />
  <rect class="lint" x="120" y="396" width="150" height="20" rx="5" />
  <path class="duct" d="M320 250 H430 a26 26 0 0 1 26 26 V340 a26 26 0 0 0 26 26 H600" />
  <path class="duct2" d="M600 366 a24 24 0 0 0 24 -24 V200" />
  <rect class="wallcap" x="600" y="170" width="52" height="40" rx="6" />
  <path class="flap" d="M652 178 l26 -12 M652 192 l26 12" />
  <path class="lint-blob" d="M470 352 q22 -16 44 0 q-22 12 -44 0 z" />
  {_callout(1, 195, 406, 150, 470, _esc(l.get("c1", "Lint screen, clean every load")), "end")}
  {_callout(2, 492, 352, 420, 440, _esc(l.get("c2", "Lint build-up in the duct")), "end")}
  {_callout(3, 626, 190, 700, 120, _esc(l.get("c3", "Outside vent flap must open")), "end")}
  {_callout(4, 456, 300, 520, 236, _esc(l.get("c4", "Crushed or kinked duct")), "end")}'''


def dryer_thermistor(labels):
    l = labels
    return f'''
  <rect class="body" x="90" y="110" width="300" height="320" rx="14" />
  <circle class="glass" cx="240" cy="280" r="98" />
  <rect class="duct-box" x="420" y="190" width="200" height="140" rx="10" />
  <path class="heat" d="M448 300 q16 -30 32 0 q16 30 32 0 q16 -30 32 0" />
  <rect class="part" x="560" y="212" width="44" height="30" rx="6" />
  <circle class="sensor" cx="582" cy="227" r="9" />
  <path class="wire" d="M604 227 h60" />
  <rect class="part" x="430" y="212" width="44" height="30" rx="6" />
  <circle class="sensor" cx="452" cy="227" r="9" />
  {_callout(1, 582, 227, 690, 150, _esc(l.get("c1", "Thermistor, check resistance")), "end")}
  {_callout(2, 452, 227, 400, 150, _esc(l.get("c2", "Thermal cut-out")), "end")}
  {_callout(3, 520, 300, 690, 390, _esc(l.get("c3", "Heater element")), "end")}'''


# ---------------------------------------------------------------- dishwasher

def dishwasher_sump_float(labels):
    l = labels
    return f'''
  <rect class="body" x="110" y="60" width="420" height="380" rx="14" />
  <rect class="panel" x="128" y="78" width="384" height="40" rx="7" />
  <rect class="screen" x="380" y="86" width="112" height="24" rx="5" />
  <text class="code" x="436" y="104" text-anchor="middle">{_esc(labels.get("display", "- - -"))}</text>
  <path class="rack" d="M150 200 h340 M150 290 h340" />
  <path class="tines" d="M190 200 v-22 M250 200 v-22 M310 200 v-22 M370 200 v-22 M430 200 v-22" />
  <path class="basin" d="M130 380 h380 l-30 44 h-320 z" />
  <ellipse class="sump" cx="320" cy="398" rx="54" ry="16" />
  <rect class="tray" x="110" y="440" width="420" height="26" rx="6" />
  <path class="water" d="M130 454 h380" />
  <rect class="float" x="296" y="430" width="48" height="18" rx="5" />
  {_callout(1, 320, 398, 600, 330, _esc(labels.get("c1", "Sump and filter, lift and rinse")))}
  {_callout(2, 320, 439, 600, 420, _esc(labels.get("c2", "Float switch in the base tray")))}
  {_callout(3, 320, 454, 600, 470, _esc(labels.get("c3", "Water in the base triggers the code")))}
  {_callout(4, 436, 98, 600, 110, _esc(labels.get("c4", "Code shown here")))}'''


def dishwasher_drain(labels):
    l = labels
    return f'''
  <rect class="body" x="90" y="80" width="330" height="340" rx="14" />
  <path class="basin" d="M110 350 h290 l-24 38 h-242 z" />
  <circle class="filter" cx="255" cy="366" r="26" />
  <path class="mesh" d="M235 366 h40 M255 346 v40 M241 352 l28 28 M269 352 l-28 28" />
  <path class="pipe" d="M420 330 H520 a20 20 0 0 0 20 -20 V190 a20 20 0 0 1 20 -20 H640" />
  <rect class="airgap" x="540" y="140" width="44" height="34" rx="6" />
  <rect class="disposal" x="636" y="258" width="90" height="100" rx="10" />
  <path class="knockout" d="M652 300 h58" />
  {_callout(1, 255, 366, 300, 460, _esc(l.get("c1", "Filter basket, twist and lift out")), "end")}
  {_callout(2, 562, 157, 660, 100, _esc(l.get("c2", "Air gap, lift cap and clear")), "end")}
  {_callout(3, 681, 300, 760, 400, _esc(l.get("c3", "Disposal knockout plug")), "end")}
  {_callout(4, 540, 250, 470, 200, _esc(l.get("c4", "Drain hose high loop")), "end")}'''


# ---------------------------------------------------------------- shared

def control_board(labels):
    l = labels
    return f'''
  <rect class="pcb" x="140" y="90" width="470" height="320" rx="10" />
  <path class="trace" d="M180 150 h180 v60 h120 M180 250 h90 v90 h240 M420 150 v120 h140" />
  <rect class="chip" x="330" y="190" width="90" height="60" rx="5" />
  <path class="pins" d="M330 202 h-14 M330 220 h-14 M330 238 h-14 M420 202 h14 M420 220 h14 M420 238 h14" />
  <rect class="cap" x="200" y="300" width="34" height="48" rx="5" />
  <rect class="cap" x="252" y="300" width="34" height="48" rx="5" />
  <rect class="relay" x="490" y="300" width="70" height="56" rx="5" />
  <rect class="conn" x="160" y="110" width="110" height="26" rx="4" />
  <rect class="conn" x="470" y="110" width="110" height="26" rx="4" />
  <circle class="burn" cx="269" cy="324" r="22" />
  {_callout(1, 269, 324, 660, 250, _esc(l.get("c1", "Look for a bulged or leaking capacitor")))}
  {_callout(2, 525, 328, 660, 330, _esc(l.get("c2", "Relay, listen for a click")))}
  {_callout(3, 215, 123, 660, 150, _esc(l.get("c3", "Reseat every connector")))}
  {_callout(4, 375, 220, 660, 410, _esc(l.get("c4", "Main processor, not user serviceable")))}'''


def water_supply(labels):
    l = labels
    return f'''
  <rect class="wall" x="80" y="70" width="150" height="360" rx="8" />
  <rect class="tap" x="230" y="150" width="60" height="40" rx="7" />
  <rect class="tap" x="230" y="250" width="60" height="40" rx="7" />
  <circle class="handle" cx="260" cy="130" r="20" />
  <circle class="handle" cx="260" cy="230" r="20" />
  <path class="pipe" d="M290 170 H420 a22 22 0 0 1 22 22 V300" />
  <path class="pipe" d="M290 270 H380 a20 20 0 0 1 20 20 V300" />
  <rect class="machine" x="380" y="300" width="300" height="150" rx="12" />
  <circle class="screen-mesh" cx="330" cy="170" r="11" />
  <circle class="screen-mesh" cx="330" cy="270" r="11" />
  <path class="kink" d="M442 240 q24 -18 0 -36" />
  {_callout(1, 260, 130, 150, 60, _esc(l.get("c1", "Tap fully open")), "end")}
  {_callout(2, 330, 170, 480, 120, _esc(l.get("c2", "Hose filter screen, clean of grit")))}
  {_callout(3, 442, 222, 560, 180, _esc(l.get("c3", "Kinked hose behind the machine")))}
  {_callout(4, 530, 375, 700, 470, _esc(l.get("c4", "Machine inlet")), "end")}'''


def refrigerator_sensor(labels):
    l = labels
    return f'''
  <rect class="body" x="180" y="50" width="300" height="410" rx="16" />
  <path class="divider" d="M180 190 H480" />
  <rect class="shelf" x="204" y="240" width="252" height="7" rx="3" />
  <rect class="shelf" x="204" y="320" width="252" height="7" rx="3" />
  <rect class="shelf" x="204" y="400" width="252" height="7" rx="3" />
  <rect class="panel" x="204" y="72" width="130" height="34" rx="6" />
  <rect class="part" x="396" y="120" width="40" height="28" rx="5" />
  <circle class="sensor" cx="416" cy="134" r="8" />
  <rect class="part" x="396" y="268" width="40" height="28" rx="5" />
  <circle class="sensor" cx="416" cy="282" r="8" />
  <path class="coil" d="M520 160 q22 -22 44 0 q22 22 44 0 q22 -22 44 0" />
  <rect class="fan" x="540" y="280" width="90" height="90" rx="45" />
  <path class="blade" d="M585 290 v70 M550 325 h70 M562 302 l46 46 M608 302 l-46 46" />
  {_callout(1, 416, 134, 660, 90, _esc(l.get("c1", "Freezer sensor")), "end")}
  {_callout(2, 416, 282, 300, 470, _esc(l.get("c2", "Fridge sensor")), "end")}
  {_callout(3, 585, 325, 700, 420, _esc(l.get("c3", "Evaporator fan, listen for it")), "end")}
  {_callout(4, 586, 160, 700, 230, _esc(l.get("c4", "Defrost heater / coil icing")), "end")}'''


def generic_reset(labels):
    l = labels
    return f'''
  <rect class="body" x="150" y="80" width="340" height="340" rx="14" />
  <rect class="panel" x="172" y="102" width="296" height="58" rx="8" />
  <rect class="screen" x="320" y="114" width="132" height="34" rx="6" />
  <text class="code" x="386" y="139" text-anchor="middle">{_esc(l.get("display", "- - -"))}</text>
  <circle class="btn" cx="206" cy="131" r="14" />
  <circle class="btn" cx="248" cy="131" r="14" />
  <circle class="btn" cx="290" cy="131" r="14" />
  <path class="plug-cord" d="M490 300 H600 a22 22 0 0 0 22 -22 V210" />
  <rect class="plug" x="598" y="168" width="48" height="44" rx="6" />
  <path class="prongs" d="M610 168 v-22 M634 168 v-22" />
  <rect class="socket" x="586" y="110" width="72" height="40" rx="6" />
  <path class="clock" d="M386 230 m-40 0 a40 40 0 1 0 80 0 a40 40 0 1 0 -80 0 M386 206 v24 h18" />
  {_callout(1, 622, 190, 700, 120, _esc(l.get("c1", "Unplug at the wall")), "end")}
  {_callout(2, 386, 230, 300, 470, _esc(l.get("c2", "Wait the full time, do not rush it")), "end")}
  {_callout(3, 386, 131, 560, 440, _esc(l.get("c3", "Code should clear on power-up")), "end")}'''


DIAGRAMS = {
    "washer-drain-filter": (washer_drain_filter, "Washer drain filter and pump access"),
    "washer-inlet-valve": (washer_inlet_valve, "Washer water inlet valves and supply hoses"),
    "washer-unbalanced-load": (washer_unbalanced_load, "Unbalanced drum load and levelling feet"),
    "washer-drain-pump": (washer_drain_pump, "Washer drain pump and standpipe"),
    "washer-door-latch": (washer_door_latch, "Washer door latch and lock assembly"),
    "dryer-vent-path": (dryer_vent_path, "Dryer exhaust path from lint screen to wall cap"),
    "dryer-thermistor": (dryer_thermistor, "Dryer thermistor, cut-out and heater"),
    "dishwasher-sump-float": (dishwasher_sump_float, "Dishwasher sump, base tray and float switch"),
    "dishwasher-drain": (dishwasher_drain, "Dishwasher filter, air gap and drain route"),
    "control-board": (control_board, "Appliance control board inspection points"),
    "water-supply": (water_supply, "Water supply taps, screens and hoses"),
    "refrigerator-sensor": (refrigerator_sensor, "Refrigerator sensors, fan and defrost system"),
    "generic-reset": (generic_reset, "Power-cycle reset procedure"),
}

DEFAULT_BY_APPLIANCE = {
    "washer": "washer-drain-filter", "dryer": "dryer-vent-path",
    "dishwasher": "dishwasher-sump-float", "refrigerator": "refrigerator-sensor",
    "freezer": "refrigerator-sensor", "oven": "control-board", "range": "control-board",
    "microwave": "control-board", "dehumidifier": "generic-reset",
    "air conditioner": "generic-reset", "coffee machine": "generic-reset",
}


def render(kind, labels, appliance="washer", title=None):
    """Return a complete, accessible <figure> for the page."""
    if kind not in DIAGRAMS:
        kind = DEFAULT_BY_APPLIANCE.get(appliance, "generic-reset")
    builder, default_title = DIAGRAMS[kind]
    caption = title or default_title
    body = builder(labels or {})
    return f'''<figure class="diagram" data-kind="{kind}">
<svg viewBox="0 0 {VIEWBOX_W} {VIEWBOX_H}" role="img" xmlns="http://www.w3.org/2000/svg"
     aria-label="{_esc(caption)}">
  <title>{_esc(caption)}</title>{body}
</svg>
<figcaption>{_esc(caption.rstrip(". "))}. Original diagram, not to scale.</figcaption>
</figure>'''
