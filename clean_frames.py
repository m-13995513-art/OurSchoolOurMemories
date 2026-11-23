"""Step 1 of the character pipeline.

Reads the ORIGINAL GIFs (never modified) and writes cleaned, trimmed RGBA frames
to build/frames/<id>/<n>.png.  Cleaning = background removal, shadow removal,
motion-line removal, halo trimming.  Nothing here is scaled or aligned yet.

Run:  python3 -I tools/clean_frames.py
"""
import os, sys, json
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'originals')
OUT = os.path.join(ROOT, 'build', 'frames')

# id -> (gender, role)   (verified against the contact sheet, not assumed)
SHEETS = {
    '014': ('male', 'front_idle'),
    '016': ('male', 'front_walk'),
    '019': ('male', 'back_walk'),
    '040': ('male', 'left_walk'),
    '015': ('female', 'front_idle'),
    '017': ('female', 'front_walk'),
    '020': ('female', 'back_walk'),
    '041': ('female', 'left_walk'),
}


def border_color(a):
    h, w, _ = a.shape
    ring = np.concatenate([a[:6].reshape(-1, 3), a[-6:].reshape(-1, 3),
                           a[:, :6].reshape(-1, 3), a[:, -6:].reshape(-1, 3)])
    return np.median(ring, axis=0)


def clean(rgb, gender):
    a = rgb.astype(np.float32)
    h, w, _ = a.shape
    bg = border_color(a)
    dist = np.sqrt(((a - bg) ** 2).sum(axis=2))
    r, g, b = a[..., 0], a[..., 1], a[..., 2]

    if gender == 'male':
        bg_like = dist < 38
        # darker blue floor shadow under the feet
        shadow_like = (b > 165) & (r < 150) & (g > 100) & (b - r > 60)
    else:
        bg_like = dist < 22
        # lavender floor shadow
        shadow_like = (r > 170) & (r < 228) & (b - g > 8) & (b > 195) & (np.abs(r - g) < 22)

    cand = bg_like | shadow_like
    lab, n = ndi.label(cand)
    # components of "background or shadow" that touch the image border
    border_ids = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    bgmask = np.isin(lab, list(border_ids))
    # shadows are enclosed by feet outlines only at one side, so also take shadow
    # components that sit in the lower 35% and touch an already-removed region
    low = np.zeros_like(cand)
    low[int(h * 0.62):] = True
    sh_lab, sn = ndi.label(shadow_like & low)
    grown = ndi.binary_dilation(bgmask, iterations=2)
    for i in range(1, sn + 1):
        comp = sh_lab == i
        if (comp & grown).any() and comp.sum() > 20:
            bgmask |= comp

    fg = ~bgmask
    fg = ndi.binary_opening(fg, iterations=1)
    flab, fn = ndi.label(fg)
    if fn == 0:
        return None
    areas = ndi.sum(fg, flab, index=range(1, fn + 1))
    big = int(np.argmax(areas)) + 1
    keep = flab == big
    ys, xs = np.where(keep)
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    # keep other pieces only if big enough (hair wisps), drop motion lines / sparkles
    for i in range(1, fn + 1):
        if i == big:
            continue
        comp = flab == i
        if areas[i - 1] > 0.035 * areas[big - 1]:
            cy, cx = ndi.center_of_mass(comp)
            if x0 - 20 <= cx <= x1 + 20 and y0 - 20 <= cy <= y1 + 20:
                keep |= comp
    keep = ndi.binary_fill_holes(keep)
    # trim 1px colour halo from the background
    core = ndi.binary_erosion(keep, iterations=1)
    alpha = (core * 255).astype(np.uint8)
    out = np.dstack([rgb, alpha])
    ys, xs = np.where(core)
    return Image.fromarray(out, 'RGBA').crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))


def main():
    report = {}
    for sid, (gender, role) in SHEETS.items():
        im = Image.open(os.path.join(SRC, f'1000088{sid}.gif'))
        d = os.path.join(OUT, f'{gender}_{role}')
        os.makedirs(d, exist_ok=True)
        frames = []
        for i in range(im.n_frames):
            im.seek(i)
            rgb = np.asarray(im.convert('RGB'))
            c = clean(rgb, gender)
            if c is None:
                print('EMPTY', sid, i)
                continue
            c.save(os.path.join(d, f'{i}.png'))
            frames.append(dict(i=i, w=c.width, h=c.height, ms=im.info.get('duration', 0)))
        report[f'{gender}_{role}'] = dict(source=f'1000088{sid}.gif', frames=frames)
        print(gender, role, len(frames), 'frames')
    json.dump(report, open(os.path.join(ROOT, 'build', 'frames.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
