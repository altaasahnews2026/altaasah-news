import hashlib,html,json,os,re,urllib.parse,urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,timezone
D='assets/news';os.makedirs(D,exist_ok=True);H={'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/128 Safari/537.36'}
def get(u,t=4):
 try:
  r=urllib.request.urlopen(urllib.request.Request(u,headers=H),timeout=t);return r.read(),r.headers.get_content_type()
 except:return b'', ''
def clean(u):
 u=html.unescape(str(u or '').strip());return ('https:'+u[2:] if u.startswith('//') else u) if u.startswith(('http://','https://','//')) else ''
def cat(t):
 if any(x in t for x in ['رياضة','دوري','مباراة','منتخب','كرة','آسياد']):return 'رياضة'
 if any(x in t for x in ['اقتصاد','البنك المركزي','الأسعار','تجارة','استثمار','النفط','الذهب']):return 'اقتصاد'
 if any(x in t for x in ['حكومة','رئيس الوزراء','برلمان','وزير','سياسة']):return 'سياسة'
 if any(x in t for x in ['أمن','شرطة','جيش','هجوم','تفجير','حدود','إرهاب']):return 'أمن'
 if any(x in t for x in ['فلسطين','إيران','أمريكا','السعودية','سوريا','دولي']):return 'عربي ودولي'
 return 'محلي'
def valid(raw,typ):return len(raw)>=1200 and typ.startswith('image/') and 'svg' not in typ and (raw.startswith(b'\xff\xd8\xff') or raw.startswith(b'\x89PNG') or raw[:4]==b'RIFF' or raw[:6] in (b'GIF87a',b'GIF89a'))
def store(raw,typ,used):
 if not valid(raw,typ):return ''
 h=hashlib.sha256(raw).hexdigest()
 if h in used:return ''
 ext={'image/jpeg':'.jpg','image/png':'.png','image/webp':'.webp','image/gif':'.gif'}.get(typ,'.jpg');open(os.path.join(D,h[:24]+ext),'wb').write(raw);used.add(h);return './assets/news/'+h[:24]+ext
def grab(u):return u,*get(u,4)
def page_image(u):
 raw,_=get(u,4)
 if not raw:return ''
 s=raw.decode('utf-8','ignore')
 for pat in [r'<meta[^>]+(?:property|name)=["\'](?:og:image|twitter:image|image_src)["\'][^>]+content=["\']([^"\']+)',r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name)=["\'](?:og:image|twitter:image|image_src)["\']']:
  m=re.search(pat,s,re.I)
  if m:return clean(urllib.parse.urljoin(u,html.unescape(m.group(1))))
 return ''
def search_engine(q,engine):
 if engine=='bing':
  u='https://www.bing.com/images/search?'+urllib.parse.urlencode({'q':q,'form':'HDRSC2','first':'1'})
  pats=[r'"murl":"(https?[^"\\]+)"',r'"turl":"(https?[^"\\]+)"']
 elif engine=='google':
  u='https://www.google.com/search?'+urllib.parse.urlencode({'q':q,'tbm':'isch','hl':'ar'})
  pats=[r'"(https?://[^" ]+\.(?:jpg|jpeg|png|webp)(?:\?[^" ]*)?)"']
 else:
  u='https://duckduckgo.com/?'+urllib.parse.urlencode({'q':q})
  pats=[r'vqd=([0-9-]+)']
 r,_=get(u,5);s=r.decode('utf-8','ignore');out=[]
 for pat in pats:
  for m in re.findall(pat,s,re.I):
   x=clean(m.replace('\\/','/'))
   if x and x not in out:out.append(x)
 return out[:20]
raw,_=get('https://news.google.com/rss/search?'+urllib.parse.urlencode({'q':'العراق when:1d','hl':'ar','gl':'IQ','ceid':'IQ:ar'}),7)
if not raw:raise SystemExit('تعذر الوصول إلى الأخبار')
root=ET.fromstring(raw);rows=[];seen=set()
for it in root.findall('./channel/item'):
 t=re.sub(r'\s+',' ',it.findtext('title') or '').strip();link=clean(it.findtext('link'));src=it.find('source');sn=(src.text or '').strip() if src is not None else ''
 if sn:t=re.sub(r'\s*[-–—|]\s*'+re.escape(sn)+r'\s*$','',t,flags=re.I)
 if t and link and t not in seen:seen.add(t);rows.append((it,t,link,src))
 if len(rows)>=40:break
