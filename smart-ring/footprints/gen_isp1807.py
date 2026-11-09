from pathlib import Path

NAME = "ISP1807_LGA-78_8x8mm_P0.65mm"
LIB = Path(__file__).parent / "SmartRing.pretty"
LIB.mkdir(exist_ok=True)

EDGE = 0.3125
FAR = 8 - EDGE
CORNER = 0.513
CORNER_FAR = 7.487
ROW_X = [1.4 + 0.65 * i for i in range(9)]
INNER_X = [1.725 + 0.65 * i for i in range(8)]

A = (0.775, 0.775)
B = (0.775, 0.8)
C = (0.4, 0.375)
D = (0.4, 0.4)
E = (0.375, 0.4)

pads = {}


def row(numbers, xs, y, size):
    for number, x in zip(numbers, xs):
        pads[number] = (x, y, size)


row(range(48, 31, -2), ROW_X, EDGE, C)
row(range(47, 32, -2), INNER_X, 0.95, D)
row(range(56, 48, -1), INNER_X, 1.725, D)
row(range(64, 56, -1), INNER_X, 2.375, D)
row(range(9, 24, 2), INNER_X, 3.15, D)
row(range(8, 25, 2), ROW_X, 3.8, D)

for number, y in zip((2, 4, 6), (1.4, 2.05, 2.7)):
    pads[number] = (EDGE, y, E)
for number, y in zip((30, 28, 26), (1.4, 2.05, 2.7)):
    pads[number] = (FAR, y, E)
for number, y in zip((3, 5), (1.725, 2.375)):
    pads[number] = (0.95, y, D)
for number, y in zip((29, 27), (1.725, 2.375)):
    pads[number] = (7.05, y, D)

for number, x, y in ((1, CORNER, CORNER), (31, CORNER_FAR, CORNER), (68, CORNER, CORNER_FAR), (75, CORNER_FAR, CORNER_FAR)):
    pads[number] = (x, y, A)
for number, x in ((7, CORNER), (25, CORNER_FAR)):
    pads[number] = (x, 3.6, B)

for number, y in zip((65, 66, 67), (4.55, 5.55, 6.55)):
    pads[number] = (EDGE, y, E)
for number, y in zip((78, 77, 76), (4.55, 5.55, 6.55)):
    pads[number] = (FAR, y, E)
for number, x in zip(range(69, 75), (1.5, 2.5, 3.5, 4.5, 5.5, 6.5)):
    pads[number] = (x, FAR, C)

assert sorted(pads) == list(range(1, 79))


def line(x0, y0, x1, y1, layer, width):
    return (
        f'  (fp_line (start {x0} {y0}) (end {x1} {y1}) '
        f'(stroke (width {width}) (type solid)) (layer "{layer}"))\n'
    )


def outline(half, layer, width):
    return (
        line(-half, -half, half, -half, layer, width)
        + line(half, -half, half, half, layer, width)
        + line(half, half, -half, half, layer, width)
        + line(-half, half, -half, -half, layer, width)
    )


def text(kind, value, y, layer):
    return (
        f'  (fp_text {kind} "{value}" (at 0 {y}) (layer "{layer}")\n'
        '    (effects (font (size 0.6 0.6) (thickness 0.1)))\n  )\n'
    )


body = (
    f'(footprint "{NAME}" (version 20240108) (generator "gen_isp1807") (layer "F.Cu")\n'
    '  (descr "Insight SiP ISP1807 LGA, datasheet R19 section 4. Antenna half needs a metal keep-out on every layer.")\n'
    '  (attr smd)\n'
    + text("reference", "REF**", -5.0, "F.SilkS")
    + text("value", NAME, 5.0, "F.Fab")
    + text("user", "ANTENNA KEEP-OUT", 2.0, "F.Fab")
    + outline(4.0, "F.Fab", 0.1)
    + outline(4.15, "F.SilkS", 0.12)
    + outline(4.3, "F.CrtYd", 0.05)
    + line(-4.0, 0.0, 4.0, 0.0, "F.Fab", 0.1)
    + '  (fp_circle (center -4.6 -4.6) (end -4.45 -4.6) (stroke (width 0.1) (type solid)) (fill solid) (layer "F.SilkS"))\n'
)

for number in sorted(pads):
    x, y, (w, h) = pads[number]
    body += (
        f'  (pad "{number}" smd rect (at {x - 4:.4f} {y - 4:.4f}) (size {w} {h}) '
        '(layers "F.Cu" "F.Paste" "F.Mask"))\n'
    )

(LIB / f"{NAME}.kicad_mod").write_text(body + ")\n", encoding="utf-8")
print(len(pads), "pads written")
