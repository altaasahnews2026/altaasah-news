import hashlib, html, json, re, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from PIL import Image

NEWS_DIR = Path('assets/news')
NEWS_DIR.mkdir(parents=True, exist_ok=True)
HEADERS = {'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/128 Safari/537.36','Accept-Language':'ar-IQ,ar;q=0.9,en;q=0.7'}
GENERIC_WORDS = ('logo','icon','favicon','avatar','placeholder','default','sprite','banner','advert','ads','loading','no-image','no_image','profile')
RSS_FEEDS = [
    'https://www.alsumaria.tv/Rss/iraq-latest-news/ar',
    'https://www.alsumaria.tv/Rss/News',
    'https://www.alsumaria.tv/Rss/News/ar/1/سياسة',
    'https://www.alsumaria.tv/Rss/News/ar/48/محليات',
    'https://www.alsumaria.tv/Rss/News/ar/16/أمن',
    'https://www.alsumaria.tv/Rss/News/ar/5/رياضة',
    'https://www.alsumaria.tv/Rss/News/ar/49/دوليات',
]
KIRKUK_PAGES = [
    ('https://www.shafaq.com/ar/tags/كركوك','شفق نيوز'),
    ('https://964media.com/province/kirkuk/','شبكة 964'),
    ('https://964media.com/province/kirkuk/page/2/','شبكة 964'),
    ('https://www.kirkuknow.com/ar','كركوك ناو'),
]
KIRKUK_WORDS = ('كركوك','كركوكَ','كركوك،','كركوك.','التون كوبري','التونكوبري','آلتون كوبري','الدبس','داقوق','الحويجة','ليلان','الرشاد','الرياض','الزاب','قره تبه','جيمن','باي حسن','بابا كركر')
REPORT_WORDS = ('تقرير','تقارير','تحقيق','تحقيقات','ملف','ملفات','قراءة','رصد','تغطية','استطلاع','تحليل','دراسة','خاص')
IRAQ_WORDS = ('العراق','بغداد','نينوى','الموصل','البصرة','النجف','كربلاء','الأنبار','الانبار','صلاح الدين','ديالى','واسط','ميسان','ذي قار','المثنى','بابل','القادسية','الديوانية','دهوك','أربيل','اربيل','السليمانية','حلبجة','كركوك','الحشد','البرلمان العراقي','الحكومة العراقية','القوات العراقية')
ARAB_INTL_WORDS = ('فلسطين','غزة','إسرائيل','اسرائيل','لبنان','سوريا','الأردن','الاردن','السعودية','الإمارات','الامارات','الكويت','قطر','البحرين','عُمان','عمان','اليمن','مصر','ليبيا','تونس','الجزائر','المغرب','السودان','إيران','ايران','تركيا','أمريكا','امريكا','أميركا','روسيا','أوكرانيا','الصين','أوروبا','أوروبا','بريطانيا','فرنسا','ألمانيا','دولي','دولية','مجلس الأمن','الأمم المتحدة')

def get(url, timeout=12):
    try:
        req=urllib.request.Request(url,headers=HEADERS)
        with urllib.request.urlopen(req,timeout=timeout) as r:return r.read(),r.headers.get_content_type(),r.geturl()
    except Exception:return b'','',url

def clean_url(v,base=''):
    v=html.unescape(str(v or '').strip())
    return urllib.parse.urljoin(base,v) if v else ''

def host(url):
    try:return urllib.parse.urlparse(url).netloc.lower().split(':')[0]
    except:return ''

def norm_title(v):return re.sub(r'\s+',' ',str(v or '')).strip()

def is_kirkuk(title):
    t=norm_title(title)
    return any(k in t for k in KIRKUK_WORDS)

def is_report(title):
    t=norm_title(title)
    return any(k in t for k in REPORT_WORDS)

def region(title, kirkuk=False):
    t=norm_title(title)
    if kirkuk or is_kirkuk(t): return 'كركوك'
    if any(k in t for k in ARAB_INTL_WORDS) and not any(k in t for k in IRAQ_WORDS): return 'عربي ودولي'
    if any(k in t for k in IRAQ_WORDS): return 'العراق'
    # الأخبار العراقية العامة تأتي قبل العربي والدولي، ما لم يظهر بوضوح أنها خارج العراق.
    return 'العراق'

