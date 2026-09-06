import hashlib, html, json, os, re, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
NEWS_IMAGE_DIR='assets/news'; os.makedirs(NEWS_IMAGE_DIR, exist_ok=True)
HEADERS={'User-Agent':'Mozilla/5.0','Accept':'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8'}
def fetch(url,timeout=8):
 req=urllib.request.Request(url,headers=HEADERS)
 with urllib.request.urlopen(req,timeout=timeout) as r:return r.read(),r.headers.get_content_type(),r.geturl()
def clean(u):
 u=html.unescape(str(u or '').strip()); return ('https:'+u if u.startswith('//') else u) if u.startswith(('http','//')) else ''
def title(t,src=''):
 t=re.sub(r'\s+',' ',str(t or '')).strip(); src=re.sub(r'\s+',' ',str(src or '')).strip()
 return re.sub(r'\s*[-–—|]\s*'+re.escape(src)+r'\s*$','',t,flags=re.I).strip() if src else t
def category(t):
 if any(k in t for k in ['رياضة','دوري','مباراة','منتخب','كرة']):return 'رياضة'
 if any(k in t for k in ['اقتصاد','البنك المركزي','الأسعار','تجارة','استثمار','النفط','الذهب']):return 'اقتصاد'
 if any(k in t for k in ['حكومة','رئيس الوزراء','برلمان','وزير','سياسة']):return 'سياسة'
 if any(k in t for k in ['أمن','شرطة','جيش','هجوم','تفجير','حدود']):return 'أمن'
 if any(k in t for k in ['فلسطين','إيران','أمريكا','السعودية','سوريا','دولي']):return 'عربي ودولي'
 return 'محلي'
def save(url,used):
 try:
  raw,typ,_=fetch(url,7)
  if len(raw)<3000 or not typ.startswith('image/') or 'svg' in typ:return ''
  if not(raw[:3]==b'\xff\xd8\xff' or raw.startswith(b'\x89PNG') or raw[:4]==b'RIFF' or raw[:6] in (b'GIF87a',b'GIF89a')):return ''
  h=hashlib.sha256(raw).hexdigest()
  if h in used:return ''
  ext={ 'image/jpeg':'.jpg','image/png':'.png','image/webp':'.webp','image/gif':'.gif'}.get(typ,'.jpg')
  name=h[:24]+ext; open(os.path.join(NEWS_IMAGE_DIR,name),'wb').write(raw); used.add(h); return './assets/news/'+name
 except Exception:return ''
def candidates(item):
 out=[]
 for m in item.findall('{http://search.yahoo.com/mrss/}content')+item.findall('{http://search.yahoo.com/mrss/}thumbnail'):
  u=clean(m.attrib.get('url')); out.append(u) if u else None
 e=item.find('enclosure'); u=clean(e.attrib.get('url')) if e is not None else ''
 if u:out.append(u)
 d=item.findtext('description') or ''
 out += [clean(x) for x in re.findall(r'<img[^>]+(?:src|data-src|data-original)=["\']([^"\']+)',d,re.I)]
 return list(dict.fromkeys(filter(None,out)))
def google_fast(t,used):
 try:
  q=urllib.parse.quote(t+' العراق')
  raw,_,_=fetch('https://www.google.com/search?tbm=isch&hl=ar&gl=iq&q='+q,8); s=raw.decode('utf-8','ignore')[:500000]
  urls=re.findall(r'https?://[^"\\<> ]+?\.(?:jpg|jpeg|png|webp)(?:\?[^"\\<> ]*)?',s,re.I)
  for u in dict.fromkeys(urls):
   if any(x in u.lower() for x in ['google.com','gstatic.com','googleusercontent.com']):continue
   x=save(u,used)
   if x:return x
 except Exception:pass
 return ''
def gdelt_fast(t,used):
 try:
  q=urllib.parse.quote(t); raw,_,_=fetch('https://api.gdeltproject.org/api/v2/doc/doc?query='+q+'&mode=artlist&maxrecords=5&timespan=1d&sort=datedesc&format=json',7)
  for a in json.loads(raw.decode('utf-8','ignore')).get('articles',[]):
   x=save(clean(a.get('socialimage') or a.get('socialImage') or a.get('image')),used)
   if x:return x
 except Exception:pass
 return ''
params=urllib.parse.urlencode({'q':'العراق when:1d','hl':'ar','gl':'IQ','ceid':'IQ:ar'})
raw,_,_=fetch('https://news.google.com/rss/search?'+params,10); root=ET.fromstring(raw)
items=[]; seen=set(); used=set()
for it in root.findall('./channel/item'):
 src=it.find('source'); sn=src.text if src is not None else ''; t=title(it.findtext('title'),sn); link=clean(it.findtext('link'))
 if not t or not link or t in seen:continue
 seen.add(t); img=''
 for u in candidates(it):
  img=save(u,used)
  if img:break
 if not img:img=google_fast(t,used)
 if not img:img=gdelt_fast(t,used)
 if not img:continue
 items.append({'title':t,'url':link,'category':category(t),'published':it.findtext('pubDate') or '','image':img,'source_url':clean(src.attrib.get('url') if src is not None else '')})
 if len(items)>=30:break
with open('news.json','w',encoding='utf-8') as f:json.dump({'updated_at':datetime.now(timezone.utc).isoformat(),'items':items},f,ensure_ascii=False,indent=2)
print('تم تحديث',len(items),'خبراً بصور حقيقية')
if len(items)<10:raise SystemExit('صور حقيقية كافية غير متاحة: '+str(len(items)))
