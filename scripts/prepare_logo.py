from PIL import Image
from pathlib import Path
from collections import deque

out=Path('assets/logo-transparent.png')
out.parent.mkdir(parents=True,exist_ok=True)
src_jpg=Path('assets/logo.jpg')
src_svg=Path('logo.svg')

# Prefer the raster logo when present; otherwise render the repository's
# official SVG logo. The old workflow failed here because logo.jpg no longer exists.
if src_jpg.exists():
    im=Image.open(src_jpg).convert('RGBA')
else:
    import cairosvg
    cairosvg.svg2png(url=str(src_svg),write_to=str(out),output_width=900)
    im=Image.open(out).convert('RGBA')

p=im.load(); w,h=im.size
seen=bytearray(w*h); q=deque()
for x in range(w):
    q.append((x,0)); q.append((x,h-1))
for y in range(h):
    q.append((0,y)); q.append((w-1,y))
def bg(px):
    r,g,b,a=px
    return a>0 and r>242 and g>242 and b>242
while q:
    x,y=q.popleft(); i=y*w+x
    if seen[i] or not bg(p[x,y]): continue
    seen[i]=1
    for nx,ny in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
        if 0<=nx<w and 0<=ny<h and not seen[ny*w+nx]: q.append((nx,ny))
for y in range(h):
    for x in range(w):
        if seen[y*w+x]: p[x,y]=(255,255,255,0)
bbox=im.getbbox()
if bbox:
    pad=12
    im=im.crop((max(0,bbox[0]-pad),max(0,bbox[1]-pad),min(w,bbox[2]+pad),min(h,bbox[3]+pad)))
im.save(out,optimize=True)
