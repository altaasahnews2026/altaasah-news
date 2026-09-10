import hashlib, html, json, re, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from io import BytesIO
from pathlib import Path
from PIL import Image

NEWS_DIR = Path('assets/news'); NEWS_DIR.mkdir(parents=True, exist_ok=True)
HEADERS = {'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/128 Safari/537.36','Accept-Language':'ar-IQ,ar;q=0.9,en;q=0.7'}
GENERIC_WORDS = ('logo','icon','favicon','avatar','placeholder','default','sprite','banner','advert','ads','loading','no-image','no_image','profile')
RSS_FEEDS = ['https://www.alsumaria.tv/Rss/iraq-latest-news/ar','https://www.alsumaria.tv/Rss/News','https://www.alsumaria.tv/Rss/News/ar/1/سياسة','https://www.alsumaria.tv/Rss/News/ar/48/محليات','https://www.alsumaria.tv/Rss/News/ar/16/أمن','https://www.alsumaria.tv/Rss/News/ar/5/رياضة','https://www.alsumaria.tv/Rss/News/ar/49/دوليات']
KIRKUK_PAGES = [('https://www.shafaq.com/ar/tags/كركوك','شفق نيوز'),('https://www.shafaq.com/ar/tags/محافظة-كركوك','شفق نيوز'),('https://964media.com/province/kirkuk/','شبكة 964'),('https://www.kirkuknow.com/ar','كركوك ناو')]
IRAQ_PAGES = [('https://www.shafaq.com/ar/tags/بغداد','شفق نيوز'),('https://964media.com/province/baghdad/','شبكة 964'),('https://www.alsumaria.tv/news/localnews','السومرية نيوز')]
IRAN_STUDENTS_PAGES = [('https://www.shafaq.com/ar/tags/الطلبة-العراقيين','شفق نيوز'),('https://www.shafaq.com/ar/tags/طلبة-عراقيين','شفق نيوز'),('https://www.alsumaria.tv/news/localnews','السومرية نيوز')]
KIRKUK_WORDS = ('كركوك','التون كوبري','التونكوبري','آلتون كوبري','الدبس','داقوق','الحويجة','ليلان','الرشاد','الرياض','الزاب','قره تبه','جيمن','باي حسن','بابا كركر')
REPORT_WORDS = ('تقرير','تقارير','تحقيق','تحقيقات','ملف','ملفات','قراءة','رصد','تغطية','استطلاع','تحليل','دراسة','خاص')
IRAQ_WORDS = ('العراق','بغداد','نينوى','الموصل','البصرة','النجف','كربلاء','الأنبار','الانبار','صلاح الدين','ديالى','واسط','ميسان','ذي قار','المثنى','بابل','القادسية','الديوانية','دهوك','أربيل','اربيل','السليمانية','حلبجة','كركوك','الحشد','البرلمان العراقي','الحكومة العراقية','القوات العراقية')
ARAB_INTL_WORDS = ('فلسطين','غزة','إسرائيل','اسرائيل','لبنان','سوريا','الأردن','الاردن','السعودية','الإمارات','الامارات','الكويت','قطر','البحرين','عُمان','عمان','اليمن','مصر','ليبيا','تونس','الجزائر','المغرب','السودان','إيران','ايران','تركيا','أمريكا','امريكا','أميركا','روسيا','أوكرانيا','الصين','أوروبا','بريطانيا','فرنسا','ألمانيا','دولي','دولية','مجلس الأمن','الأمم المتحدة')
IRAN_STUDENT_WORDS = ('الطلبة العراقيين','طلبة عراقيين','الطلبة العراقيون','طلبة عراقيون','الطلاب العراقيين','طلاب عراقيين','جامعة سمنان','سمنان','الاعتداء على الطلبة العراقيين')
MAX_AGE=timedelta(hours=30); NOW=datetime.now(timezone.utc)

def get(url,timeout=12):
 try:
  req=urllib.request.Request(url,headers=HEADERS)
  with urllib.request.urlopen(req,timeout=timeout) as r:return r.read(),r.headers.get_content_type(),r.geturl()
 except:return b'','',url

def clean_url(v,base=''):return urllib.parse.urljoin(base,html.unescape(str(v or '').strip())) if v else ''
def host(url):
 try:return urllib.parse.urlparse(url).netloc.lower().split(':')[0]
 except:return ''
