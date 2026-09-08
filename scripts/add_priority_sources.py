import hashlib, html, json, re, urllib.parse, urllib.request
from datetime import datetime, timezone, timedelta
from io import BytesIO
from pathlib import Path
from PIL import Image

HEADERS={'User-Agent':'Mozilla/5.0','Accept-Language':'ar-IQ,ar;q=0.9,en;q=0.7'}
MAX_AGE=timedelta(hours=30); NOW=datetime.now(timezone.utc)
SOURCES=[
 ('https://www.rudawarabia.net/arabic','روداو'),
 ('https://www.alsharqiya.com/news','الشرقية'),
 ('https://news.imn.iq/','العراقية'),
 ('https://www.alsumaria.tv/iraq-latest-news','السومرية نيوز'),
 ('https://www.shafaq.com/ar','شفق نيوز'),
]
KIRKUK=('كركوك','التون كوبري','التونكوبري','الدبس','داقوق','الحويجة','ليلان','الرشاد','الرياض','الزاب','قره تبه','باي حسن','بابا كركر')
BAGHDAD=('بغداد','الرصافة','الكرخ','مدينة الصدر','الكاظمية','الأعظمية','الزعفرانية','العامرية')
STUDENTS=('طلبة عراقيين','طلاب عراقيين','الطلبة العراقيين','الطلاب العراقيين','طلبة العراق','طلاب العراق','سمنان','إيران','ايران','اعتداء على الطلبة','الاعتداء على الطلبة')

def get(u):
 try:
  r=urllib.request.urlopen(urllib.request.Request(u,headers=HEADERS),timeout=12); return r.read(),r.geturl()
 except:return b'',u

def clean(v,b):return urllib.parse.urljoin(b,html.unescape(str(v or '').strip()))
def parse_dt(v):
 if not v:return None
 from email.utils import parsedate_to_datetime
 try:return parsedate_to_datetime(v).astimezone(timezone.utc)
 except:pass
 try:
  d=datetime.fromisoformat(v.replace('Z','+00:00')); return d.replace(tzinfo=timezone.utc) if d.tzinfo is None else d.astimezone(timezone.utc)
 except:return None

def fresh(d):return bool(d and NOW-timedelta(minutes=5)<=d<=NOW+timedelta(minutes=10) or d and NOW-d<=MAX_AGE)
def meta(t,names):
 for n in names:
  m=re.search(r'<meta[^>]+(?:property|name)=["\']'+re.escape(n)+r'["\'][^>]+content=["\']([^"\']+)',t,re.I)
  if m:return html.unescape(m.group(1)).strip()
 return ''
def extract_date(t):
 for n in ('article:published_time','og:published_time','datePublished','pubdate','publishdate','date'):
  v=meta(t,[n]); d=parse_dt(v)
  if d:return d
 return None
def extract_image(t,b):
 for n in ('og:image','og:image:url','twitter:image','twitter:image:src'):
  u=clean(meta(t,[n]),b)
  if not u:continue
  raw,_=get(u)
  try:
   with Image.open(BytesIO(raw)) as im:
    if im.width>=360 and im.height>=220: return raw
  except:pass
 return b''
def store(raw):
 h=hashlib.sha256(raw).hexdigest(); p=Path('assets/news'); p.mkdir(parents=True,exist_ok=True); f=p/(h[:24]+'.jpg')
 if not f.exists():f.write_bytes(raw)
 return './assets/news/'+f.name
def region(t):
 if any(k in t for k in KIRKUK):return 'كركوك'
 if any(k in t for k in BAGHDAD):return 'بغداد'
 return 'العراق'
def relevant(t):return ('العراق' in t or any(k in t for k in KIRKUK+BAGHDAD+STUDENTS))
def rows(page,base):
 out=[]
 for m in re.finditer(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',page,re.I|re.S):
  u=clean(m.group(1),base); title=html.unescape(re.sub(r'\s+',' ',re.sub('<[^>]+>',' ',m.group(2)))).strip()
  if len(title)>=15 and u.startswith(('http://','https://')) and relevant(title):out.append((title,u))
 return out[:100]

try:data=json.loads(Path('news.json').read_text(encoding='utf-8'))
except:data={'updated_at':NOW.isoformat(),'items':[]}
items=data.get('items',[]); seen={x.get('url') for x in items}|{x.get('title') for x in items}
for page_url,source in SOURCES:
 raw,base=get(page_url)
 if not raw:continue
 text=raw.decode('utf-8','ignore')
 for title,url in rows(text,base):
  if url in seen or title in seen:continue
  ar,final=get(url)
  if not ar:continue
  t=ar.decode('utf-8','ignore'); d=extract_date(t)
  if not fresh(d):continue
  img=extract_image(t,final)
  if not img:continue
  canon=clean(meta(t,['og:url']),final) or final
  title2=meta(t,['og:title']) or title
  item={'title':title2,'url':canon,'category':'عربي ودولي' if any(k in title2 for k in STUDENTS) else region(title2),'region':region(title2),'published':d.isoformat(),'image':store(img),'original_image':store(img),'source_url':canon,'source_name':source,'breaking':False,'kirkuk':region(title2)=='كركوك','report':False}
  items.append(item); seen.add(canon); seen.add(title2)
rank={'كركوك':0,'بغداد':1,'العراق':2,'عربي ودولي':3}; items.sort(key=lambda x:(rank.get(x.get('region'),2),-datetime.fromisoformat(x['published'].replace('Z','+00:00')).timestamp() if x.get('published') else 0)); data={'updated_at':NOW.isoformat(),'items':items[:60]}; Path('news.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8'); print('priority sources merged',len(items))