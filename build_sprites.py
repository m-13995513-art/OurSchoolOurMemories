"""Step 2 of the character pipeline: align + scale + derive + pack.

Input : build/frames/<gender>_<role>/<n>.png   (from clean_frames.py)
        originals/1000088018.png ... sitting art (cleaned here)
Output: public/assets/characters/characters_<gender>.png  (atlas)
        public/assets/characters/characters_<gender>.json (Phaser JSON-hash atlas)
        public/assets/characters/animations.json          (animation table + provenance)
        build/preview_<gender>.png                         (contact sheet for review)

Every animation carries a `source` field so nothing generated is passed off as
original GIF content:
    gif        - frames taken straight from an uploaded GIF
    gif-still  - a single frame of an uploaded GIF used as a still pose
    mirrored   - horizontal mirror of a gif animation (left -> right)
    art        - cleaned still from an uploaded sitting image
    generated  - procedurally derived by this script (lean / bob / hop / fold)
"""
import os, json, glob, math
import numpy as np
from PIL import Image, ImageOps
from scipy import ndimage as ndi

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FR = os.path.join(ROOT, 'build', 'frames')
OUT = os.path.join(ROOT, 'public', 'assets', 'characters')
os.makedirs(OUT, exist_ok=True)

CW, CH = 128, 120          # canvas of one frame
BASE_Y = 114               # feet baseline inside the canvas
CX = CW // 2               # torso centre x
TARGET_H = 96              # standing character height in px


def load_frames(key):
    files = sorted(glob.glob(os.path.join(FR, key, '*.png')), key=lambda p: int(os.path.basename(p)[:-4]))
    return [Image.open(f).convert('RGBA') for f in files]


def torso_cx(im):
    a = np.asarray(im)[..., 3] > 0
    h = a.shape[0]
    rows = a[int(h * .40):int(h * .66)]
    ys, xs = np.where(rows)
    return xs.mean() if len(xs) else im.width / 2


def place(im, scale, bob=0, dx=0):
    """scale, then drop onto the canvas: feet on BASE_Y, torso on CX."""
    w, h = max(1, round(im.width * scale)), max(1, round(im.height * scale))
    cx = torso_cx(im) * scale
    pm = np.asarray(im).astype(np.float32)
    pm[..., :3] *= pm[..., 3:4] / 255.0               # premultiply -> no white halos when resizing
    t = Image.fromarray(pm.astype(np.uint8), 'RGBA').resize((w, h), Image.LANCZOS)
    arr = np.asarray(t).astype(np.float32)
    a = arr[..., 3:4]
    rgb = np.where(a > 0, arr[..., :3] * 255.0 / np.maximum(a, 1), 0)
    # crisp pixel-art edge: binarise alpha instead of leaving a soft fringe
    a2 = np.where(a >= 110, 255, 0)
    out = Image.fromarray(np.dstack([np.clip(rgb, 0, 255), a2]).astype(np.uint8), 'RGBA')
    can = Image.new('RGBA', (CW, CH), (0, 0, 0, 0))
    can.alpha_composite(out, (int(round(CX - cx + dx)), int(round(BASE_Y - h + bob))))
    return can


