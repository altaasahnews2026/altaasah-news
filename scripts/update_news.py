import hashlib, html, json, re, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from PIL import Image

NEWS_DIR = Path('assets/news')
NEWS_DIR.mkdir(parents=True, exist_ok=True)
UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/128 Safari/537.36'
HEADERS = {'User-Agent': UA, 'Accept-Language': 'ar-IQ,ar;q=0.9,en;q=0.7'}
GENERIC_WORDS = ('logo','icon','favicon','avatar','placeholder','default','sprite','banner','advert','ads','loading','no-image','no_image','profile')
BLOCKED_HOSTS = {'news.google.com','google.com','www.google.com','bing.com','www.bing.com','commons.wikimedia.org'}
TRUSTED_HOST_HINTS = ('alsumaria.tv','baghdadtoday.news','ipa.com.iq','shafaq.com','alrray.org','alhadath.net','aljazeera.net','aawsat.com','iraqinews.com','ina.iq')
QUERIES = [
    'العراق when:1d', 'العراق عاجل when:1d', 'العراق بغداد when:1d',
    'العراق سياسة when:1d', 'العراق أمن when:1d', 'العراق اقتصاد when:1d',
    'العراق رياضة when:1d', 'العراق محافظات when:1d', 'العراق حكومة when:1d',
    'العراق برلمان when:1d', 'العراق نفط when:1d', 'العراق كردستان when:1d',
    'العراق طلبة when:1d', 'العراق طقس when:1d', 'العراق صحة when:1d',
    'site:alsumaria.tv العراق when:1d', 'site:baghdadtoday.news العراق when:1d',
    'site:shafaq.com العراق when:1d', 'site:ipa.com.iq العراق when:1d',
    'site:alrray.org العراق when:1d'
]

def clean_url(v):
    v = html.unescape(str(v or '').strip())
    if v.startswith('//'):
        return 'https:' + v[2:]
    if v.startswith(('http://','https://')):
        return v
    return ''

def norm_title(v):
    v = re.sub(r'\s+', ' ', str(v or '')).strip()
    v = re.sub(r'\s*[-–—|]\s*[^|]+$', '', v)
    return v.strip()

def host(url):
    try:
        return urllib.parse.urlparse(url).netloc.lower().split(':')[0]
    except Exception:
        return ''

def is_google_or_search(url):
    h = host(url)
    return h in BLOCKED_HOSTS or h.endswith('.google.com') or h.endswith('.bing.com')

def get(url, timeout=10):
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read(), r.headers.get_content_type(), r.geturl()
    except Exception:
        return b'', '', url

def resolve_article(url):
    raw, typ, final = get(url, 12)
    if not raw or is_google_or_search(final):
        return '', b'', '', final
    return final, raw, typ, final

