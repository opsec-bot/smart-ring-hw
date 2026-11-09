from math import hypot, pi
from pathlib import Path

from build123d import *

OUT = Path(__file__).parent / "out"
OUT.mkdir(exist_ok=True)

R_IN = 9.0
THICKNESS = 4.0
WALL = 0.8
EDGE_FILLET = 1.0

MODULE = (8.0, 1.0, 8.0)  # ISP1807
SENSOR = (4.3, 1.4, 2.9)  # MAXM86161
PCB_T = 0.4
BOARD_Z = MODULE[2] + 0.3
Z_CLEAR = 0.1

R_OUT = R_IN + THICKNESS
R_CAV_IN = R_IN + WALL
R_CAV_OUT = R_OUT - WALL
CAV_Z = BOARD_Z + 2 * Z_CLEAR
WIDTH = CAV_Z + 2 * WALL

WINDOW_TOP = R_IN + 0.5
PIN_R = 1.0
PIN_ANGLE = 15


def span_y(dx, y0, y1, dz, x=0.0, z=0.0):
    return Pos(x, (y0 + y1) / 2, z) * Box(dx, abs(y1 - y0), dz)


def span_x(x0, x1, dy, dz, y=0.0, z=0.0):
    return Pos((x0 + x1) / 2, y, z) * Box(abs(x1 - x0), dy, dz)


def arc(r0, r1, height, a0, a1):
    profile = Plane.XZ * Pos((r0 + r1) / 2, 0) * Rectangle(r1 - r0, height)
    return Rot(Z=a0) * revolve(profile, Axis.Z, revolution_arc=a1 - a0)


def annulus(r0, r1, height):
    return Cylinder(r1, height) - Cylinder(r0, height + 1)


def radial_pin(radius, r0, r1, angle):
    return Rot(Z=angle) * Pos((r0 + r1) / 2, 0, 0) * Rot(Y=90) * Cylinder(radius, r1 - r0)


band = annulus(R_IN, R_OUT, WIDTH)
band = fillet(band.edges().filter_by(GeomType.CIRCLE), EDGE_FILLET)

cavity = annulus(R_CAV_IN, R_CAV_OUT, CAV_Z)
aperture = span_y(SENSOR[0] + 0.3, -(R_CAV_IN + 0.1), -(R_IN - 0.5), SENSOR[2] + 0.3)
pin_holes = [radial_pin(PIN_R, R_IN - 0.5, R_CAV_IN + 0.1, a) for a in (PIN_ANGLE, -PIN_ANGLE)]

shell = band - cavity - aperture
for hole in pin_holes:
    shell -= hole

window = span_y(SENSOR[0] + 0.3, -WINDOW_TOP, -(R_IN - 0.5), SENSOR[2] + 0.3) - Cylinder(R_IN, WIDTH + 1)

top_pcb_y = R_CAV_IN + 0.05
top_pcb = span_y(9.0, top_pcb_y, top_pcb_y + PCB_T, BOARD_Z)
module = span_y(MODULE[0], top_pcb_y + PCB_T, top_pcb_y + PCB_T + MODULE[1], MODULE[2])

sensor = span_y(SENSOR[0], -(WINDOW_TOP + SENSOR[1]), -WINDOW_TOP, SENSOR[2])
sensor_pcb_y = WINDOW_TOP + SENSOR[1]
sensor_pcb = span_y(7.0, -(sensor_pcb_y + PCB_T), -sensor_pcb_y, BOARD_Z)

side_x = R_CAV_IN + 0.05
side_pcb = span_x(side_x, side_x + PCB_T, 13.0, BOARD_Z)
pmic = span_x(side_x + PCB_T, side_x + PCB_T + 0.6, 2.5, 2.5, y=-3.0)
imu = span_x(side_x + PCB_T, side_x + PCB_T + 0.83, 3.0, 2.5, y=0.2)
temp = span_x(side_x + PCB_T, side_x + PCB_T + 0.8, 2.0, 2.0, y=3.0, z=-1.5)
flash = span_x(side_x + PCB_T, side_x + PCB_T + 0.8, 2.0, 3.0, y=3.2, z=2.0)

BATTERY_A0, BATTERY_A1 = 118.0, 246.0
BATTERY_R0, BATTERY_R1 = R_CAV_IN + 0.2, R_CAV_OUT - 0.2
battery = arc(BATTERY_R0, BATTERY_R1, CAV_Z - 0.4, BATTERY_A0, BATTERY_A1)

pins = [radial_pin(PIN_R - 0.05, R_IN, R_CAV_IN + 0.05, a) for a in (PIN_ANGLE, -PIN_ANGLE)]

parts = {
    "shell": (shell, Color(0.13, 0.14, 0.16)),
    "optical_window": (window, Color(0.55, 0.8, 0.9, 0.6)),
    "pcb_top": (top_pcb, Color(0.1, 0.35, 0.2)),
    "isp1807_module": (module, Color(0.72, 0.72, 0.68)),
    "pcb_sensor": (sensor_pcb, Color(0.1, 0.35, 0.2)),
    "maxm86161": (sensor, Color(0.05, 0.05, 0.05)),
    "pcb_side": (side_pcb, Color(0.1, 0.35, 0.2)),
    "bq25120a": (pmic, Color(0.2, 0.2, 0.22)),
    "bmi270": (imu, Color(0.2, 0.2, 0.22)),
    "tmp117": (temp, Color(0.2, 0.2, 0.22)),
    "qspi_flash": (flash, Color(0.2, 0.2, 0.22)),
    "battery": (battery, Color(0.75, 0.55, 0.15)),
    "contact_a": (pins[0], Color(0.85, 0.68, 0.2)),
    "contact_b": (pins[1], Color(0.85, 0.68, 0.2)),
}


def overlap(a, b):
    result = a.intersect(b)
    if result is None:
        return 0.0
    shapes = result if isinstance(result, list) else [result]
    return sum(shape.volume for shape in shapes)


names = list(parts)
collisions = []
for i, first in enumerate(names):
    for second in names[i + 1:]:
        volume = overlap(parts[first][0], parts[second][0])
        if volume > 1e-4:
            collisions.append((first, second, round(volume, 4)))

solids = []
for name, (shape, color) in parts.items():
    shape.label = name
    shape.color = color
    solids.append(shape)
assembly = Compound(label="smart_ring", children=solids)

export_step(assembly, str(OUT / "ring_assembly.step"))
export_gltf(assembly, str(OUT / "ring_assembly.glb"), binary=True)
export_stl(split(shell, bisect_by=Plane.XY, keep=Keep.TOP), str(OUT / "shell_top.stl"))
export_stl(split(shell, bisect_by=Plane.XY, keep=Keep.BOTTOM), str(OUT / "shell_bottom.stl"))

module_top = top_pcb_y + PCB_T + MODULE[1]
battery_mm3 = battery.volume
print(f"ring: ID {2 * R_IN} OD {2 * R_OUT} width {WIDTH:.2f} thickness {THICKNESS}")
print(f"module corner radius {hypot(MODULE[0] / 2, module_top):.2f} vs cavity {R_CAV_OUT}")
print(f"shell volume {shell.volume:.0f} mm3, mass at 1.2 g/cc {shell.volume * 1.2e-3:.2f} g")
print(f"battery envelope {battery_mm3:.0f} mm3, ideal at 250 Wh/L {battery_mm3 * 1e-6 * 250 / 3.7 * 1000:.0f} mAh")
print(f"outer arc check {2 * pi * R_OUT:.1f} mm circumference")
print("collisions:", collisions if collisions else "none")
