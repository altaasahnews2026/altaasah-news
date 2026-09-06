import hashlib,html,json,os,re,urllib.parse,urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime,timezone
D='assets/news';os.makedirs(D,exist_ok=True)
H={'User-Agent':'Mozilla/5.0'}
def get(u,t=5):
 try:
  r=urllib.request.urlopen(urllib.request.Request(u,headers=H),timeout=t);return r.read(),r.headers.get_content_type()
 except:return b'', ''
def clean(u):
 u=html.unescape(str(u or '').strip());return ('https:'+u[2:] if u.startswith('//') else u) if u.startswith(('http://','https://','//')) else ''
def save(u,used):
 raw,typ=get(u,4)
 if len(raw)<2000 or not typ.startswith('image/') or 'svg' in typ:return ''
 if not(raw.startswith(b'\xff\xd8\xff') or raw.startswith(b'\x89PNG') or raw[:4]==b'RIFF' or raw[:6] in (b'GIF87a',b'GIF89a')):return ''
 h=hashlib.sha256(raw).hexdigest()
 if h in used:return ''
 ext={'image/jpeg':'.jpg','image/png':'.png','image/webp':'.webp','image/gif':'.gif'}.get(typ,'.jpg')
 open(os.path.join(D,h[:24]+ext),'wb').write(raw);used.add(h);return './assets/news/'+h[:24]+ext
def cat(t):
 if any(x in t for x in ['رياضة','دوري','مباراة','منتخب','كرة']):return 'رياضة'
 if any(x in t for x in ['اقتصاد','البنك المركزي','الأسعار','تجارة','استثمار','النفط','الذهب']):return 'اقتصاد'
 if any(x in t for x in ['حكومة','رئيس الوزراء','برلمان','وزير','سياسة']):return 'سياسة'
 if any(x in t for x in ['أمن','شرطة','جيش','هجوم','تفجير','حدود']):return 'أمن'
 if any(x in t for x in ['فلسطين','إيران','أمريكا','السعودية','سوريا','دولي']):return 'عربي ودولي'
 return 'محلي'
q=urllib.parse.urlencode({'q':'العراق when:1d','hl':'ar','gl':'IQ','ceid':'IQ:ar'})
raw,_=get('https://news.google.com/rss/search?'+q,7)
if not raw:raise SystemExit('تعذر الوصول إلى موجز الأخبار')
root=ET.fromstring(raw);used=set();items=[];seen=set()
for it in root.findall('./channel/item'):
 t=re.sub(r'\s+',' ',it.findtext('title') or '').strip();link=clean(it.findtext('link'));src=it.find('source');sn=(src.text or '').strip() if src is not None else ''
 if sn:t=re.sub(r'\s*[-–—|]\s*'+re.escape(sn)+r'\s*$','',t,flags=re.I)
 if not t or not link or t in seen:continue
 seen.add(t);img=''
 for m in it.findall('{http://search.yahoo.com/mrss/}content')+it.findall('{http://search.yahoo.com/mrss/}thumbnail'):
  img=save(clean(m.attrib.get('url')),used)
  if img:break
 if not img:
  e=it.find('enclosure');img=save(clean(e.attrib.get('url')) if e is not None else '',used)
 if not img:continue
 items.append({'title':t,'url':link,'category':cat(t),'published':it.findtext('pubDate') or '','image':img,'source_url':clean(src.attrib.get('url') if src is not None else '')})
 if len(items)>=24:break
with open('news.json','w',encoding='utf-8') as f:json.dump({'updated_at':datetime.now(timezone.utc).isoformat(),'items':items},f,ensure_ascii=False,indent=2)
print('تم تحديث',len(items),'خبراً بصور RSS حقيقية')
if len(items)<8:raise SystemExit('عدد الأخبار المصورة غير كاف: '+str(len(items)))