from pathlib import Path
import hashlib,json
from PIL import Image,ImageDraw,ImageFont,ImageFilter
ROOT=Path('.');NEWS=ROOT/'news.json';OUT=ROOT/'assets/news';OUT.mkdir(parents=True,exist_ok=True)
FONT_CANDIDATES=['/usr/share/fonts/truetype/noto/NotoSansArabic-Bold.ttf','/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf']
def font(size):
 for p in FONT_CANDIDATES:
  if Path(p).exists():return ImageFont.truetype(p,size)
 return ImageFont.load_default()
def shape_ar(text):
 try:
  import arabic_reshaper
  from bidi.algorithm import get_display
  return get_display(arabic_reshaper.reshape(text))
 except:return text
def official_template():
 W=H=1254;im=Image.new('RGB',(W,H),(5,20,39));d=ImageDraw.Draw(im);d.rectangle((0,0,W,175),fill=(210,25,38));d.text((W//2,82),shape_ar('خبر'),font=font(92),fill='white',anchor='mm')
 for x in range(40,W,55):
  for y in range(205,930,55):
   if ((x//55)+(y//55))%3==0:d.ellipse((x,y,x+4,y+4),fill=(28,57,82))
 d.rectangle((0,950,W,H),fill=(3,14,29));d.rectangle((0,950,18,H),fill=(210,25,38));d.text((W//2,1030),shape_ar('التاسعة نيوز'),font=font(62),fill='white',anchor='mm');d.text((W//2,1100),shape_ar('نعلم لتعلم'),font=font(38),fill=(210,25,38),anchor='mm');return im
def source_path(v):
 p=str(v or '').strip();p=p[2:] if p.startswith('./') else p
 if not p.startswith('assets/news/') or 'news-template-' in Path(p).name:return None
 q=ROOT/p
 return q if q.exists() and q.is_file() else None
def fit_cover(photo,size):
 tw,th=size;photo=photo.convert('RGB');s=max(tw/photo.width,th/photo.height);nw=max(tw,round(photo.width*s));nh=max(th,round(photo.height*s));photo=photo.resize((nw,nh),Image.Resampling.LANCZOS);return photo.crop(((nw-tw)//2,(nh-th)//2,(nw-tw)//2+tw,(nh-th)//2+th))
def build(template,photo):
 photo=fit_cover(photo,(1254,775)).filter(ImageFilter.UnsharpMask(radius=1,percent=80,threshold=3));c=template.copy();c.paste(photo,(0,175));return c.convert('RGB')
data=json.loads(NEWS.read_text(encoding='utf-8'));items=data.get('items',[])
if not items:raise SystemExit('لا توجد أخبار لتركيب الصور')
template=official_template()
for item in items:
 src=item.get('original_image') or item.get('image');sp=source_path(src)
 if not sp:raise SystemExit(f'مصدر صورة حقيقي غير صالح للخبر: {src}')
 try:
  with Image.open(sp) as photo:
   photo.load();key=hashlib.sha1((str(item.get('url',''))+'|'+str(item.get('title',''))+'|'+str(sp)).encode()).hexdigest()[:16];out=OUT/f'news-template-{key}.jpg';build(template,photo).save(out,quality=90,optimize=True,progressive=True)
  with Image.open(out) as check:check.verify();assert check.size==(1254,1254) and check.mode=='RGB'
 except Exception as exc:raise SystemExit(f'فشل تجهيز صورة الخبر: {src} — {exc}')
 item['image']='./assets/news/'+out.name;item['original_image']=str(src)
NEWS.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8');print('تم تركيب صور الأخبار داخل القالب:',len(items))
