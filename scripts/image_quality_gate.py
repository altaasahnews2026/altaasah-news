from pathlib import Path
import json,hashlib,html,re,urllib.request,urllib.parse
from io import BytesIO
from PIL import Image,ImageOps
from difflib import SequenceMatcher
D=Path('assets/news');H={'User-Agent':'Mozilla/5.0 Chrome/128 Safari/537.36'}
def get(u):
 try:return urllib.request.urlopen(urllib.request.Request(u,headers=H),timeout=6).read()
 except:return b''
def clean(u):
 u=html.unescape(str(u or '').strip());return ('https:'+u[2:] if u.startswith('//') else u) if u.startswith(('http://','https://','//')) else ''
def norm(t):
 t=re.sub(r'[إأآا]','ا',t);t=re.sub(r'ى','ي',t);t=re.sub(r'ة','ه',t);return re.sub(r'\s+',' ',re.sub(r'[^\u0600-\u06ff\w\s]',' ',t)).strip().lower()
def ph(raw):
 try:
  with Image.open(BytesIO(raw)) as im:
   im=ImageOps.exif_transpose(im).convert('L')
   if im.width<320 or im.height<200:return None
   p=list(im.resize((16,16)).getdata());a=sum(p)/len(p);return sum((x>a)<<i for i,x in enumerate(p))
 except:return None
def good(raw):
 try:
  with Image.open(BytesIO(raw)) as im:
   if im.width<320 or im.height<200:return False
   p=list(im.convert('L').resize((24,24)).getdata());return max(p)-min(p)>=28
 except:return False
def og(url):
 s=get(url).decode('utf-8','ignore')
 for p in [r'<meta[^>]+(?:property|name)=["\'](?:og:image|twitter:image|image_src)["\'][^>]+content=["\']([^"\']+)',r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name)=["\'](?:og:image|twitter:image|image_src)["\']']:
  m=re.search(p,s,re.I)
  if m:return clean(urllib.parse.urljoin(url,m.group(1)))
 return ''
def search(q):
 u='https://www.bing.com/images/search?'+urllib.parse.urlencode({'q':'"'+q+'"','form':'HDRSC2'});s=get(u).decode('utf-8','ignore');out=[]
 for m in re.findall(r'"murl":"(https?[^"\\]+)"',s,re.I):
  x=clean(m.replace('\\/','/'))
  if x and x not in out:out.append(x)
 return out[:12]
d=json.loads(Path('news.json').read_text(encoding='utf-8'));items=d.get('items',[]);seen=[];visual=[];fixed=[]
for item in items:
 t=str(item.get('title',''));n=norm(t)
 if any(SequenceMatcher(None,n,o).ratio()>=.78 for o in seen):continue
 candidates=[];u=og(item.get('url',''))
 if u:candidates.append(u)
 candidates+=search(t)
 chosen=''
 for u in candidates:
  raw=get(u)
  if not raw or not good(raw):continue
  v=ph(raw)
  if v is not None and any((v-x).bit_count()<=7 for x in visual):continue
  try:
   with Image.open(BytesIO(raw)) as im:ext={"JPEG":".jpg","PNG":".png","WEBP":".webp"}.get(im.format,'.jpg')
  except:continue
  name='source-'+hashlib.sha256(raw).hexdigest()[:24]+ext;path=D/name
  if not path.exists():path.write_bytes(raw)
  chosen='./assets/news/'+name
  if v is not None:visual.append(v)
  break
 if not chosen:continue
 item['image']=chosen;item['original_image']=chosen;seen.append(n);fixed.append(item)
 if len(fixed)>=24:break
if len(fixed)<20:raise SystemExit(f'بوابة جودة الصور رفضت الأخبار/الصور: {len(fixed)} فقط')
d['items']=fixed;Path('news.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8');print('بوابة الجودة: ',len(fixed),'صور مرتبطة ومختلفة بصرياً')