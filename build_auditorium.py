"""Draws the New Auditorium (Building 4) as a top-down pixel map AND writes the
matching game data, so art and collision can never drift apart.

Layout is derived from the uploaded photos (see ASSETS.md section 5):
  - stage at the top, big centre screen + podium, a screen on each side wall,
    a rear screen mounted above the exit
  - central red carpet, yellow seat blocks left/right, red seats at the front and rear
  - rear centre exit, glass control booth on the screen-LEFT of the exit
    (= the right-hand side when standing on stage looking back, as in photo 1000087982)
  - 2nd floor balcony runs along both side walls and across the rear
Anything the photos do not show is tagged NEEDS_REFERENCE in the data.

Outputs
  public/assets/maps/auditorium_1f.png / auditorium_2f.png / auditorium_2f_overhead.png
  src/maps/auditoriumMap.js
"""
import os, json, random, math
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = 32
W, H = 40, 30
PW, PH = W * T, H * T
random.seed(7)

# ---------------------------------------------------------------- palette
C = dict(
    wood=(148, 84, 50), wood_dk=(116, 62, 38), wood_lt=(170, 104, 62), wood_hi=(190, 124, 76),
    stage=(204, 140, 82), stage_dk=(150, 92, 52), stage_lt=(226, 164, 100), lip=(112, 64, 40),
    carpet=(176, 32, 36), carpet_dk=(138, 22, 28), carpet_lt=(204, 52, 52), gold=(222, 178, 80), gold_dk=(168, 124, 44),
    y_seat=(236, 196, 76), y_back=(206, 160, 44), y_dk=(132, 92, 24), y_lt=(252, 226, 130),
    r_seat=(184, 38, 46), r_back=(146, 26, 36), r_dk=(78, 14, 22), r_lt=(222, 78, 80),
    wall_r=(164, 30, 34), wall_w=(228, 224, 216), wall_g=(172, 172, 170), wall_dk=(92, 70, 64), wall_edge=(60, 40, 38),
    door=(56, 32, 28), door_lt=(86, 52, 44), screen=(40, 220, 56), screen_dk=(22, 120, 34), frame=(24, 36, 30),
    curtain=(206, 146, 56), curtain_dk=(160, 104, 36), curtain_lt=(236, 182, 92), valance=(172, 30, 34),
    glass=(168, 214, 228), glass_dk=(96, 150, 172), pillar=(240, 196, 40), pillar_dk=(180, 136, 20),
    desk=(176, 150, 120), desk_dk=(120, 96, 74), mon=(40, 54, 70), mon_scr=(120, 188, 232),
    mixer=(46, 48, 56), exit_glow=(255, 250, 226),
    floor2=(176, 120, 78), floor2_dk=(140, 92, 56), rail=(238, 226, 206), rail_dk=(176, 160, 138),
)


def tile_rect(c0, r0, c1, r1):
    return (c0 * T, r0 * T, (c1 + 1) * T - 1, (r1 + 1) * T - 1)


def px(c, r):
    return (c * T, r * T)


# ---------------------------------------------------------------- layout constants (tiles)
STAGE = dict(c0=8, r0=2, c1=31, r1=7)            # platform incl. lip row r1
STEPS = dict(c0=18, c1=21)
MAIN_SCREEN = dict(c0=15, r0=0, c1=24, r1=1)
CARPET = dict(c0=19, c1=20, r0=8, r1=29)
YELLOW = dict(L=(4, 17), R=(22, 35), r0=12, r1=21)
RED_FRONT = dict(L=(10, 17), R=(22, 29), r0=9, r1=10)
RED_REAR = dict(L=(6, 17), R=(22, 33), r0=22, r1=23)
BOOTH = dict(c0=5, r0=24, c1=14, r1=27)          # glass room, door gap on its east side
EXIT = dict(c0=18, c1=21, r0=28, r1=29)
PILLARS = [(16, 27), (23, 27)]
SIDE_DOORS_2F = dict(L=dict(c=1, r0=3, r1=5), R=dict(c=38, r0=3, r1=5))
SIDE_SCREENS = dict(L=dict(c0=0, c1=1, r0=7, r1=10), R=dict(c0=38, c1=39, r0=7, r1=10))
REAR_SCREEN = dict(c0=17, c1=22, r=26)           # overhead layer, above the exit
DECOR_DOORS = [(1, r) for r in (13, 18, 23)] + [(38, r) for r in (13, 18, 23)]


def noise(img, amt=5, seed=1):
    rnd = random.Random(seed)
    px_ = img.load()
    for y in range(img.height):
        for x in range(img.width):
            v = rnd.randint(-amt, amt)
            r, g, b, a = px_[x, y]
            px_[x, y] = (max(0, min(255, r + v)), max(0, min(255, g + v)), max(0, min(255, b + v)), a)


def shade(col, k):
    return tuple(max(0, min(255, int(v * k))) for v in col)