def region_rank(item):
    return {'كركوك':0,'العراق':1,'عربي ودولي':2}.get(item.get('region'),1)

def meta(text,names):
    for name in names:
        for p in (rf'<meta[^>]+(?:property|name)=["\']{re.escape(name)}["\'][^>]+content=["\']([^"\']+)',rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name)=["\']{re.escape(name)}["\']'):
            m=re.search(p,text,re.I)
            if m:return html.unescape(m.group(1)).strip()
    return ''

def canonical(text,base):
    m=re.search(r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)',text,re.I)
    return clean_url(m.group(1),base) if m else base

def extract_image(text,base):
    candidates=[]
    for key in ('og:image','og:image:url','twitter:image','twitter:image:src','image_src'):
        u=meta(text,[key])
        if u:candidates.append(clean_url(u,base))
    for m in re.finditer(r'<img[^>]+(?:src|data-src|data-original)=["\']([^"\']+)',text,re.I):
        candidates.append(clean_url(m.group(1),base))
        if len(candidates)>=15:break
    seen=set()
    for u in candidates:
        if not u or u in seen or u.lower().split('?')[0].endswith('.svg'):continue
        seen.add(u); path=urllib.parse.urlparse(u).path.lower()
        if any(w in path for w in GENERIC_WORDS):continue
        raw,typ,_=get(u,10)
        if not raw or not typ.startswith('image/') or 'svg' in typ:continue
        try:
            with Image.open(BytesIO(raw)) as im:
                if im.width<360 or im.height<220 or im.width/max(1,im.height)>4.5 or im.height/max(1,im.width)>4.5:continue
                im.verify()
            return raw,typ
        except Exception:continue
    return b'',''

def store(raw,typ):
    if not raw or not typ.startswith('image/') or 'svg' in typ:return ''
    h=hashlib.sha256(raw).hexdigest(); ext={'image/jpeg':'.jpg','image/png':'.png','image/webp':'.webp','image/gif':'.gif'}.get(typ,'.jpg')
    p=NEWS_DIR/(h[:24]+ext)
    if not p.exists():p.write_bytes(raw)
    return './assets/news/'+p.name

def category(title):
    t=title
    if is_kirkuk(t):return 'كركوك'
    if any(k in t for k in ('رياضة','كرة','منتخب','مباراة','دوري','اتحاد الكرة','بطولة')):return 'رياضة'
    if any(k in t for k in ('دولار','ذهب','اقتصاد','مصرف','بنك','نفط','استثمار','أسعار','تجارة','بورصة','مالية')):return 'اقتصاد'
    if any(k in t for k in ('حكومة','وزير','رئيس الوزراء','برلمان','نائب','حزب','انتخابات','سياسة')):return 'سياسة'
    if any(k in t for k in ('هجوم','انفجار','شرطة','جيش','أمن','إرهاب','مسيرة','مخدرات','سلاح','اعتقال','مقتل','قتلى','حريق')):return 'أمن'
    if any(k in t for k in ('إيران','سوريا','فلسطين','غزة','لبنان','أمريكا','أميركا','تركيا','دولي','هرمز','اليمن')):return 'عربي ودولي'
    if any(k in t for k in ('صحة','مستشفى','طلاب','طلبة','تربية','تعليم','طقس','أمطار','ولادة')):return 'محليات'
    return 'محليات'

def is_breaking(title):return bool(re.search(r'(^|\s)(عاجل|طارئ|تحديث عاجل|تحذير عاجل)(\s|$)|انفجار|هجوم|هزة أرضية|زلزال|حريق كبير|اشتباك|قتلى|ضحايا',title,re.I))

def parse_feed(url,source='السومرية نيوز'):
    raw,typ,final=get(url)
    if not raw:return []
    try:root=ET.fromstring(raw)
    except Exception:return []
    rows=[]
    for item in root.findall('.//item'):
        title=norm_title(item.findtext('title') or ''); link=clean_url(item.findtext('link'),final); pub=item.findtext('pubDate') or item.findtext('{http://purl.org/dc/elements/1.1/}date') or ''
        if title and link:rows.append((title,link,pub,source))
    return rows

