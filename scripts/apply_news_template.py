from pathlib import Path
import base64, hashlib, io, json, re
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path('.')
NEWS = ROOT / 'news.json'
TEMPLATE = ROOT / 'assets/news/ninth-news-template.svg'
OUT = ROOT / 'assets/news'

FONT_CANDIDATES = [
    '/usr/share/fonts/truetype/noto/NotoSansArabic-Bold.ttf',
    '/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf',
    '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
]

def font(size):
    for p in FONT_CANDIDATES:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def shape_ar(text):
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
        return get_display(arabic_reshaper.reshape(text))
    except Exception:
        return text

def extract_template():
    raw = TEMPLATE.read_text(encoding='utf-8')
    m = re.search(r'href="data:image/jpeg;base64,([^\"]+)"', raw)
    if not m:
        raise RuntimeError('لم يتم العثور على صورة القالب داخل ninth-news-template.svg')
    return Image.open(io.BytesIO(base64.b64decode(m.group(1)))).convert('RGB')

def source_path(value):
    p = str(value or '')
    if p.startswith('./'):
        q = ROOT / p[2:]
        return q if q.exists() else None
    if p.startswith('assets/'):
        q = ROOT / p
        return q if q.exists() else None
    return None

def wrap_text(draw, text, fnt, max_width):
    words = str(text or '').split()
    lines=[]; cur=''
    for w in words:
        test = (cur+' '+w).strip()
        if draw.textbbox((0,0), shape_ar(test), font=fnt)[2] <= max_width:
            cur=test
        else:
            if cur: lines.append(cur)
            cur=w
    if cur: lines.append(cur)
    return lines[:3]

def build(template, photo, title):
    canvas = template.copy()
    W,H = canvas.size
    y0, y1 = 245, 950
    box_h = y1-y0
    photo = photo.convert('RGB')
    scale=max(W/photo.width, box_h/photo.height)
    nw,nh=int(photo.width*scale),int(photo.height*scale)
    photo=photo.resize((nw,nh),Image.Resampling.LANCZOS)
    left=(nw-W)//2; top=(nh-box_h)//2
    photo=photo.crop((left,top,left+W,top+box_h))
    photo=photo.filter(ImageFilter.UnsharpMask(radius=1, percent=80, threshold=3))
    canvas.paste(photo,(0,y0))
    overlay=Image.new('RGBA',(W,box_h),(0,0,0,0))
    od=ImageDraw.Draw(overlay)
    panel_y=box_h-210
    od.rounded_rectangle((55,panel_y,W-55,box_h-28),radius=12,fill=(3,20,42,218),outline=(226,29,43,235),width=4)
    canvas=Image.alpha_composite(canvas.convert('RGBA'),overlay)
    d=ImageDraw.Draw(canvas)
    f=font(46 if len(str(title))<70 else 40)
    lines=wrap_text(d,title,f,W-180)
    line_h=58
    total=len(lines)*line_h
    y=y0+panel_y+(box_h-panel_y-total)//2-4
    for line in lines:
        t=shape_ar(line)
        bb=d.textbbox((0,0),t,font=f)
        x=(W-(bb[2]-bb[0]))//2
        d.text((x+2,y+2),t,font=f,fill=(0,0,0,170))
        d.text((x,y),t,font=f,fill='white')
        y+=line_h
    return canvas.convert('RGB')

data=json.loads(NEWS.read_text(encoding='utf-8'))
template=extract_template()
count=0
for item in data.get('items',[]):
    src=item.get('original_image') or item.get('image')
    sp=source_path(src)
    if not sp or sp.suffix.lower()=='.svg':
        continue
    try:
        photo=Image.open(sp)
        key=hashlib.sha1((str(item.get('url',''))+'|'+str(item.get('title',''))+'|'+str(sp)).encode()).hexdigest()[:16]
        out=OUT/f'news-template-{key}.jpg'
        build(template,photo,item.get('title','خبر من التاسعة نيوز')).save(out,quality=88,optimize=True,progressive=True)
        item['original_image']=str(src)
        item['image']='./assets/news/'+out.name
        count+=1
    except Exception as e:
        print(f'تعذر تجهيز صورة: {sp}: {e}')
NEWS.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
print(f'تم تطبيق قالب التاسعة نيوز على {count} خبراً')
