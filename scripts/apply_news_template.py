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

def fallback_template():
    W = H = 1254
    im = Image.new('RGB', (W, H), (5, 20, 39))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 175), fill=(210, 25, 38))
    d.text((W // 2, 82), shape_ar('خبر'), font=font(92), fill='white', anchor='mm')
    for x in range(40, W, 55):
        for y in range(205, 930, 55):
            if ((x // 55) + (y // 55)) % 3 == 0:
                d.ellipse((x, y, x + 4, y + 4), fill=(28, 57, 82))
    d.rectangle((0, 950, W, H), fill=(3, 14, 29))
    d.rectangle((0, 950, 18, H), fill=(210, 25, 38))
    d.text((W // 2, 1030), shape_ar('التاسعة نيوز'), font=font(62), fill='white', anchor='mm')
    d.text((W // 2, 1100), shape_ar('نعلم لتعلم'), font=font(38), fill=(210, 25, 38), anchor='mm')
    return im

def extract_template():
    try:
        raw = TEMPLATE.read_text(encoding='utf-8')
        m = re.search(r'href="data:image/(?:jpeg|jpg|png);base64,([^"]+)"', raw)
        if not m:
            raise ValueError('embedded image missing')
        encoded = re.sub(r'\s+', '', m.group(1))
        if 'REDACTED_FOR_TOOL_PAYLOAD' in encoded or 'PLACEHOLDER' in encoded:
            raise ValueError('invalid embedded payload')
        encoded += '=' * (-len(encoded) % 4)
        blob = base64.b64decode(encoded, validate=False)
        with Image.open(io.BytesIO(blob)) as im:
            return im.convert('RGB')
    except Exception as e:
        print(f'تعذر قراءة القالب الأصلي، سيتم استخدام قالب آمن مؤقتاً: {e}')
        return fallback_template()

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
    lines, cur = [], ''
    for w in words:
        test = (cur + ' ' + w).strip()
        if draw.textbbox((0, 0), shape_ar(test), font=fnt)[2] <= max_width:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines[:3]

def fit_cover(photo, size):
    tw, th = size
    photo = photo.convert('RGB')
    scale = max(tw / photo.width, th / photo.height)
    nw = max(tw, int(round(photo.width * scale)))
    nh = max(th, int(round(photo.height * scale)))
    photo = photo.resize((nw, nh), Image.Resampling.LANCZOS)
    left = max(0, (nw - tw) // 2)
    top = max(0, (nh - th) // 2)
    return photo.crop((left, top, left + tw, top + th))

def build(template, photo, title):
    W, H = template.size
    y0, y1 = 175, min(950, H)
    box_h = max(1, y1 - y0)
    canvas = template.convert('RGB').copy()

    # Always make the source photo exactly the same size as the target region.
    photo = fit_cover(photo, (W, box_h))
    photo = photo.filter(ImageFilter.UnsharpMask(radius=1, percent=80, threshold=3))
    canvas.paste(photo, (0, y0))

    # Overlay must be the full canvas size for alpha_composite; the old code
    # incorrectly used a W x box_h overlay against a W x H canvas.
    overlay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    panel_y = max(y0 + 10, y1 - 205)
    od.rounded_rectangle((45, panel_y, W - 45, min(H - 25, y1 - 25)), radius=14,
                         fill=(3, 20, 42, 222), outline=(210, 25, 38, 235), width=4)
    canvas = Image.alpha_composite(canvas.convert('RGBA'), overlay)

    d = ImageDraw.Draw(canvas)
    title = str(title or 'خبر من التاسعة نيوز')
    f = font(46 if len(title) < 70 else 40)
    lines = wrap_text(d, title, f, W - 160)
    line_h = 58
    panel_bottom = min(H - 25, y1 - 25)
    panel_top = panel_y
    total_h = len(lines) * line_h
    y = panel_top + max(12, (panel_bottom - panel_top - total_h) // 2)
    for line in lines:
        t = shape_ar(line)
        bb = d.textbbox((0, 0), t, font=f)
        x = (W - (bb[2] - bb[0])) // 2
        d.text((x + 2, y + 2), t, font=f, fill=(0, 0, 0, 170))
        d.text((x, y), t, font=f, fill='white')
        y += line_h
    return canvas.convert('RGB')

data = json.loads(NEWS.read_text(encoding='utf-8'))
template = extract_template()
count = 0
items = data.get('items', [])

for item in items:
    src = item.get('original_image') or item.get('image')
    sp = source_path(src)
    if not sp or sp.suffix.lower() == '.svg':
        continue
    try:
        with Image.open(sp) as photo:
            photo.load()
            key = hashlib.sha1((str(item.get('url', '')) + '|' + str(item.get('title', '')) + '|' + str(sp)).encode()).hexdigest()[:16]
            out = OUT / f'news-template-{key}.jpg'
            build(template, photo, item.get('title', 'خبر من التاسعة نيوز')).save(
                out, quality=88, optimize=True, progressive=True
            )
        # Validate the generated file before exposing it to the website.
        with Image.open(out) as check:
            check.verify()
        item['original_image'] = str(src)
        item['image'] = './assets/news/' + out.name
        count += 1
    except Exception as e:
        print(f'تعذر تجهيز صورة: {sp}: {e}')

if items and count != len(items):
    raise SystemExit(f'فشل تركيب القالب: تم تجهيز {count} من {len(items)} خبراً فقط')

NEWS.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'تم تطبيق قالب التاسعة نيوز على {count} خبراً')
