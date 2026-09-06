import hashlib,html,json,os,re,urllib.parse,urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
D='assets/news';os.makedirs(D,exist_ok=True);H={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
def get(u,t=5):
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
def tokens(s):return set(re.findall(r'[\u0600-\u06ffA-Za-z]{3,}',s.lower()))
def valid(raw,typ):return len(raw)>=1500 and typ.startswith('image/') and 'svg' not in typ and (raw.startswith(b'\xff\xd8\xff') or raw.startswith(b'\x89PNG') or raw[:4]==b'RIFF' or raw[:6] in (b'GIF87a',b'GIF89a'))
def store(raw,typ,used):
 if not valid(raw,typ):return ''
 h=hashlib.sha256(raw).hexdigest()
 if h in used:return ''
 ext={'image/jpeg':'.jpg','image/png':'.png','image/webp':'.webp','image/gif':'.gif'}.get(typ,'.jpg');open(os.path.join(D,h[:24]+ext),'wb').write(raw);used.add(h);return './assets/news/'+h[:24]+ext
def grab(u):
 try:return u,*get(u,4)
 except:return u,b'', ''
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
with ThreadPoolExecutor(max_workers=12) as ex:
 for (idx,u),(uu,rawi,typ) in zip(jobs,[f.result() for f in [ex.submit(grab,u) for _,u in jobs]]):
  p=store(rawi,typ,used)
  if p and idx not in imgs:imgs[idx]=p
# صورة بديلة سريعة: ستة استعلامات صور دفعة واحدة، ثم تنزيل النتائج بالتوازي
if len(imgs)<8:
 qs={'محلي':'العراق بغداد أخبار','سياسة':'العراق حكومة برلمان سياسة','اقتصاد':'العراق اقتصاد نفط بغداد','أمن':'العراق أمن شرطة جيش','رياضة':'العراق رياضة منتخب كرة','عربي ودولي':'العراق فلسطين إيران أخبار'}
 def search_images(q):
  u='https://www.bing.com/images/search?'+urllib.parse.urlencode({'q':q,'form':'HDRSC2','first':'1'})
  r,_=get(u,6);s=r.decode('utf-8','ignore');out=[]
  for m in re.findall(r'"murl":"(https?[^"\\]+)"',s):
   m=clean(m.replace('\\/','/'))
   if m and m not in out:out.append(m)
  return out[:15]
 pool=[]
 with ThreadPoolExecutor(max_workers=6) as ex:
  for c,urls in zip(qs,ex.map(search_images,qs.values())):pool.append((c,urls))
 def dl(u):return grab(u)
 for i,(_,t,_,_) in enumerate(rows):
  if i in imgs:continue
  c=cat(t); urls=dict(pool).get(c,[]) or dict(pool).get('محلي',[])
  # نفضل الصورة التي تنتمي لفئة الخبر، ونأخذ أول صورة فريدة صالحة
  for u in urls:
   _,rr,typ=dl(u);p=store(rr,typ,used)
   if p:imgs[i]=p;break
  if len(imgs)>=24:break
items=[]
for i,(it,t,link,src) in enumerate(rows):
 if i not in imgs:continue
 items.append({'title':t,'url':link,'category':cat(t),'published':it.findtext('pubDate') or '','image':imgs[i],'source_url':clean(src.attrib.get('url') if src is not None else '')})
 if len(items)>=24:break
with open('news.json','w',encoding='utf-8') as f:json.dump({'updated_at':datetime.now(timezone.utc).isoformat(),'items':items},f,ensure_ascii=False,indent=2)
print('تم تحديث',len(items),'خبراً بنظام صور سريع')
if len(items)<8:raise SystemExit('تعذر توفير 8 صور حقيقية على الأقل')