def norm_title(v):return re.sub(r'\s+',' ',str(v or '')).strip()
def is_kirkuk(t):return any(k in norm_title(t) for k in KIRKUK_WORDS)
def is_report(t):return any(k in norm_title(t) for k in REPORT_WORDS)
def is_iran_students(t):return any(k in norm_title(t) for k in IRAN_STUDENT_WORDS)

def parse_date(v):
 if not v:return None
 v=html.unescape(str(v)).strip()
 try:return parsedate_to_datetime(v).astimezone(timezone.utc)
 except:pass
 try:
  d=datetime.fromisoformat(v.replace('Z','+00:00')); return d.replace(tzinfo=timezone.utc) if d.tzinfo is None else d.astimezone(timezone.utc)
 except:return None

def extract_published(text,fallback=''):
 vals=[]
 for key in ('article:published_time','og:published_time','datePublished','pubdate','publishdate','date'):
  for p in (rf'<meta[^>]+(?:property|name)=["\']{re.escape(key)}["\'][^>]+content=["\']([^"\']+)',rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name)=["\']{re.escape(key)}["\']'):
   m=re.search(p,text,re.I)
   if m:vals.append(m.group(1))
 for m in re.finditer(r'<time[^>]+(?:datetime|data-datetime)=["\']([^"\']+)',text,re.I):vals.append(m.group(1))
 for v in vals:
  d=parse_date(v)
  if d:return d
 return parse_date(fallback)

def fresh(d):return bool(d and NOW-timedelta(minutes=5)<=d<=NOW+timedelta(minutes=10) or d and NOW-d<=MAX_AGE)

def meta(text,names):
 for name in names:
  for p in (rf'<meta[^>]+(?:property|name)=["\']{re.escape(name)}["\'][^>]+content=["\']([^"\']+)',rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name)=["\']{re.escape(name)}["\']'):
   m=re.search(p,text,re.I)
   if m:return html.unescape(m.group(1)).strip()
 return ''

def canonical(text,base):
 m=re.search(r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)',text,re.I); return clean_url(m.group(1),base) if m else base

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
  except:continue
 return b'',''

def store(raw,typ):
 if not raw or not typ.startswith('image/') or 'svg' in typ:return ''
 h=hashlib.sha256(raw).hexdigest(); ext={'image/jpeg':'.jpg','image/png':'.png','image/webp':'.webp','image/gif':'.gif'}.get(typ,'.jpg'); p=NEWS_DIR/(h[:24]+ext)
 if not p.exists():p.write_bytes(raw)
 return './assets/news/'+p.name

def category(t):
 if is_kirkuk(t):return 'كركوك'
 if any(k in t for k in ('رياضة','كرة','منتخب','مباراة','دوري','اتحاد الكرة','بطولة')):return 'رياضة'
 if any(k in t for k in ('دولار','ذهب','اقتصاد','مصرف','بنك','نفط','استثمار','أسعار','تجارة','بورصة','مالية')):return 'اقتصاد'
 if any(k in t for k in ('حكومة','وزير','رئيس الوزراء','برلمان','نائب','حزب','انتخابات','سياسة')):return 'سياسة'
 if any(k in t for k in ('هجوم','انفجار','شرطة','جيش','أمن','إرهاب','مسيرة','مخدرات','سلاح','اعتقال','مقتل','قتلى','حريق')):return 'أمن'
 if any(k in t for k in ('إيران','سوريا','فلسطين','غزة','لبنان','أمريكا','أميركا','تركيا','دولي','هرمز','اليمن')):return 'عربي ودولي'
 return 'محليات'

def region(t):
 if is_kirkuk(t):return 'كركوك'
 if is_iran_students(t):return 'عربي ودولي'
 if any(k in t for k in IRAQ_WORDS):return 'العراق'
 if any(k in t for k in ARAB_INTL_WORDS):return 'عربي ودولي'
 return 'العراق'
def is_breaking(t):return bool(re.search(r'(^|\s)(عاجل|طارئ|تحديث عاجل|تحذير عاجل)(\s|$)|انفجار|هجوم|هجوم جديد|اعتداء|اشتباك|قتلى|ضحايا',t,re.I))