# ---------------------------------------------------------------- drawing pieces
def floor(d, base, dk, lt, rect, plank=16):
    x0, y0, x1, y1 = rect
    d.rectangle(rect, fill=base)
    for y in range(y0, y1 + 1, plank):
        d.line([(x0, y), (x1, y)], fill=dk)
        d.line([(x0, y + 1), (x1, y + 1)], fill=lt)
    # staggered plank ends
    for row, y in enumerate(range(y0, y1 + 1, plank)):
        off = (row * 37) % 96
        for x in range(x0 + off, x1 + 1, 96):
            d.line([(x, y), (x, y + plank - 1)], fill=dk)


def chair(d, c, r, seat, back, dk, lt):
    """top-down chair facing north (towards the stage), covered like the banquet chairs in the photos."""
    x, y = c * T, r * T
    d.rounded_rectangle((x + 5, y + 6, x + 27, y + 30), 4, fill=(0, 0, 0, 70))            # soft shadow
    d.rounded_rectangle((x + 4, y + 4, x + 26, y + 26), 4, fill=seat, outline=dk)
    d.rectangle((x + 6, y + 6, x + 24, y + 9), fill=lt)                                     # seat highlight
    d.rounded_rectangle((x + 4, y + 19, x + 26, y + 28), 3, fill=back, outline=dk)         # backrest (south side)
    d.line([(x + 8, y + 22), (x + 22, y + 22)], fill=lt)
    d.line([(x + 6, y + 26), (x + 24, y + 26)], fill=dk)