def page_rows(url,source):
    raw,typ,final=get(url,12)
    if not raw:return []
    text=raw.decode('utf-8','ignore'); rows=[]; seen=set()
    for m in re.finditer(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',text,re.I|re.S):
        href=clean_url(m.group(1),final); title=norm_title(re.sub('<[^>]+>',' ',m.group(2)))
        title=html.unescape(title)
        if not title or len(title)<10 or href in seen:continue
        h=host(href)
        if (h.endswith('shafaq.com') and '/ar/' in href) or h.endswith('964media.com') or h.endswith('kirkuknow.com'):
            if any(x in href for x in ('/tags/','/province/','/category/','/ar$')):continue
            seen.add(href);rows.append((title,href,'',source))
    return rows[:100]

def kirkuk_rows():
    out=[];seen=set()
    with ThreadPoolExecutor(max_workers=len(KIRKUK_PAGES)) as ex:
        fs=[ex.submit(page_rows,u,s) for u,s in KIRKUK_PAGES]
        for f in as_completed(fs):
            try:got=f.result()
            except Exception:got=[]
            for row in got:
                if not is_kirkuk(row[0]):continue
                key=row[1]
                if key not in seen:seen.add(key);out.append(row)
    return out

def shafaq_rows():
    return page_rows('https://www.shafaq.com/ar','شفق نيوز')

rows=[];seen=set()
# أولاً: كل ما يتعلق بكركوك، بما في ذلك الأخبار والتقارير والتحقيقات والملفات والتحليلات.
for row in kirkuk_rows():
    key=(row[0],row[1])
    if key not in seen:seen.add(key);rows.append(row)
with ThreadPoolExecutor(max_workers=len(RSS_FEEDS)) as ex:
    fs=[ex.submit(parse_feed,u) for u in RSS_FEEDS]
    for f in as_completed(fs):
        try:got=f.result()
        except Exception:got=[]
        for row in got:
            key=(row[0],row[1])
            if key not in seen:seen.add(key);rows.append(row)
if len(rows)<40:
    for row in shafaq_rows():
        key=(row[0],row[1])
        if key not in seen:seen.add(key);rows.append(row)
rows=rows[:180]

def enrich(row):
    title,url,pub,source=row; raw,typ,final=get(url,12)
    if not raw or not final or host(final).endswith('google.com'):return None
    text=raw.decode('utf-8','ignore'); image_raw,image_typ=extract_image(text,final)
    if not image_raw:return None
    final=canonical(text,final); title=norm_title(meta(text,['og:title','twitter:title']) or title)
    k=is_kirkuk(title); r=region(title,k); img=store(image_raw,image_typ)
    return {'title':title,'url':final,'category':category(title),'region':r,'published':pub,'image':img,'original_image':img,'source_url':final,'source_name':source,'breaking':is_breaking(title),'kirkuk':k,'report':is_report(title)}

items=[];seen_titles=set();seen_urls=set()
with ThreadPoolExecutor(max_workers=18) as ex:
    fs=[ex.submit(enrich,row) for row in rows]
    for f in as_completed(fs):
        try:item=f.result()
        except Exception:item=None
        if not item or not item.get('image'):continue
        if item['url'] in seen_urls or item['title'] in seen_titles:continue
        seen_urls.add(item['url']);seen_titles.add(item['title']);items.append(item)
# ترتيب الصفحة الرئيسية ثابت: كركوك ثم العراق ثم عربي ودولي، والأحدث أولاً داخل كل مجموعة.
items.sort(key=lambda x: region_rank(x))
items.sort(key=lambda x: str(x.get('published') or ''), reverse=True)
# ثبات أولوية المجموعة بعد ترتيب التاريخ.
items.sort(key=lambda x: region_rank(x))
items=items[:48]
if len(items)<20:raise SystemExit(f'لم يتم العثور على 20 خبراً بصور أصلية من صفحات الناشرين. المتاح: {len(items)}')
Path('news.json').write_text(json.dumps({'updated_at':datetime.now(timezone.utc).isoformat(),'items':items},ensure_ascii=False,indent=2),encoding='utf-8')
k=sum(1 for x in items if x.get('kirkuk')); reports=sum(1 for x in items if x.get('kirkuk') and x.get('report'))
print('تم تحديث الأخبار:',len(items),'— كركوك:',k,'— تقارير كركوك:',reports,'— الترتيب: كركوك ثم العراق ثم عربي ودولي.')