used=set();imgs={};jobs=[]
for i,(it,t,link,src) in enumerate(rows):
 for m in it.findall('{http://search.yahoo.com/mrss/}content')+it.findall('{http://search.yahoo.com/mrss/}thumbnail'):
  u=clean(m.attrib.get('url')); 
  if u:jobs.append((i,u))
 e=it.find('enclosure')
 if e is not None and clean(e.attrib.get('url')):jobs.append((i,clean(e.attrib.get('url'))))
with ThreadPoolExecutor(max_workers=16) as ex:
 fs=[ex.submit(grab,u) for _,u in jobs]
 for (idx,_),(uu,rr,typ) in zip(jobs,[f.result() for f in fs]):
  p=store(rr,typ,used)
  if p and idx not in imgs:imgs[idx]=p
# المصدر الحقيقي: Google News link غالباً يحول مباشرة إلى صفحة الخبر؛ نبحث عن og:image بالتوازي
if len(imgs)<8:
 with ThreadPoolExecutor(max_workers=16) as ex:
  fs={ex.submit(page_image,link):i for i,(_,_,link,_) in enumerate(rows) if i not in imgs}
  for f in as_completed(fs):
   i=fs[f]
   try:u=f.result()
   except:u=''
   if not u:continue
   try:_,rr,typ=grab(u);p=store(rr,typ,used)
   except:p=''
   if p:imgs[i]=p
   if len(imgs)>=24:break
# بحث صور متعدد المحركات والفئات، والتحميل بالتوازي
if len(imgs)<8:
 qs={'محلي':'العراق بغداد أخبار','سياسة':'العراق حكومة برلمان سياسة','اقتصاد':'العراق اقتصاد نفط بغداد','أمن':'العراق أمن شرطة جيش','رياضة':'العراق رياضة منتخب كرة','عربي ودولي':'العراق فلسطين إيران أخبار'}
 searches=[]
 for engine in ['bing','google']:
  for c,q in qs.items():searches.append((engine,c,q))
 pool={}
 with ThreadPoolExecutor(max_workers=12) as ex:
  fs={ex.submit(search_engine,q,e):(e,c) for e,c,q in searches}
  for f in as_completed(fs):
   e,c=fs[f]
   try:pool[(e,c)]=f.result()
   except:pool[(e,c)]=[]
 candidates=[]
 for i,(_,t,_,_) in enumerate(rows):
  if i in imgs:continue
  c=cat(t)
  for e in ['bing','google']:
   for u in pool.get((e,c),[]):candidates.append((i,u))
 # تحميل كل المرشحين دفعة واحدة بدلاً من الانتظار لكل خبر
 with ThreadPoolExecutor(max_workers=20) as ex:
  fs={ex.submit(grab,u):i for i,u in candidates}
  for f in as_completed(fs):
   i=fs[f]
   if i in imgs:continue
   try:u,rr,typ=f.result();p=store(rr,typ,used)
   except:p=''
   if p:imgs[i]=p
   if len(imgs)>=24:break
items=[]
for i,(it,t,link,src) in enumerate(rows):
 if i not in imgs:continue
 items.append({'title':t,'url':link,'category':cat(t),'published':it.findtext('pubDate') or '','image':imgs[i],'source_url':clean(src.attrib.get('url') if src is not None else '')})
 if len(items)>=24:break
with open('news.json','w',encoding='utf-8') as f:json.dump({'updated_at':datetime.now(timezone.utc).isoformat(),'items':items},f,ensure_ascii=False,indent=2)
print('تم تحديث',len(items),'خبراً بنظام صور متعدد المصادر وسريع')
if len(items)<8:raise SystemExit('تعذر توفير 8 صور حقيقية على الأقل')
