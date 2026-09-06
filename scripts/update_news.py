import hashlib,html,json,os,re,urllib.parse,urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,timezone
D='assets/news';os.makedirs(D,exist_ok=True);H={'User-Agent':'Mozilla/5.0'}
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
def valid_image(raw,typ):return len(raw)>=1500 and typ.startswith('image/') and 'svg' not in typ and (raw.startswith(b'\xff\xd8\xff') or raw.startswith(b'\x89PNG') or raw[:4]==b'RIFF' or raw[:6] in (b'GIF87a',b'GIF89a'))
def save_raw(raw,typ,used):
 if not valid_image(raw,typ):return ''
 h=hashlib.sha256(raw).hexdigest()
 if h in used:return ''
 ext={ 'image/jpeg':'.jpg','image/png':'.png','image/webp':'.webp','image/gif':'.gif'}.get(typ,'.jpg');open(os.path.join(D,h[:24]+ext),'wb').write(raw);used.add(h);return './assets/news/'+h[:24]+ext
def download(u):return (u,*get(u,4))
q=urllib.parse.urlencode({'q':'العراق when:1d','hl':'ar','gl':'IQ','ceid':'IQ:ar'})
raw,_=get('https://news.google.com/rss/search?'+q,7)
if not raw:raise SystemExit('تعذر الوصول إلى موجز الأخبار')
root=ET.fromstring(raw);rows=[];seen=set()
for it in root.findall('./channel/item'):
 t=re.sub(r'\s+',' ',it.findtext('title') or '').strip();link=clean(it.findtext('link'));src=it.find('source');sn=(src.text or '').strip() if src is not None else ''
 if sn:t=re.sub(r'\s*[-–—|]\s*'+re.escape(sn)+r'\s*$','',t,flags=re.I)
 if t and link and t not in seen:seen.add(t);rows.append((it,t,link,src))
 if len(rows)>=40:break
# نجمع كل روابط الصور من RSS ثم ننزلها بالتوازي
jobs=[]
for i,(it,t,link,src) in enumerate(rows):
 us=[]
 for m in it.findall('{http://search.yahoo.com/mrss/}content')+it.findall('{http://search.yahoo.com/mrss/}thumbnail'):us.append(clean(m.attrib.get('url')))
 e=it.find('enclosure')
 if e is not None:us.append(clean(e.attrib.get('url')))
 for u in dict.fromkeys(x for x in us if x):jobs.append((i,u))
used=set();imgs={}
with ThreadPoolExecutor(max_workers=10) as ex:
 futs=[ex.submit(download,u) for _,u in jobs]
 for (idx,u),f in zip(jobs,futs):
  try:
   _,r,typ=f.result();p=save_raw(r,typ,used)
   if p and idx not in imgs:imgs[idx]=p
  except:pass
# إذا لم توفر RSS صوراً، استخدم GDELT مرة واحدة فقط ثم طابق الصور مع العناوين
if len(imgs)<8:
 gdq=urllib.parse.urlencode({'query':'iraq OR Iraq OR Baghdad','mode':'artlist','maxrecords':'100','format':'json','sort':'datedesc','timespan':'1d'})
 gr,_=get('https://api.gdeltproject.org/api/v2/doc/doc?'+gdq,6)
 try:cands=json.loads(gr).get('articles',[]) if gr else []
 except:cands=[]
 pool=[]
 for c in cands:
  u=clean(c.get('socialimage'));ct=c.get('title','');
  if u:pool.append((tokens(ct),u))
 used_titles=set();missing=[i for i in range(len(rows)) if i not in imgs]
 for i in missing:
  rt=tokens(rows[i][1]);best=None;score=-1
  for n,(ct,u) in enumerate(pool):
   if n in used_titles:continue
   sc=len(rt&ct)
   if sc>score:score=sc;best=(n,u)
  if best and score>0:used_titles.add(best[0]);pool_url=best[1]
  else:continue
  try:
   _,r,typ=get(pool_url,4);p=save_raw(r,typ,used)
   if p:imgs[i]=p
  except:pass
items=[]
for i,(it,t,link,src) in enumerate(rows):
 if i not in imgs:continue
 items.append({'title':t,'url':link,'category':cat(t),'published':it.findtext('pubDate') or '','image':imgs[i],'source_url':clean(src.attrib.get('url') if src is not None else '')})
 if len(items)>=24:break
with open('news.json','w',encoding='utf-8') as f:json.dump({'updated_at':datetime.now(timezone.utc).isoformat(),'items':items},f,ensure_ascii=False,indent=2)
print('تم تحديث',len(items),'خبراً بصور حقيقية وبنظام سريع ومتوازي')
if len(items)<8:raise SystemExit('عدد الأخبار المصورة غير كاف: '+str(len(items)))