def wall_panels(d, rect, vertical=False):
    x0, y0, x1, y1 = rect
    d.rectangle(rect, fill=C['wall_w'])
    seq = [C['wall_r'], C['wall_w'], C['wall_g'], C['wall_r'], C['wall_w'], C['wall_w'], C['wall_r'], C['wall_g']]
    n = 0
    if not vertical:
        for x in range(x0, x1 + 1, T):
            for yy in range(y0, y1 + 1, T):
                col = seq[(x // T * 3 + yy // T * 5 + n) % len(seq)]
                d.rectangle((x, yy, x + T - 1, yy + T - 1), fill=col)
                d.line([(x, yy), (x + T - 1, yy)], fill=shade(col, 1.15))
                d.line([(x, yy + T - 1), (x + T - 1, yy + T - 1)], fill=shade(col, .78))
                d.line([(x + T - 1, yy), (x + T - 1, yy + T - 1)], fill=shade(col, .84))
    else:
        for x in range(x0, x1 + 1, T):
            for yy in range(y0, y1 + 1, T):
                col = seq[(x // T * 5 + yy // T * 3 + n) % len(seq)]
                d.rectangle((x, yy, x + T - 1, yy + T - 1), fill=col)
                d.line([(x, yy), (x, yy + T - 1)], fill=shade(col, 1.15))
                d.line([(x, yy + T - 1), (x + T - 1, yy + T - 1)], fill=shade(col, .78))
                d.line([(x + T - 1, yy), (x + T - 1, yy + T - 1)], fill=shade(col, .84))


def screen(d, rect, glow=True):
    x0, y0, x1, y1 = rect
    d.rectangle((x0 - 3, y0 - 3, x1 + 3, y1 + 3), fill=C['frame'])
    d.rectangle(rect, fill=C['screen'])
    d.rectangle((x0, y0, x1, y0 + 2), fill=(120, 255, 130))
    d.rectangle((x0, y1 - 2, x1, y1), fill=C['screen_dk'])
    d.line([(x0 + 3, y0 + 5), (x0 + (x1 - x0) // 3, y0 + 5)], fill=(190, 255, 196))


def double_door(d, x, y, w, h, vertical=False):
    d.rectangle((x, y, x + w - 1, y + h - 1), fill=C['door'], outline=C['wall_edge'])
    if not vertical:
        d.line([(x + w // 2, y + 2), (x + w // 2, y + h - 3)], fill=C['wall_edge'])
        d.rectangle((x + w // 2 - 4, y + h // 2 - 3, x + w // 2 - 3, y + h // 2 + 3), fill=C['gold'])
        d.rectangle((x + w // 2 + 3, y + h // 2 - 3, x + w // 2 + 4, y + h // 2 + 3), fill=C['gold'])
        d.rectangle((x + 3, y + 3, x + w // 2 - 3, y + h - 4), outline=C['door_lt'])
        d.rectangle((x + w // 2 + 3, y + 3, x + w - 4, y + h - 4), outline=C['door_lt'])
    else:
        d.line([(x + 2, y + h // 2), (x + w - 3, y + h // 2)], fill=C['wall_edge'])
        d.rectangle((x + w // 2 - 3, y + h // 2 - 4, x + w // 2 + 3, y + h // 2 - 3), fill=C['gold'])
        d.rectangle((x + w // 2 - 3, y + h // 2 + 3, x + w // 2 + 3, y + h // 2 + 4), fill=C['gold'])
        d.rectangle((x + 3, y + 3, x + w - 4, y + h // 2 - 3), outline=C['door_lt'])
        d.rectangle((x + 3, y + h // 2 + 3, x + w - 4, y + h - 4), outline=C['door_lt'])


def bunting(d, x0, y, x1, vertical=False):
    """red swag along a balcony rail."""
    if not vertical:
        for x in range(x0, x1, 16):
            d.pieslice((x, y - 8, x + 16, y + 8), 0, 180, fill=(190, 30, 38))
            d.arc((x, y - 8, x + 16, y + 8), 0, 180, fill=(110, 14, 22))
    else:
        for yy in range(x0, x1, 16):
            d.pieslice((y - 8, yy, y + 8, yy + 16), 270, 450, fill=(190, 30, 38))
            d.arc((y - 8, yy, y + 8, yy + 16), 270, 450, fill=(110, 14, 22))


def vignette_and_lights(img, lights):
    ov = Image.new('RGBA', img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    for (cx, cy, rad, a) in lights:
        d.ellipse((cx - rad, cy - rad, cx + rad, cy + rad), fill=(255, 224, 150, a))
    ov = ov.filter(ImageFilter.GaussianBlur(26))
    img.alpha_composite(ov)
    v = Image.new('RGBA', img.size, (0, 0, 0, 0))
    dv = ImageDraw.Draw(v)
    dv.rectangle((0, 0, img.width, img.height), outline=(20, 8, 8, 70), width=40)
    v = v.filter(ImageFilter.GaussianBlur(30))
    img.alpha_composite(v)


# ---------------------------------------------------------------- 1F
def draw_1f():
    img = Image.new('RGBA', (PW, PH), C['wood'])
    d = ImageDraw.Draw(img, 'RGBA')
    floor(d, C['wood'], C['wood_dk'], C['wood_lt'], (0, 0, PW - 1, PH - 1))

    # walls --------------------------------------------------------
    wall_panels(d, (0, 0, PW - 1, 2 * T - 1))                                   # top
    wall_panels(d, (0, 2 * T, 2 * T - 1, PH - 1), vertical=True)                # left
    wall_panels(d, (PW - 2 * T, 2 * T, PW - 1, PH - 1), vertical=True)          # right
    wall_panels(d, (2 * T, PH - 2 * T, PW - 2 * T - 1, PH - 1))                 # bottom
    d.rectangle((0, 2 * T - 4, PW - 1, 2 * T - 1), fill=C['wall_edge'])
    d.rectangle((2 * T - 4, 2 * T, 2 * T - 1, PH - 2 * T), fill=C['wall_edge'])
    d.rectangle((PW - 2 * T, 2 * T, PW - 2 * T + 3, PH - 2 * T), fill=C['wall_edge'])

    # under-balcony shadow strips + red swags on the rail line (balcony is overhead, see 2F)
    for (c0, c1) in ((2, 3), (36, 37)):
        d.rectangle((c0 * T, 9 * T, (c1 + 1) * T - 1, 27 * T), fill=(40, 16, 10, 38))
    d.rectangle((2 * T, 27 * T, 38 * T, 28 * T - 1), fill=(40, 16, 10, 30))
    d.rectangle((3 * T, 9 * T, 3 * T + 5, 27 * T), fill=C['rail'])
    d.rectangle((36 * T + 26, 9 * T, 36 * T + 31, 27 * T), fill=C['rail'])
    bunting(d, 9 * T, 3 * T + 8, 27 * T, vertical=True)
    bunting(d, 9 * T, 36 * T + 24, 27 * T, vertical=True)

    # stage ---------------------------------------------------------
    s = STAGE
    sx0, sy0 = s['c0'] * T, s['r0'] * T
    sx1, sy1 = (s['c1'] + 1) * T - 1, (s['r1'] + 1) * T - 1
    floor(d, C['stage'], C['stage_dk'], C['stage_lt'], (sx0, sy0, sx1, sy1 - T), plank=16)
    # gleam on the polished stage
    for k in range(5):
        gx = sx0 + 40 + k * 150
        d.polygon([(gx, sy0 + 100), (gx + 26, sy0 + 100), (gx + 6, sy1 - T), (gx - 20, sy1 - T)], fill=(255, 236, 190, 26))
    # curtains (rows 2-3) with fold shading + red valance
    cx0, cx1 = sx0, sx1
    d.rectangle((cx0, sy0, cx1, sy0 + 2 * T - 1), fill=C['curtain'])
    for x in range(cx0, cx1, 12):
        d.rectangle((x + 4, sy0, x + 7, sy0 + 2 * T - 1), fill=C['curtain_dk'])
        d.rectangle((x, sy0, x + 1, sy0 + 2 * T - 1), fill=C['curtain_lt'])
    d.rectangle((cx0, sy0, cx1, sy0 + 12), fill=C['valance'])
    for x in range(cx0, cx1, 24):
        d.pieslice((x, sy0 + 4, x + 24, sy0 + 26), 0, 180, fill=C['valance'], outline=(100, 16, 20))
    # main screen on the back wall above the curtain
    ms = MAIN_SCREEN
    screen(d, (ms['c0'] * T, 5, (ms['c1'] + 1) * T - 1, 2 * T - 10))
    # hall banner above the screen (plain, text on the photo banner is not legible)
    d.rectangle((9 * T, 2, 14 * T - 1, 22), fill=(28, 24, 24), outline=C['gold_dk'])
    d.rectangle((25 * T, 2, 30 * T - 1, 22), fill=(28, 24, 24), outline=C['gold_dk'])
    for bx in (9 * T, 25 * T):
        for k in range(5):
            d.rectangle((bx + 10 + k * 28, 9, bx + 22 + k * 28, 15), fill=C['gold_dk'])
    # side couplet boards flanking the stage
    for bx in (8 * T - 22, 32 * T + 4):
        d.rectangle((bx, 3 * T, bx + 17, 7 * T - 4), fill=(28, 24, 24), outline=C['gold_dk'])
        for k in range(6):
            d.rectangle((bx + 6, 3 * T + 8 + k * 17, bx + 11, 3 * T + 16 + k * 17), fill=C['gold_dk'])
    # stage lip + steps
    d.rectangle((sx0, sy1 - T + 1, sx1, sy1), fill=C['lip'])
    d.rectangle((sx0, sy1 - T + 1, sx1, sy1 - T + 4), fill=C['stage_lt'])
    d.rectangle((sx0, sy1 - 6, sx1, sy1), fill=shade(C['lip'], .78))
    st = STEPS
    for i in range(3):
        d.rectangle((st['c0'] * T, sy1 - T + 4 + i * 9, (st['c1'] + 1) * T - 1, sy1 - T + 12 + i * 9),
                    fill=shade(C['stage'], .86 - i * .08), outline=C['stage_dk'])
    # podium
    px0, py0 = 19 * T + 2, 5 * T
    d.rounded_rectangle((px0 + 3, py0 + 5, px0 + 59, py0 + 51), 4, fill=(0, 0, 0, 70))
    d.rounded_rectangle((px0, py0, px0 + 56, py0 + 46), 4, fill=(150, 88, 52), outline=C['lip'])
    d.rectangle((px0 + 4, py0 + 4, px0 + 52, py0 + 14), fill=(190, 122, 78))
    d.rectangle((px0 + 20, py0 + 24, px0 + 36, py0 + 38), fill=(120, 30, 34), outline=C['gold'])

    # side wall screens + 2F doors beside the stage -----------------
    for side, cfg in SIDE_SCREENS.items():
        x0 = cfg['c0'] * T + (6 if side == 'L' else 14)
        d.rectangle((x0 - 3, cfg['r0'] * T + 3, x0 + 14 + 3, (cfg['r1'] + 1) * T - 3), fill=C['frame'])
        d.rectangle((x0, cfg['r0'] * T + 6, x0 + 14, (cfg['r1'] + 1) * T - 6), fill=C['screen'])
        d.rectangle((x0, cfg['r0'] * T + 6, x0 + 14, cfg['r0'] * T + 9), fill=(120, 255, 130))
    for side, cfg in SIDE_DOORS_2F.items():
        x = cfg['c'] * T - (0 if side == 'L' else 0)
        y0 = cfg['r0'] * T
        h = (cfg['r1'] - cfg['r0'] + 1) * T
        double_door(d, x if side == 'L' else x, y0, T, h, vertical=True)
        # stair sign: arrow chevrons to say "up"
        cx = x + 16
        for k in range(3):
            yy = y0 + 20 + k * 14
            d.line([(cx - 7, yy + 6), (cx, yy), (cx + 7, yy + 6)], fill=C['gold'], width=2)
    for (c, r) in DECOR_DOORS:
        double_door(d, c * T, r * T, T, 2 * T - 6, vertical=True)

    # carpet --------------------------------------------------------
    k = CARPET
    cx0, cx1 = k['c0'] * T, (k['c1'] + 1) * T - 1
    d.rectangle((cx0, k['r0'] * T, cx1, PH - 1), fill=C['carpet'])
    d.rectangle((cx0, k['r0'] * T, cx0 + 3, PH - 1), fill=C['gold'])
    d.rectangle((cx1 - 3, k['r0'] * T, cx1, PH - 1), fill=C['gold'])
    d.rectangle((cx0 + 4, k['r0'] * T, cx0 + 5, PH - 1), fill=C['gold_dk'])
    d.rectangle((cx1 - 5, k['r0'] * T, cx1 - 4, PH - 1), fill=C['gold_dk'])
    for y in range(k['r0'] * T, PH, 8):
        d.line([(cx0 + 6, y), (cx1 - 6, y)], fill=C['carpet_dk'])
    d.line([((cx0 + cx1) // 2, k['r0'] * T), ((cx0 + cx1) // 2, PH - 1)], fill=C['carpet_lt'])

    # seats ---------------------------------------------------------
    for side in ('L', 'R'):
        a, b = YELLOW[side]
        for r in range(YELLOW['r0'], YELLOW['r1'] + 1):
            for c in range(a, b + 1):
                chair(d, c, r, C['y_seat'], C['y_back'], C['y_dk'], C['y_lt'])
        a, b = RED_FRONT[side]
        for r in range(RED_FRONT['r0'], RED_FRONT['r1'] + 1):
            for c in range(a, b + 1):
                chair(d, c, r, C['r_seat'], C['r_back'], C['r_dk'], C['r_lt'])
        a, b = RED_REAR[side]
        for r in range(RED_REAR['r0'], RED_REAR['r1'] + 1):
            for c in range(a, b + 1):
                chair(d, c, r, C['r_seat'], C['r_back'], C['r_dk'], C['r_lt'])

    # exit ----------------------------------------------------------
    e = EXIT
    ex0, ey0, ex1 = e['c0'] * T, e['r0'] * T, (e['c1'] + 1) * T - 1
    d.rectangle((ex0 - 6, ey0, ex1 + 6, PH - 1), fill=C['wall_edge'])
    d.rectangle((ex0, ey0, ex1, PH - 1), fill=C['exit_glow'])
    d.rectangle((ex0, ey0, ex1, ey0 + 3), fill=(255, 255, 255))
    d.rectangle((ex0 + 2 * T - 1, ey0, ex0 + 2 * T, PH - 1), fill=(220, 214, 190))
    d.rectangle((ex0, PH - 8, ex1, PH - 1), fill=(210, 200, 170))
    for i, ch in enumerate('EXIT'):                                       # tiny pixel sign above exit
        d.rectangle((ex0 + 10 + i * 28, ey0 - 14, ex0 + 30 + i * 28, ey0 - 4), fill=(20, 120, 60))
    d.text((ex0 + 38, ey0 - 14), 'EXIT', fill=(255, 255, 255))

    # pillars -------------------------------------------------------
    for (c, r) in PILLARS:
        d.ellipse((c * T + 3, r * T + 22, c * T + 29, r * T + 36), fill=(0, 0, 0, 80))
        d.rectangle((c * T + 4, r * T, c * T + 27, r * T + 30), fill=C['pillar'], outline=C['pillar_dk'])
        d.rectangle((c * T + 7, r * T + 2, c * T + 10, r * T + 28), fill=(255, 226, 110))
        d.rectangle((c * T + 22, r * T + 2, c * T + 25, r * T + 28), fill=C['pillar_dk'])

    # control booth -------------------------------------------------
    b = BOOTH
    bx0, by0, bx1, by1 = b['c0'] * T, b['r0'] * T, (b['c1'] + 1) * T - 1, (b['r1'] + 1) * T - 1
    d.rectangle((bx0, by0, bx1, by1), fill=(176, 186, 198))                      # booth floor
    for y in range(by0, by1, 16):
        d.line([(bx0, y), (bx1, y)], fill=(158, 168, 182))
    for x in range(bx0, bx1, 16):
        d.line([(x, by0), (x, by1)], fill=(164, 174, 188))
    d.rectangle((bx0, by0, bx1, by0 + 5), fill=C['glass_dk'])                   # north glass
    d.rectangle((bx0, by0 + 6, bx1, by0 + 9), fill=(214, 238, 246, 170))
    d.rectangle((bx0, by0, bx0 + 5, by1), fill=C['glass_dk'])                   # west glass
    for gx in range(bx0 + 40, bx1, 64):
        d.line([(gx, by0), (gx, by0 + 9)], fill=(236, 248, 252))
    # desk along the south wall with two monitors, a mixer and a rack
    dy0 = (b['r1']) * T
    d.rectangle((bx0 + 6, dy0, bx1, by1), fill=C['desk'], outline=C['desk_dk'])
    d.rectangle((bx0 + 6, dy0, bx1, dy0 + 3), fill=(206, 182, 150))
    d.rounded_rectangle((bx0 + 24, dy0 + 5, bx0 + 104, by1 - 3), 3, fill=C['mixer'], outline=(20, 20, 26))    # mixer
    for i in range(10):
        d.rectangle((bx0 + 30 + i * 7, dy0 + 10, bx0 + 33 + i * 7, dy0 + 22), fill=(110, 200, 120) if i % 3 else (230, 190, 70))
    d.rectangle((bx0 + 120, dy0 + 4, bx0 + 164, by1 - 4), fill=C['mon'], outline=(10, 14, 20))                  # monitor 1
    d.rectangle((bx0 + 123, dy0 + 7, bx0 + 161, by1 - 8), fill=C['mon_scr'])
    d.rectangle((bx0 + 170, dy0 + 4, bx0 + 214, by1 - 4), fill=C['mon'], outline=(10, 14, 20))                  # monitor 2
    d.rectangle((bx0 + 173, dy0 + 7, bx0 + 211, by1 - 8), fill=(150, 214, 170))
    d.rectangle((bx0 + 226, dy0 + 2, bx1 - 4, by1 - 2), fill=(58, 60, 66), outline=(20, 20, 26))                 # rack
    for i in range(4):
        d.rectangle((bx0 + 230, dy0 + 5 + i * 5, bx1 - 8, dy0 + 8 + i * 5), fill=(30, 32, 38))
    # open door gap on the east side (kept clear in collision)
    d.rectangle((bx1 - 5, (b['r0'] + 1) * T, bx1, (b['r1'] - 0) * T - 1), fill=(176, 186, 198))
    d.line([(bx1, (b['r0'] + 1) * T), (bx1, b['r1'] * T - 1)], fill=C['glass_dk'], width=1)

    # soft ceiling lights + vignette + paper grain -------------------
    lights = [(x, y, 120, 46) for x in range(200, PW, 270) for y in (330, 560, 780)]
    vignette_and_lights(img, lights)
    noise(img, 3)
    return img


# ---------------------------------------------------------------- 2F
def draw_2f(img1):
    """2nd floor: NEEDS_REFERENCE for everything inside the balcony. Shape is limited to what the photos
    show (a balcony running along both side walls and across the rear, red-swag rail, rear screen)."""
    base = Image.new('RGBA', (PW, PH), (22, 12, 10, 255))
    d = ImageDraw.Draw(base, 'RGBA')
    # the hall seen from above, darkened (the void)
    low = img1.copy()
    dark = Image.new('RGBA', low.size, (14, 6, 6, 150))
    low.alpha_composite(dark)
    base.alpha_composite(low)
    # balcony walkway ring
    ring = [(2, 3, 4, 27), (35, 3, 37, 27), (2, 25, 37, 27)]
    for (c0, r0, c1, r1) in ring:
        floor(d, C['floor2'], C['floor2_dk'], shade(C['floor2'], 1.12), tile_rect(c0, r0, c1, r1), plank=16)
    # inner rail with swags
    d.rectangle((5 * T - 8, 3 * T, 5 * T - 1, 25 * T), fill=C['rail'], outline=C['rail_dk'])
    d.rectangle((35 * T, 3 * T, 35 * T + 7, 25 * T), fill=C['rail'], outline=C['rail_dk'])
    d.rectangle((5 * T - 8, 25 * T - 8, 35 * T + 7, 25 * T - 1), fill=C['rail'], outline=C['rail_dk'])
    bunting(d, 3 * T, 5 * T - 4, 25 * T, vertical=True)
    bunting(d, 3 * T, 35 * T + 4, 25 * T, vertical=True)
    bunting(d, 5 * T, 25 * T - 4, 35 * T)
    # outer walls
    wall_panels(d, (0, 0, 2 * T - 1, PH - 1), vertical=True)
    wall_panels(d, (PW - 2 * T, 0, PW - 1, PH - 1), vertical=True)
    wall_panels(d, (2 * T, PH - 2 * T, PW - 2 * T - 1, PH - 1))
    wall_panels(d, (2 * T, 0, PW - 2 * T - 1, 2 * T - 1))
    # stair landings beside the stage (PLACEHOLDER: no photo of the stairwell)
    for (c0, c1) in ((2, 4), (35, 37)):
        for i in range(6):
            y = (3 + i) * T
            d.rectangle((c0 * T, y, (c1 + 1) * T - 1, y + T - 1), fill=shade(C['floor2'], .9 + .02 * i), outline=C['floor2_dk'])
            d.line([(c0 * T, y + 4), ((c1 + 1) * T - 1, y + 4)], fill=shade(C['rail'], .9))
        d.polygon([((c0 + 1) * T + 6, 3 * T + 20), ((c0 + 1) * T + 26, 3 * T + 20), ((c0 + 1) * T + 16, 3 * T + 6)], fill=C['gold'])
    # rear: where the rear screen hangs (shown as its back, dark) + control-booth roof area
    d.rectangle((17 * T, 25 * T + 8, 22 * T + 31, 25 * T + 22), fill=(30, 40, 34), outline=C['frame'])
    # side screens' backs: skip
    # NEEDS_REFERENCE watermark: faint diagonal hatch on the void so nobody mistakes this for a real survey
    hatch = Image.new('RGBA', base.size, (0, 0, 0, 0))
    dh = ImageDraw.Draw(hatch)
    for x in range(-PH, PW, 40):
        dh.line([(x, 0), (x + PH, PH)], fill=(255, 255, 255, 10))
    base.alpha_composite(hatch)
    vignette_and_lights(base, [(x, 440, 100, 36) for x in (260, 640, 1020)])
    noise(base, 3, seed=2)
    return base


def draw_rear_screen_overhead():
    img = Image.new('RGBA', (PW, PH), (0, 0, 0, 0))
    d = ImageDraw.Draw(img, 'RGBA')
    r = REAR_SCREEN
    x0, x1 = r['c0'] * T, (r['c1'] + 1) * T - 1
    y0 = r['r'] * T + 4
    d.rectangle((x0, y0 + 24, x1, y0 + 34), fill=(0, 0, 0, 60))                     # shadow cast on floor
    d.rectangle((x0 - 3, y0 - 3, x1 + 3, y0 + 21), fill=C['frame'])
    d.rectangle((x0, y0, x1, y0 + 18), fill=C['screen'])
    d.rectangle((x0, y0, x1, y0 + 2), fill=(120, 255, 130))
    d.line([(x0 + 3, y0 + 6), (x0 + 60, y0 + 6)], fill=(190, 255, 196))
    return img


# ---------------------------------------------------------------- data
def build_data():
    rects = []   # collision rectangles in px: [x, y, w, h, tag]

    def R(c0, r0, c1, r1, tag):
        rects.append([c0 * T, r0 * T, (c1 - c0 + 1) * T, (r1 - r0 + 1) * T, tag])

    # outer walls (top wall also covers the curtains: stage walkable starts at row 4)
    R(0, 0, 39, 1, 'wall_top')
    R(0, 2, 1, 29, 'wall_left')
    R(38, 2, 39, 29, 'wall_right')
    R(2, 28, 17, 29, 'wall_bottom_l')
    R(22, 28, 37, 29, 'wall_bottom_r')
    # stage
    R(8, 2, 31, 3, 'curtain')
    R(8, 7, 17, 7, 'stage_lip_l')
    R(22, 7, 31, 7, 'stage_lip_r')
    rects.append([19 * T + 2, 5 * T, 56, 46, 'podium'])
    # seat blocks (players use sit-points; blocks themselves are solid)
    for side in ('L', 'R'):
        a, b = YELLOW[side]
        R(a, YELLOW['r0'], b, YELLOW['r1'], f'yellow_{side}')
        a, b = RED_FRONT[side]
        R(a, RED_FRONT['r0'], b, RED_FRONT['r1'], f'red_front_{side}')
        a, b = RED_REAR[side]
        R(a, RED_REAR['r0'], b, RED_REAR['r1'], f'red_rear_{side}')
    # pillars
    for i, (c, r) in enumerate(PILLARS):
        rects.append([c * T + 4, r * T + 4, 24, 26, f'pillar_{i}'])
    # booth: north glass, west glass, desk (door gap on the east side stays open)
    b = BOOTH
    rects.append([b['c0'] * T, b['r0'] * T, (b['c1'] - b['c0'] + 1) * T, 10, 'booth_glass_n'])
    rects.append([b['c0'] * T, b['r0'] * T, 6, (b['r1'] - b['r0'] + 1) * T, 'booth_glass_w'])
    rects.append([b['c0'] * T + 6, b['r1'] * T, (b['c1'] - b['c0'] + 1) * T - 6, T, 'booth_desk'])

    seats = []
    def add_seats(kind, side, cols, rows, label):
        for ri, r in enumerate(range(rows[0], rows[1] + 1)):
            for ci, c in enumerate(range(cols[0], cols[1] + 1)):
                seats.append(dict(id=f'{label}_{side}_{ri + 1}_{ci + 1}', kind=kind,
                                  x=c * T + T // 2, y=r * T + T // 2 + 2, facing='up'))
    for side in ('L', 'R'):
        add_seats('yellow', side, YELLOW[side], (YELLOW['r0'], YELLOW['r1']), 'Y')
        add_seats('red', side, RED_FRONT[side], (RED_FRONT['r0'], RED_FRONT['r1']), 'RF')
        add_seats('red', side, RED_REAR[side], (RED_REAR['r0'], RED_REAR['r1']), 'RR')

    # booth computers (which physical one is "A"/"B" is NOT confirmed by the photos)
    comp_y = BOOTH['r1'] * T - 6
    computers = [
        dict(id='computer_slot_1', x=BOOTH['c0'] * T + 142, y=comp_y, label='Computer 1', default_app='AUDITORIUMC',
             note='NEEDS_REFERENCE: photo 1000088052 shows two monitors side by side but not which is A / B. '
                  'Swap via COMPUTER_ASSIGNMENT in src/config/settings.js'),
        dict(id='computer_slot_2', x=BOOTH['c0'] * T + 192, y=comp_y, label='Computer 2', default_app='MEDIA_PLAYER',
             note='NEEDS_REFERENCE: see computer_slot_1'),
    ]

    data = dict(
        id='auditorium', tile=T, cols=W, rows=H, width=PW, height=PH,
        spawn=dict(x=int(20 * T), y=int(26.5 * T), facing='up'),
        collision=rects,
        seats=seats,
        screens=[
            dict(id='main', label='Main Stage Screen', rect=[MAIN_SCREEN['c0'] * T, 5, 10 * T, 2 * T - 15], layer='floor'),
            dict(id='left', label='Left Screen', rect=[SIDE_SCREENS['L']['c0'] * T + 6, SIDE_SCREENS['L']['r0'] * T + 6, 15, 4 * T - 12], layer='floor', vertical=True),
            dict(id='right', label='Right Screen', rect=[SIDE_SCREENS['R']['c0'] * T + 14, SIDE_SCREENS['R']['r0'] * T + 6, 15, 4 * T - 12], layer='floor', vertical=True),
            dict(id='rear', label='Rear Screen', rect=[REAR_SCREEN['c0'] * T, REAR_SCREEN['r'] * T + 4, 6 * T, 19], layer='overhead',
                 note='hangs above the exit in the photos; drawn in the overhead layer'),
        ],
        computers=computers,
        doors=[
            dict(id='stage_door_left', label='Stage left door', kind='stairs_up', to='auditorium_2f', toSpawn='stairs_left',
                 zone=[2 * T, 3 * T, T, 3 * T], stairs=[[2.5 * T, 4.5 * T], [3.5 * T, 3.5 * T]],
                 note='photos show the door but nothing behind it: stairwell is NEEDS_REFERENCE'),
            dict(id='stage_door_right', label='Stage right door', kind='stairs_up', to='auditorium_2f', toSpawn='stairs_right',
                 zone=[37 * T, 3 * T, T, 3 * T], stairs=[[37.5 * T, 4.5 * T], [36.5 * T, 3.5 * T]],
                 note='same as left door'),
            dict(id='rear_exit', label='Exit', kind='exit', to='school_map', toSpawn='auditorium_entrance',
                 zone=[EXIT['c0'] * T, 28 * T, 4 * T, T],
                 note='campus map is NEEDS_REFERENCE (no photo of the campus layout); exit shows a message until it exists'),
        ],
        interactables=[
            dict(id='podium', label='Podium', x=19.5 * T + 2, y=5.7 * T, r=46, kind='info', text_key='podium'),
        ],
        needs_reference=[
            '2F interior layout', 'stairwell shape and position behind the two stage doors',
            'which booth monitor is Computer A vs B', 'campus map / Buildings 1-3', 'booth door position (assumed east side)',
        ],
    )
    # 2F ---------------------------------------------------------
    c2 = []
    def R2(c0, r0, c1, r1, tag):
        c2.append([c0 * T, r0 * T, (c1 - c0 + 1) * T, (r1 - r0 + 1) * T, tag])
    R2(0, 0, 39, 2, 'wall_top'); R2(0, 0, 1, 29, 'wall_left'); R2(38, 0, 39, 29, 'wall_right')
    R2(0, 28, 39, 29, 'wall_bottom')
    # everything inside the rail is void
    R2(5, 3, 34, 24, 'void')
    data['floor2'] = dict(
        id='auditorium_2f', width=PW, height=PH, collision=c2, needs_reference=True,
        spawns=dict(stairs_left=dict(x=3.5 * T, y=4.5 * T, facing='down'), stairs_right=dict(x=36.5 * T, y=4.5 * T, facing='down')),
        doors=[
            dict(id='stairs_down_left', label='Stairs down', kind='stairs_down', to='auditorium', toSpawn='stage_door_left',
                 zone=[2 * T, 3 * T, 3 * T, T]),
            dict(id='stairs_down_right', label='Stairs down', kind='stairs_down', to='auditorium', toSpawn='stage_door_right',
                 zone=[35 * T, 3 * T, 3 * T, T]),
        ],
        screens=[dict(id='rear_back', label='Rear screen (back)', rect=[17 * T, 25 * T + 8, 6 * T, 14])],
    )
    data['spawns'] = dict(stage_door_left=dict(x=3.5 * T, y=7 * T, facing='down'),
                          stage_door_right=dict(x=36.5 * T, y=7 * T, facing='down'),
                          auditorium_entrance=dict(x=20 * T, y=26.5 * T, facing='up'))
    return data


def main():
    out = os.path.join(ROOT, 'public', 'assets', 'maps')
    os.makedirs(out, exist_ok=True)
    img1 = draw_1f()
    img1.convert('RGB').save(os.path.join(out, 'auditorium_1f.png'), optimize=True)
    draw_2f(img1).convert('RGB').save(os.path.join(out, 'auditorium_2f.png'), optimize=True)
    draw_rear_screen_overhead().save(os.path.join(out, 'auditorium_overhead.png'), optimize=True)
    data = build_data()
    os.makedirs(os.path.join(ROOT, 'src', 'maps'), exist_ok=True)
    with open(os.path.join(ROOT, 'src', 'maps', 'auditoriumMap.js'), 'w') as f:
        f.write('// GENERATED by tools/build_auditorium.py — edit the script, not this file.\n')
        f.write('// Items under needs_reference are NOT confirmed by any uploaded photo.\n')
        f.write('export const AUDITORIUM = ' + json.dumps(data, indent=1) + ';\n')
    # debug overlay
    dbg = img1.copy()
    dd = ImageDraw.Draw(dbg, 'RGBA')
    for x, y, w, h, tag in data['collision']:
        dd.rectangle((x, y, x + w - 1, y + h - 1), fill=(255, 0, 0, 70), outline=(255, 0, 0, 200))
    for s in data['seats']:
        dd.ellipse((s['x'] - 2, s['y'] - 2, s['x'] + 2, s['y'] + 2), fill=(0, 120, 255, 220))
    for dr in data['doors']:
        x, y, w, h = dr['zone']
        dd.rectangle((x, y, x + w, y + h), fill=(255, 255, 0, 90), outline=(255, 255, 0, 255))
    for c in data['computers']:
        dd.ellipse((c['x'] - 6, c['y'] - 6, c['x'] + 6, c['y'] + 6), fill=(0, 255, 255, 220))
    sp = data['spawn']
    dd.ellipse((sp['x'] - 6, sp['y'] - 6, sp['x'] + 6, sp['y'] + 6), fill=(0, 255, 0, 255))
    os.makedirs(os.path.join(ROOT, 'build'), exist_ok=True)
    dbg.convert('RGB').save(os.path.join(ROOT, 'build', 'auditorium_debug.png'))
    print('collision rects', len(data['collision']), 'seats', len(data['seats']))


if __name__ == '__main__':
    main()