def meta(html_text, names):
    for name in names:
        p1 = rf'<meta[^>]+(?:property|name)=["\']{re.escape(name)}["\'][^>]+content=["\']([^"\']+)'
        p2 = rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name)=["\']{re.escape(name)}["\']'
        for p in (p1,p2):
            m = re.search(p, html_text, re.I)
            if m:
                return html.unescape(m.group(1)).strip()
    return ''

def canonical(html_text, base):
    m = re.search(r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)', html_text, re.I)
    return clean_url(urllib.parse.urljoin(base, html.unescape(m.group(1)))) if m else base

def extract_image(html_text, base):
    candidates = []
    for key in ('og:image','og:image:url','twitter:image','twitter:image:src','image_src'):
        u = meta(html_text, [key])
        if u:
            candidates.append(clean_url(urllib.parse.urljoin(base, u)))
    for m in re.finditer(r'<img[^>]+(?:src|data-src|data-original)=["\']([^"\']+)', html_text, re.I):
        u = clean_url(urllib.parse.urljoin(base, html.unescape(m.group(1))))
        if u:
            candidates.append(u)
        if len(candidates) >= 12:
            break
    seen = set()
    for u in candidates:
        if not u or u in seen or u.lower().split('?')[0].endswith('.svg'):
            continue
        seen.add(u)
        path = urllib.parse.urlparse(u).path.lower()
        if any(w in path for w in GENERIC_WORDS):
            continue
        raw, typ, _ = get(u, 8)
        if not raw or not typ.startswith('image/') or 'svg' in typ:
            continue
        try:
            with Image.open(BytesIO(raw)) as im:
                if im.width < 360 or im.height < 220 or im.width / max(1, im.height) > 4.5 or im.height / max(1, im.width) > 4.5:
                    continue
                im.verify()
            return u, raw, typ
        except Exception:
            continue
    return '', b'', ''

def rss(query):
    u = 'https://news.google.com/rss/search?' + urllib.parse.urlencode({'q':query,'hl':'ar','gl':'IQ','ceid':'IQ:ar'})
    raw, typ, _ = get(u, 12)
    if not raw:
        return []
    try:
        root = ET.fromstring(raw)
    except Exception:
        return []
    out = []
    for it in root.findall('./channel/item'):
        title = norm_title(it.findtext('title') or '')
        link = clean_url(it.findtext('link'))
        src = it.find('source')
        source_name = (src.text or '').strip() if src is not None else ''
        source_url = clean_url(src.attrib.get('url')) if src is not None else ''
        pub = it.findtext('pubDate') or ''
        if title and link:
            out.append((title, link, source_name, source_url, pub))
    return out

def category(title):
    t = title
    if any(k in t for k in ('رياضة','كرة','منتخب','مباراة','دوري','اتحاد الكرة','بطولة')): return 'رياضة'
    if any(k in t for k in ('دولار','ذهب','اقتصاد','مصرف','بنك','نفط','استثمار','أسعار','تجارة','بورصة','مالية')): return 'اقتصاد'
    if any(k in t for k in ('حكومة','وزير','رئيس الوزراء','برلمان','نائب','حكيم','بارزاني','حزب','انتخابات','سياسة')): return 'سياسة'
    if any(k in t for k in ('هجوم','انفجار','شرطة','جيش','أمن','إرهاب','مسيرة','مخدرات','سلاح','اعتقال','مقتل','قتلى','حريق')): return 'أمن'
    if any(k in t for k in ('إيران','سوريا','فلسطين','غزة','لبنان','أمريكا','أميركا','تركيا','دولي','هرمز','اليمن')): return 'عربي ودولي'
    if any(k in t for k in ('صحة','مستشفى','طلاب','طلبة','تربية','تعليم','طقس','أمطار','ولادة')): return 'محليات'
    return 'محليات'

def breaking(title):
    return bool(re.search(r'(^|\s)(عاجل|طارئ|تحديث عاجل|تحذير عاجل)(\s|$)|انفجار|هجوم|هزة أرضية|زلزال|حريق كبير|اشتباك|قتلى|ضحايا', title, re.I))

def store(raw, typ):
    if not raw or not typ.startswith('image/') or 'svg' in typ:
        return ''
    h = hashlib.sha256(raw).hexdigest()
    ext = {'image/jpeg':'.jpg','image/png':'.png','image/webp':'.webp','image/gif':'.gif'}.get(typ, '.jpg')
    p = NEWS_DIR / (h[:24] + ext)
    if not p.exists():
        p.write_bytes(raw)
    return './assets/news/' + p.name

rows = []
seen_titles = set(); seen_urls = set()
with ThreadPoolExecutor(max_workers=10) as ex:
    futures = [ex.submit(rss, q) for q in QUERIES]
    for f in as_completed(futures):
        try: got = f.result()
        except Exception: got = []
        for row in got:
            title, link, source_name, source_url, pub = row
            key = re.sub(r'[^\w\u0600-\u06ff]+','',title).lower()
            if key in seen_titles or link in seen_urls:
                continue
            seen_titles.add(key); seen_urls.add(link); rows.append(row)

rows = rows[:90]

def enrich(row):
    title, link, source_name, source_url, pub = row
    final, html_bytes, _, final_url = resolve_article(link)
    if not final or not html_bytes:
        return None
    h = host(final)
    if not h or is_google_or_search(final):
        return None
    text = html_bytes.decode('utf-8','ignore')
    image_url, raw, typ = extract_image(text, final)
    if not raw:
        return None
    can = canonical(text, final)
    if can and not is_google_or_search(can):
        final = can
    title_meta = meta(text, ['og:title','twitter:title'])
    clean_title = norm_title(title_meta or title)
    trusted = any(x in h for x in TRUSTED_HOST_HINTS)
    iraqish = bool(re.search(r'العراق|بغداد|البصرة|نينوى|كركوك|أربيل|السليمانية|ديالى|الأنبار|ذي قار|النجف|كربلاء|ميسان|واسط|بابل|صلاح الدين|دهوك|المثنى|القادسية', clean_title))
    if not trusted and not iraqish:
        return None
    return {
        'title': clean_title, 'url': final, 'category': category(clean_title),
        'published': pub, 'image': store(raw, typ), 'original_image': store(raw, typ),
        'source_url': source_url or final, 'source_name': source_name, 'breaking': breaking(clean_title)
    }

items = []
with ThreadPoolExecutor(max_workers=18) as ex:
    futures = [ex.submit(enrich, r) for r in rows]
    for f in as_completed(futures):
        try: item = f.result()
        except Exception: item = None
        if not item or not item.get('image'):
            continue
        if any(x['url'] == item['url'] or x['title'] == item['title'] for x in items):
            continue
        items.append(item)
        if len(items) >= 36:
            break

items.sort(key=lambda x: x.get('published',''), reverse=True)
if len(items) < 20:
    raise SystemExit(f'لم يتم العثور على 20 خبراً بصور أصلية من صفحات الناشرين. المتاح: {len(items)}')

now = datetime.now(timezone.utc).isoformat()
data = {'updated_at': now, 'items': items[:36]}
Path('news.json').write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
print('تم تحديث الأخبار:', len(data['items']), 'خبرًا بصور من صفحات الأخبار الأصلية فقط.')
