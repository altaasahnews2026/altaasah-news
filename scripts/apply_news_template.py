from pathlib import Path
import json, re
from PIL import Image
ROOT=Path('.')
NEWS=ROOT/'news.json'

def valid_source(value):
    p=str(value or '').strip()
    p=p[2:] if p.startswith('./') else p
    if not (p.startswith('assets/news/') or p.startswith('assets/editorial/')):
        return None
    q=ROOT/p
    return q if q.exists() and q.is_file() else None

def valid_image(path):
    if path.suffix.lower()=='.svg':
        s=path.read_text(encoding='utf-8', errors='ignore')[:5000]
        return bool(re.search(r'<svg\b', s, re.I) and re.search(r'width=["\'](?:\d+)', s, re.I) and re.search(r'height=["\'](?:\d+)', s, re.I))
    with Image.open(path) as im:
        im.verify()
    with Image.open(path) as im:
        if im.width<360 or im.height<220:
            return False
    return True

data=json.loads(NEWS.read_text(encoding='utf-8'))
items=data.get('items',[])
if len(items)<20:
    raise SystemExit(f'لا توجد أخبار كافية: {len(items)}')
for item in items:
    src=item.get('original_image') or item.get('image')
    path=valid_source(src)
    if not path:
        raise SystemExit(f'صورة خام غير صالحة للخبر: {src}')
    try:
        if not valid_image(path):
            raise SystemExit(f'أبعاد/صيغة الصورة غير صالحة: {src}')
    except SystemExit:
        raise
    except Exception as exc:
        raise SystemExit(f'فشل التحقق من الصورة الخام: {src} — {exc}')
    item['image']=str(src if str(src).startswith('./') else './'+str(src))
    item['original_image']=item['image']
NEWS.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
print('تم تثبيت الصور الخام للأخبار:',len(items))
