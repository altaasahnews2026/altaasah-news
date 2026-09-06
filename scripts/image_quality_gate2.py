from pathlib import Path
import json,hashlib,html,re,urllib.request,urllib.parse
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor,as_completed
from PIL import Image,ImageOps
D=Path('assets/news');H={'User-Agent':'Mozilla/5.0 Chrome/128 Safari/537.36'}
def get(u):
 try:return urllib.request.urlopen(urllib.request.Request(u,headers=H),timeout=6).read()
 except:return b''
def clean(u):
 u=html.unescape(str(u or '').strip());return ('https:'+u[2:] if u.startswith('//') else u) if u.startswith(('http://','https://','//')) else ''
def norm(t):
 t=re.sub(r'[إأآا]','ا',t);t=re.sub(r'ى','ي',t);t=re.sub(r'ة','ه',t);return re.sub(r'\s+',' ',re.sub(r'[^\u0600-\u06ff\w\s]',' ',t)).strip().lower()
def good(raw):
 try:
  with Image.open(BytesIO(raw)) as im:im=ImageOps.exif_transpose(im);return im.width>=320 and im.height>=200
 except:return False
def og(u):
 if not u:return ''
 s=get(u).decode('utf-8','ignore')
 for p in [r'<meta[^>]+(?:property|name)=["\'](?:og:image|twitter:image|image_src)["\'][^>]+content=["\']([^"\']+)',r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name)=["\'](?:og:image|twitter:image|image_src)["\']']:
  m=re.search(p,s,re.I)
  if m:return clean(urllib.parse.urljoin(u,m.group(1)))
 return ''
def local(v):
 p=str(v or '').strip();p=p[2:] if p.startswith('./') else p
 if not p.startswith('assets/news/'):return None
 q=Path(p);return q if q.is_file() else None
d=json.loads(Path('news.json').read_text(encoding='utf-8'));unique=[];seen=set()
for item in d.get('items',[]):
 t=norm(str(item.get('title','')))
 if len(re.findall(r'[\u0600-\u06ff]',str(item.get('title',''))))<6 or t in seen:continue
 seen.add(t);unique.append(item)
 if len(unique)>=24:break
resolved={}
with ThreadPoolExecutor(max_workers=12) as ex:
 fs={ex.submit(og,x.get('url','')):i for i,x in enumerate(unique)}
 for f in as_completed(fs):
  i=fs[f]
  try:resolved[i]=f.result()
  except:resolved[i]=''
used=set();fixed=[]
for i,item in enumerate(unique):
 candidates=[];u=resolved.get(i)
 if u:candidates.append(u)
 op=local(item.get('original_image'))
 if op:candidates.append(str(op))
 oi=local(item.get('image'))
 if oi and 'news-template-' not in oi.name:candidates.append(str(oi))
 chosen=''
 for u in candidates:
  try:raw=get(u) if str(u).startswith('http') else Path(u).read_bytes()
  except:continue
  if not raw or not good(raw):continue
  h=hashlib.sha256(raw).hexdigest()
  if h in used:continue
  try:
   with Image.open(BytesIO(raw)) as im:ext={"JPEG":".jpg","PNG":".png","WEBP":".webp"}.get(im.format,'.jpg')
  except:continue
  name='source-'+h[:24]+ext;path=D/name
  if not path.exists():path.write_bytes(raw)
  used.add(h);chosen='./assets/news/'+name;break
 if chosen:item['image']=chosen;item['original_image']=chosen;fixed.append(item)
if len(fixed)<20:raise SystemExit(f'بوابة جودة الصور لم تجد 20 صورة صالحة: {len(fixed)}')
d['items']=fixed[:24];Path('news.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8');print('بوابة جودة الصور: OK',len(d['items']))