def parse_feed(url,source='السومرية نيوز'):
 raw,_,final=get(url)
 if not raw:return []
 try:root=ET.fromstring(raw)
 except:return []
 out=[]
 for item in root.findall('.//item'):
  title=norm_title(item.findtext('title') or ''); link=clean_url(item.findtext('link'),final); pub=item.findtext('pubDate') or item.findtext('{http://purl.org/dc/elements/1.1/}date') or ''; d=parse_date(pub)
  if title and link and fresh(d):out.append((title,link,d.isoformat(),source))
 return out

def page_rows(url,source):
 raw,_,final=get(url,12)
 if not raw:return []
 text=raw.decode('utf-8','ignore'); rows=[];seen=set()
 for m in re.finditer(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',text,re.I|re.S):
  href=clean_url(m.group(1),final); title=html.unescape(norm_title(re.sub('<[^>]+>',' ',m.group(2))))
  if not title or len(title)<10 or href in seen:continue
  h=host(href)
  if (h.endswith('shafaq.com') and '/ar/' in href) or h.endswith('964media.com') or h.endswith('kirkuknow.com') or h.endswith('alsumaria.tv'):
   if any(x in href for x in ('/tags/','/province/','/category/')):continue
   seen.add(href);rows.append((title,href,'',source))
 return rows[:120]

def collect_pages(pages, predicate=None):
 out=[];seen=set()
 with ThreadPoolExecutor(max_workers=len(pages)) as ex:
  fs=[ex.submit(page_rows,u,s) for u,s in pages]
  for f in as_completed(fs):
   try:got=f.result()
   except:got=[]
   for row in got:
    if (predicate is None or predicate(row[0])) and row[1] not in seen:
     seen.add(row[1]);out.append(row)
 return out

rows=[]
for row in collect_pages(KIRKUK_PAGES, is_kirkuk):rows.append(row)
for row in collect_pages(IRAQ_PAGES, lambda t: any(k in t for k in IRAQ_WORDS) or 'بغداد' in t):rows.append(row)
for row in collect_pages(IRAN_STUDENTS_PAGES, is_iran_students):rows.append(row)
seen=set();rows=[r for r in rows if not (r[1] in seen or seen.add(r[1]))]
with ThreadPoolExecutor(max_workers=len(RSS_FEEDS)) as ex:
 for f in as_completed([ex.submit(parse_feed,u) for u in RSS_FEEDS]):
  try:got=f.result()
  except:got=[]
  for row in got:
   if row[1] not in seen:seen.add(row[1]);rows.append(row)

def enrich(row):
 title,url,pub,source=row; raw,_,final=get(url,12)
 if not raw:return None
 text=raw.decode('utf-8','ignore'); d=extract_published(text,pub)
 if not fresh(d):return None
 image_raw,image_typ=extract_image(text,final)
 if not image_raw:return None
 final=canonical(text,final); title=norm_title(meta(text,['og:title','twitter:title']) or title); img=store(image_raw,image_typ)
 return {'title':title,'url':final,'category':category(title),'region':region(title),'published':d.isoformat(),'image':img,'original_image':img,'source_url':final,'source_name':source,'breaking':is_breaking(title),'kirkuk':is_kirkuk(title),'report':is_report(title)}

items=[];seen_titles=set();seen_urls=set()
with ThreadPoolExecutor(max_workers=18) as ex:
 for f in as_completed([ex.submit(enrich,row) for row in rows]):
  try:item=f.result()
  except:item=None
  if not item or not item.get('image'):continue
  if item['url'] in seen_urls or item['title'] in seen_titles:continue
  seen_urls.add(item['url']);seen_titles.add(item['title']);items.append(item)
# الأحدث أولاً، مع إبقاء أخبار كركوك داخل الموقع لكن ليس في مقدمة الواجهة
rank={'العراق':0,'عربي ودولي':1,'كركوك':2}; items.sort(key=lambda x:x.get('published',''),reverse=True); items.sort(key=lambda x:rank.get(x.get('region'),1)); items=items[:48]
if len(items)<20:raise SystemExit(f'الأخبار اليومية الحديثة غير كافية: {len(items)}')
Path('news.json').write_text(json.dumps({'updated_at':datetime.now(timezone.utc).isoformat(),'items':items},ensure_ascii=False,indent=2),encoding='utf-8')
print('تم تحديث الأخبار الحديثة فقط:',len(items),'— كركوك:',sum(x.get('region')=='كركوك' for x in items),'— طلبة إيران:',sum(is_iran_students(x.get('title','')) for x in items),'— بغداد:',sum('بغداد' in x.get('title','') for x in items))