def unit_scale(frames):
    hs = sorted(f.height for f in frames)
    return TARGET_H / hs[len(hs) // 2]


def lean(can, k):
    """shear around the feet so the body leans (k>0 leans to the left, k<0 to the right)."""
    return can.transform(can.size, Image.AFFINE, (1, -k, k * BASE_Y, 0, 1, 0), Image.NEAREST)


def squash(can, sy, sx=1.0):
    w, h = can.size
    nw, nh = round(w * sx), round(h * sy)
    r = can.resize((nw, nh), Image.NEAREST)
    out = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    out.alpha_composite(r, (CX - nw // 2, BASE_Y - round(BASE_Y * sy)))
    return out


def clean_still(path, gender):
    """clean a single sitting image with the same method as clean_frames."""
    import importlib.util
    spec = importlib.util.spec_from_file_location('cf', os.path.join(ROOT, 'tools', 'clean_frames.py'))
    cf = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cf)
    rgb = np.asarray(Image.open(path).convert('RGB'))
    return cf.clean(rgb, gender)


def fold_sit(can):
    """generated sitting pose from a standing canvas: keep the upper body, fold the
    lower legs into a short, forward-pointing stub (chair hides the rest)."""
    a = np.asarray(can)
    ys = np.where(a[..., 3].any(axis=1))[0]
    top, bot = ys.min(), ys.max()
    hem = int(top + (bot - top) * 0.76)               # just below the shorts / skirt
    upper = can.crop((0, 0, CW, hem))
    legs = can.crop((0, hem, CW, bot + 1))
    legs = legs.resize((legs.width, max(4, int(legs.height * 0.5))), Image.NEAREST)
    out = Image.new('RGBA', (CW, CH), (0, 0, 0, 0))
    drop = 10                                          # body sinks onto the seat
    out.alpha_composite(upper, (0, drop))
    out.alpha_composite(legs, (0, hem + drop - 4))
    # re-anchor so the lowest pixel sits on BASE_Y again
    arr = np.asarray(out)
    lo = np.where(arr[..., 3].any(axis=1))[0].max()
    shifted = Image.new('RGBA', (CW, CH), (0, 0, 0, 0))
    shifted.alpha_composite(out, (0, BASE_Y - lo))
    return shifted


def build(gender):
    base = f'{gender}_'
    fi = load_frames(base + 'front_idle')
    fw = load_frames(base + 'front_walk')
    bw = load_frames(base + 'back_walk')
    lw = load_frames(base + 'left_walk')

    # ONE scale per character, from the walk cycle of the front view, so every
    # direction keeps the same size ratio (side/back were drawn at a different zoom,
    # so each sheet is normalised by its own median height to the same TARGET_H).
    S = {k: unit_scale(v) for k, v in dict(fi=fi, fw=fw, bw=bw, lw=lw).items()}
    anims = {}   # name -> dict(frames=[Image], fps, loop, source, note)

    def add(name, frames, fps, source, loop=True, note=''):
        anims[name] = dict(frames=frames, fps=fps, loop=loop, source=source, note=note)

    P_fi = [place(f, S['fi']) for f in fi]
    P_fw = [place(f, S['fw']) for f in fw]
    P_bw = [place(f, S['bw']) for f in bw]
    P_lw = [place(f, S['lw']) for f in lw]

    add('front_idle', P_fi, 4, 'gif', note='uploaded idle GIF; motion marks removed')
    add('front_walk', P_fw[1:] + P_fw[:1], 8, 'gif')
    add('back_walk', P_bw[1:] + P_bw[:1], 8, 'gif')
    add('left_walk', P_lw[1:] + P_lw[:1], 8, 'gif')
    add('back_idle', [P_bw[0]], 1, 'gif-still', note='walk frame 0 (standing pose)')
    add('left_idle', [P_lw[0]], 1, 'gif-still', note='walk frame 0 (standing pose)')

    # right = mirrored left. Backpack stays behind the body, so mirroring is geometrically correct.
    add('right_walk', [ImageOps.mirror(f) for f in anims['left_walk']['frames']], 8, 'mirrored',
        note='mirror of left_walk; reviewed in build/preview_*.png')
    add('right_idle', [ImageOps.mirror(P_lw[0])], 1, 'mirrored')

    # ---- run: NOT a faster walk. 6 frames, stronger bob, forward lean, longer bounce ----
    def run(walk_frames, k):
        fr = walk_frames[:-1] if len(walk_frames) > 6 else walk_frames
        pick = [fr[i % len(fr)] for i in (0, 2, 3, 4, 6, 7)]
        out = []
        for i, f in enumerate(pick):
            bob = -7 if i % 3 == 1 else (-3 if i % 3 == 2 else 0)
            f = lean(f, k) if k else f
            f = ImageChops_offset(f, 0, bob)
            out.append(f)
        return out

    add('front_run', run(anims['front_walk']['frames'], 0.0), 12, 'generated',
        note='lean-free bob + stride from walk frames; hand-tuned, not original art')
    add('back_run', run(anims['back_walk']['frames'], 0.0), 12, 'generated')
    add('left_run', run(anims['left_walk']['frames'], 0.14), 12, 'generated',
        note='forward lean (shear) + bob')
    add('right_run', run(anims['right_walk']['frames'], -0.14), 12, 'generated')

    # ---- sit ----
    sit_dir = {}
    if gender == 'female':
        sf = clean_still(os.path.join(ROOT, 'originals', '1000088049.jpg'), 'female')
        sb = clean_still(os.path.join(ROOT, 'originals', '1000088051.jpg'), 'female')
        # match head width of the standing sprite so sitting girl is the same size
        def head_w(im):
            a = np.asarray(im)[..., 3] > 0
            h = a.shape[0]
            ys, xs = np.where(a[:int(h * .35)])
            return xs.max() - xs.min() + 1
        ref = head_w(fw[0]) * S['fw']
        s_f = min(ref / head_w(sf), 104 / sf.height)
        sit_dir['front'] = place(sf, s_f)
        # back view: hair is the widest part as well
        s_b = min((head_w(bw[0]) * S['bw']) / head_w(sb), 104 / sb.height)
        sit_dir['back'] = place(sb, s_b)
        add('sit_front', [sit_dir['front']], 1, 'art', note='cleaned from uploaded sitting image 1000088049.jpg')
        add('sit_back', [sit_dir['back']], 1, 'art', note='cleaned from uploaded sitting image 1000088051.jpg')
    else:
        add('sit_front', [fold_sit(P_fw[0])], 1, 'generated',
            note='no uploaded male sitting art: upper body of walk frame 0 + folded legs')
        add('sit_back', [fold_sit(P_bw[0])], 1, 'generated')
    add('sit_left', [fold_sit(P_lw[0])], 1, 'generated', note='no uploaded side sitting art')
    add('sit_right', [ImageOps.mirror(fold_sit(P_lw[0]))], 1, 'generated')

    # ---- interact: a small hop + squash, per direction (generated) ----
    hop = [0, -5, -9, -5, 0, 2, 0]
    sq = [(1, 1), (1.02, .98), (1.0, 1.03), (1.02, .98), (1, 1), (1.03, .96), (1, 1)]
    for d, still in (('front', P_fi[0]), ('back', P_bw[0]), ('left', P_lw[0]), ('right', ImageOps.mirror(P_lw[0]))):
        fr = []
        for b, (sx, sy) in zip(hop, sq):
            f = squash(still, sy, sx)
            fr.append(ImageChops_offset(f, 0, b))
        add(f'interact_{d}', fr, 10, 'generated', loop=False, note='hop to show the interaction; no arm art in source')

    return anims


def ImageChops_offset(im, dx, dy):
    out = Image.new('RGBA', im.size, (0, 0, 0, 0))
    out.alpha_composite(im, (dx, dy)) if dy >= 0 else out.alpha_composite(im.crop((0, -dy, im.width, im.height)), (dx, 0))
    return out


def pack(gender, anims):
    names, ims = [], []
    for n, a in anims.items():
        for i, f in enumerate(a['frames']):
            names.append(f'{n}_{i}')
            ims.append(f)
    cols = 12
    rows = math.ceil(len(ims) / cols)
    atlas = Image.new('RGBA', (cols * CW, rows * CH), (0, 0, 0, 0))
    frames = {}
    for k, (n, f) in enumerate(zip(names, ims)):
        x, y = (k % cols) * CW, (k // cols) * CH
        atlas.alpha_composite(f, (x, y))
        frames[n] = dict(frame=dict(x=x, y=y, w=CW, h=CH), rotated=False, trimmed=False,
                         spriteSourceSize=dict(x=0, y=0, w=CW, h=CH), sourceSize=dict(w=CW, h=CH))
    atlas.save(os.path.join(OUT, f'characters_{gender}.png'), optimize=True)
    json.dump(dict(frames=frames, meta=dict(app='tools/build_sprites.py', image=f'characters_{gender}.png',
                                            format='RGBA8888', size=dict(w=atlas.width, h=atlas.height), scale='1')),
              open(os.path.join(OUT, f'characters_{gender}.json'), 'w'), indent=1)
    # preview on a mid-grey checker so halos are visible
    prev = Image.new('RGBA', atlas.size, (95, 120, 150, 255))
    prev.alpha_composite(atlas)
    prev.convert('RGB').save(os.path.join(ROOT, 'build', f'preview_{gender}.png'))
    return atlas.size, len(ims)


def main():
    table = dict(canvas=dict(w=CW, h=CH), anchor=dict(x=CX / CW, y=BASE_Y / CH), anims={})
    for g in ('male', 'female'):
        anims = build(g)
        size, n = pack(g, anims)
        table['anims'][g] = {k: dict(count=len(v['frames']), fps=v['fps'], loop=v['loop'], source=v['source'], note=v['note'])
                              for k, v in anims.items()}
        print(g, 'atlas', size, 'frames', n, 'anims', len(anims))
    json.dump(table, open(os.path.join(OUT, 'animations.json'), 'w'), indent=1, ensure_ascii=False)


if __name__ == '__main__':
    main()
