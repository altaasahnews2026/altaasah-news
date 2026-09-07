import html, json, re, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

UA='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/128 Safari/537.36'
HEADERS={'User-Agent':UA,'Accept-Language':'ar-IQ,ar;q=0.9,en;q=0.7'}
FEEDS={
 'عراق':[
  'https://www.alsumaria.tv/Rss/iraq-latest-news/ar',
  'https://www.alsumaria.tv/Rss/News/ar/1/سياسة',
  'https://www.alsumaria.tv/Rss/News/ar/48/محليات',
  'https://www.alsumaria.tv/Rss/News/ar/16/أمن',
  'https://www.alsumaria.tv/Rss/News/ar/5/رياضة',
 ],
 'مشرق أوسط':[
  'https://aawsat.com/feed/arab-world',
  'https://aawsat.com/feed/gulf',
  'https://aawsat.com/feed/asia',
 ],
 'دولي':[
  'https://aawsat.com/feed/news',
  'https://aawsat.com/feed/europe',
  'https://aawsat.com/feed/america',
 ]
}

def get(url):
 try:
  req=urllib.request.Request(url,headers=HEADERS)
  with urllib.request.urlopen(req,timeout=12) as r:return r.read()
 except Exception:return b''

def parse(raw, category):
 if not raw:return []
 try:root=ET.fromstring(raw)
 except Exception:return []
 out=[]
 for it in root.findall('.//item'):
  title=html.unescape(re.sub(r'\s+',' ',(it.findtext('title') or '').strip()))
  link=(it.findtext('link') or '').strip()
  pub=(it.findtext('pubDate') or '').strip()
  if title and link and link.startswith(('http://','https://')):out.append({'title':title,'url':link,'category':category,'published':pub})
 return out

def breaking(title):
 t=re.sub(r'[\u200e\u200f\u202a-\u202e]','',str(title or ''))
 urgent_words=('عاجل','طارئ','تحذير عاجل','بشكل عاجل','تغطية مباشرة','تحديث عاجل')
 crisis_words=('قتلى','ضحايا','شهيد','شهداء','مقتل','إصابة خطيرة','انفجار','هجوم','غارة','زلزال','هزة','حريق كبير','اشتباك','إغلاق','تحذير','سقوط طائرة','اختطاف','قصف','استهداف','إطلاق نار','مسيّرة','مسيرة')
 return any(w in t for w in urgent_words) or any(w in t for w in crisis_words)

all_items=[]
for category, urls in FEEDS.items():
 for url in urls:
  all_items.extend(parse(get(url),category))

# Iraq site news are the first priority for the ticker.
try:
 data=json.loads(Path('news.json').read_text(encoding='utf-8'))
 for x in data.get('items',[]):
  if x.get('title') and x.get('url'):
   all_items.insert(0,{'title':x['title'],'url':x['url'],'category':'عراق','published':x.get('published','')})
except Exception:pass

seen=set(); items=[]
for x in all_items:
 key=re.sub(r'\W+','',x['title']).lower()
 if not key or key in seen:continue
 seen.add(key); x['breaking']=breaking(x['title']); items.append(x)

# Keep a balanced rolling stream: Iraq + Middle East + international.
result=[]
for cat,limit in [('عراق',28),('مشرق أوسط',24),('دولي',24)]:
 result.extend([x for x in items if x['category']==cat][:limit])

breaking_items=[x for x in result if x['breaking']]
latest=result[:72]
Path('ticker.json').write_text(json.dumps({'updated_at':datetime.now(timezone.utc).isoformat(),'latest':latest,'breaking':breaking_items[:30]},ensure_ascii=False,indent=2),encoding='utf-8')
print('ticker:',len(latest),'latest /',len(breaking_items[:30]),'breaking')
if len(latest)<20:raise SystemExit('تعذر بناء شريط أخبار كافٍ')
