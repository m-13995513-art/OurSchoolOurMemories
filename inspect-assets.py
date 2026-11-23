import sys, os, glob, json
from PIL import Image
rows=[]
for p in sorted(glob.glob(sys.argv[1]+'/*')):
    im=Image.open(p)
    n=getattr(im,'n_frames',1)
    durs=[]
    for i in range(n):
        im.seek(i); durs.append(im.info.get('duration',0))
    im.seek(0)
    rgba=im.convert('RGBA')
    c=rgba.getpixel((2,2))
    tr=any(px[3]<255 for px in list(rgba.getdata())[::97])
    rows.append(dict(file=os.path.basename(p),fmt=im.format,size=os.path.getsize(p),w=im.width,h=im.height,frames=n,dur=sorted(set(durs)),loop=im.info.get('loop'),corner=c,transparent=tr))
for r in rows: print(json.dumps(r,ensure_ascii=False))
json.dump(rows,open('tools/inspect-report.json','w'),ensure_ascii=False,indent=1)
