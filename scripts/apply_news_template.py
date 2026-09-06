from pathlib import Path
import hashlib, json
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path('.')
NEWS = ROOT / 'news.json'
OUT = ROOT / 'assets/news'
FONT_CANDIDATES = ['/usr/share/fonts/truetype/noto/NotoSansArabic-Bold.ttf','/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf']

def font(size):
    for p in FONT_CANDIDATES:
        if Path(p).exists(): return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def shape_ar(text):
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
        return get_display(arabic_reshaper.reshape(text))
    except Exception:
        return text

def official_template():
    W=H=1254
    im=Image.new('RGB',(W,H),(5,20,39)); d=ImageDraw.Draw(im)
    d.rectangle((0,0,W,175),fill=(210,25,38))
    d.text((W//2,82),shape_ar('خبر'),font=font(92),fill='white',anchor='mm')
    for x in range(40,W,55):
        for y in range(205,930,55):
            if ((x//55)+(y//55))%3==0:d.ellipse((x,y,x+4,y+4),fill=(28,57,82))
    d.rectangle((0,950,W,H),fill=(3,14,29)); d.rectangle((0,950,18,H),fill=(210,25,38))
    d.text((W//2,1030),shape_ar('التاسعة نيوز'),font=font(62),fill='white',anchor='mm')
    d.text((W//2,1100),shape_ar('نعلم لتعلم'),font=font(38),fill=(210,25,38),anchor='mm')
    return im

def source_path(value):
    p=str(value or '')
    if p.startswith('./'): p=p[2:]
    if p.startswith('assets/'):
        q=ROOT/p
        if q.exists() and q.is_file(): return q
    return None

def fit_cover(photo,size):
    tw,th=size; photo=photo.convert('RGB')
    scale=max(tw/photo.width,th/photo.height)
    nw=max(tw,int(round(photo.width*scale))); nh=max(th,int(round(photo.height*scale)))
    photo=photo.resize((nw,nh),Image.Resampling.LANCZOS)
    return photo.crop(((nw-tw)//2,(nh-th)//2,(nw-tw)//2+tw,(nh-th)//2+th))

def build(template,photo):
    W,H=template.size; y0,y1=175,950
    photo=fit_cover(photo,(W,y1-y0)).filter(ImageFilter.UnsharpMask(radius=1,percent=80,threshold=3))
    canvas=template.copy(); canvas.paste(photo,(0,y0)); return canvas.convert('RGB')

data=json.loads(NEWS.read_text(encoding='utf-8')); template=official_template(); items=data.get('items',[])
if not items: raise SystemExit('لا توجد أخبار لتركيب الصور')
count=0
for item in items:
    # update_news.py stores the real downloaded local image in image.
    # Accept image as the canonical source; original_image is only legacy data.
    src=item.get('image') or item.get('original_image')
    sp=source_path(src)
    if not sp or sp.suffix.lower()=='.svg': raise SystemExit(f'مصدر صورة غير صالح للخبر: {src}')
    try:
        with Image.open(sp) as photo:
            photo.load()
            key=hashlib.sha1((str(item.get('url',''))+'|'+str(item.get('title',''))+'|'+str(sp)).encode()).hexdigest()[:16]
            out=OUT/f'news-template-{key}.jpg'
            build(template,photo).save(out,quality=90,optimize=True,progressive=True)
    except Exception as exc:
        raise SystemExit(f'فشل تجهيز صورة الخبر: {src} — {exc}')
    with Image.open(out) as check:
        check.verify(); assert check.size==(1254,1254); assert check.mode=='RGB'
    item['image']='./assets/news/'+out.name
    item['original_image']=str(src)
    count+=1
if count!=len(items): raise SystemExit(f'فشل تركيب القالب: {count}/{len(items)}')
NEWS.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
print(f'تم تركيب صور الأخبار داخل القالب على {count} خبراً — كل خبر يعتمد على صورته الحقيقية')
