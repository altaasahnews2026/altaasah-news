import hashlib, html, json, re, urllib.parse, urllib.request
from datetime import datetime, timezone, timedelta
from io import BytesIO
from pathlib import Path
from PIL import Image

HEADERS={'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/128 Safari/537.36','Accept-Language':'ar-IQ,ar;q=0.9,en;q=0.7'}
MAX_AGE=timedelta(hours=30)
NOW=datetime.now(timezone.utc)
SOURCES=[('https://rudaw.net/arabic/authors/r%C3%BBdaw','رووداو'),('https://news.imn.iq/','قناة العراقية'),('https://alsharqiya.com/news','قناة الشرقية'),('https://alsharqiya.com/','قناة الشرقية'),('https://alfallujah.tv/','قناة الفلوجة'),('https://www.alarabiya.net/arab-and-world/iraq','العربية'),('https://www.alsumaria.tv/news','السومرية نيوز'),('https://www.alsumaria.tv/alsumarianews','السومرية نيوز'),('https://shafaq.com/ar','شفق نيوز'),('https://ninanews.com/website/','وكالة نينا'),('https://www.sjc.iq/','مجلس القضاء الأعلى')]
GENERIC=('logo','icon','favicon','avatar','placeholder','default','sprite','banner','advert','ads','loading','no-image','profile')
GOVERNORATES={
 'بغداد':('بغداد','بغداد','أبو غريب','ابو غريب','المدائن','التاجي','المحمودية','الطارمية'),
 'البصرة':('البصرة','البصره','الزبير','أبو الخصيب','ابي الخصيب','القرنة','الفاو','شط العرب'),
 'نينوى':('نينوى','الموصل','تلعفر','سنجار','الحمدانية','بعشيقة','تلكيف','الحضر'),
 'الأنبار':('الأنبار','الانبار','الرمادي','الفلوجة','حديثة','القائم','عانة','راوة','هيت','الرطبة'),
 'صلاح الدين':('صلاح الدين','تكريت','سامراء','بيجي','بلد','الدجيل','الشرقاط'),
 'ديالى':('ديالى','بعقوبة','خانقين','المقدادية','بلدروز','الخالص'),
 'واسط':('واسط','الكوت','النعمانية','الحي','الصويرة'),
 'ميسان':('ميسان','العمارة','المجر الكبير','قلعة صالح','الكحلاء'),
 'ذي قار':('ذي قار','الناصرية','الشطرة','الرفاعي','سوق الشيوخ','الجبايش'),
 'المثنى':('المثنى','السماوة','الرميثة','الخضر'),
 'بابل':('بابل','الحلة','المسيب','المحاويل','الهاشمية'),
 'كربلاء':('كربلاء','كربلاء المقدسة','عين التمر','الهندية'),
 'النجف':('النجف','النجف الأشرف','المناذرة','الكوفة','المشخاب'),
 'القادسية':('القادسية','الديوانية','الشامية','عفك','الحمزة'),
 'دهوك':('دهوك','زاخو','العمادية','سميل','آميدي'),
 'أربيل':('أربيل','اربيل','شقلاوة','كويسنجق','سوران','حرير'),
 'السليمانية':('السليمانية','السليمانيه','حلبجة','رانية','دوكان','كلار'),
 'كركوك':('كركوك','التون كوبري','التونكوبري','آلتون كوبري','الدبس','داقوق','الحويجة','ليلان','الرشاد','الرياض','الزاب','قره تبه','جيمن','باي حسن','بابا كركر','محمد سمعان','محمد سمعان آغا','سمعان آغا','محافظ كركوك')
}
IRAQ=('العراق','الحشد','البرلمان العراقي','الحكومة العراقية','القوات العراقية','مجلس الوزراء')
INTL=('فلسطين','غزة','إسرائيل','اسرائيل','لبنان','سوريا','الأردن','الاردن','السعودية','الإمارات','الامارات','الكويت','قطر','البحرين','عُمان','عمان','اليمن','مصر','ليبيا','تونس','الجزائر','المغرب','السودان','إيران','ايران','تركيا','أمريكا','امريكا','أميركا','روسيا','أوكرانيا','الصين','أوروبا','بريطانيا','فرنسا','ألمانيا','دولي','دولية')
ALLOWED_HOSTS=('rudaw.net','www.rudaw.net','news.imn.iq','imn.iq','www.imn.iq','alsharqiya.com','www.alsharqiya.com','alfallujah.tv','www.alfallujah.tv','alarabiya.net','www.alarabiya.net','alsumaria.tv','www.alsumaria.tv','shafaq.com','www.shafaq.com','ninanews.com','www.ninanews.com','sjc.iq','www.sjc.iq')

def get(url,timeout=12):
 try:
  r=urllib.request.Request(url,headers=HEADERS)
  with urllib.request.urlopen(r,timeout=timeout) as x:return x.read(),x.geturl()
 except:return b'',url

def clean(v,base):return urllib.parse.urljoin(base,html.unescape(str(v or '').strip()))
def host(u):return urllib.parse.urlparse(u).netloc.lower().split(':')[0]
def title(v):return re.sub(r'\s+',' ',html.unescape(re.sub('<[^>]+>',' ',str(v or '')))).strip()
def date(v):
 if not v:return None
 v=html.unescape(str(v)).strip()
 try:
  from email.utils import parsedate_to_datetime
  return parsedate_to_datetime(v).astimezone(timezone.utc)
 except:pass
 try:
  d=datetime.fromisoformat(v.replace('Z','+00:00'));return d.astimezone(timezone.utc) if d.tzinfo else d.replace(tzinfo=timezone.utc)
 except:return None

def fresh(d):return bool(d and NOW-timedelta(minutes=5)<=d<=NOW+timedelta(minutes=10) or d and NOW-d<=MAX_AGE)
def meta(t,names):
 for n in names:
  for p in (rf'<meta[^>]+(?:property|name)=["\']{re.escape(n)}["\'][^>]+content=["\']([^"\']+)',rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name)=["\']{re.escape(n)}["\']'):
   m=re.search(p,t,re.I)
   if m:return html.unescape(m.group(1)).strip()
 return ''
def published(t):
 vals=[]
 for n in ('article:published_time','og:published_time','datePublished','pubdate','publishdate','date','dateModified'):
  x=meta(t,[n])
  if x:vals.append(x)
 for m in re.finditer(r'<time[^>]+(?:datetime|data-datetime)=["\']([^"\']+)',t,re.I):vals.append(m.group(1))
 for v in vals:
  d=date(v)
  if d:return d
 return None

def image(t,base):
 cand=[]
 for n in ('og:image','og:image:url','twitter:image','twitter:image:src','image_src'):
  x=meta(t,[n])
  if x:cand.append(clean(x,base))
 for m in re.finditer(r'<img[^>]+(?:src|data-src|data-original)=["\']([^"\']+)',t,re.I):
  cand.append(clean(m.group(1),base))
  if len(cand)>=20:break
 seen=set()
 for u in cand:
  if not u or u in seen or '.svg' in u.lower():continue
  seen.add(u);p=urllib.parse.urlparse(u).path.lower()
  if any(w in p for w in GENERIC):continue
  raw,_=get(u,10)
  try:
   with Image.open(BytesIO(raw)) as im:
    if im.width<360 or im.height<220 or im.width/max(1,im.height)>4.5 or im.height/max(1,im.width)>4.5:continue
    im.verify()
   return raw
  except:continue
 return b''

def store(raw):
 h=hashlib.sha256(raw).hexdigest();p=Path('assets/news')/(h[:24]+'.jpg');p.parent.mkdir(parents=True,exist_ok=True)
 if not p.exists():p.write_bytes(raw)
 return './assets/news/'+p.name

def governorate(t):
 t=title(t)
 for name,terms in GOVERNORATES.items():
  if any(x in t for x in terms):return name
 return ''

def region(t):
 g=governorate(t)
 if g:return g
 if any(x in t for x in INTL):return 'عربي ودولي'
 if any(x in t for x in IRAQ):return 'العراق'
 return 'العراق'

def category(t):
 if any(x in t for x in ('رياضة','كرة','منتخب','مباراة','دوري','بطولة','ألعاب')):return 'رياضة'
 if any(x in t for x in ('دولار','ذهب','اقتصاد','مصرف','بنك','نفط','استثمار','أسعار','تجارة','بورصة','مالية')):return 'اقتصاد'
 if any(x in t for x in ('حكومة','وزير','رئيس الوزراء','برلمان','نائب','حزب','انتخابات','سياسة')):return 'سياسة'
 if any(x in t for x in ('هجوم','انفجار','شرطة','جيش','أمن','إرهاب','مسيرة','مخدرات','سلاح','اعتقال','مقتل','قتلى','حريق')):return 'أمن'
 if any(x in t for x in INTL):return 'عربي ودولي'
 return 'محليات'

def rows(page,base):
 out=[];seen=set()
 for m in re.finditer(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',page,re.I|re.S):
  u=clean(m.group(1),base);t=title(m.group(2))
  if len(t)<12 or u in seen:continue
  h=host(u)
  if h not in ALLOWED_HOSTS:continue
  if any(z in u for z in ('/authors/','/categories/','/category/','/tag/','/search','/contact','/about','/login')):continue
  seen.add(u);out.append((t,u))
 return out[:160]

data=json.loads(Path('news.json').read_text(encoding='utf-8'))
items=data.get('items',[]); urls={x.get('url') for x in items}; titles={x.get('title') for x in items}
added=0
for source_url,source_name in SOURCES:
 raw,final=get(source_url,12)
 if not raw:continue
 text=raw.decode('utf-8','ignore')
 for fallback,url in rows(text,final):
  if url in urls:continue
  article,article_final=get(url,12)
  if not article:continue
  at=article.decode('utf-8','ignore');d=published(at)
  if not fresh(d):continue
  t=title(meta(at,['og:title','twitter:title']) or fallback)
  if not t or t in titles:continue
  rawimg=image(at,article_final)
  if not rawimg:continue
  img=store(rawimg);g=governorate(t);r=region(t)
  item={'title':t,'url':article_final,'category':category(t),'region':r,'governorate':g,'published':d.isoformat(),'image':img,'original_image':img,'source_url':article_final,'source_name':source_name,'breaking':False,'kirkuk':g=='كركوك','report':False}
  items.append(item);urls.add(article_final);titles.add(t);added+=1

# ترتيب موحد: الأحدث أولا. لا نعطي كركوك أو أي محافظة أولوية للخبر الرئيسي.
items.sort(key=lambda x:x.get('published',''),reverse=True)
data['items']=items[:60]
data['updated_at']=datetime.now(timezone.utc).isoformat()
Path('news.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
print('AUGMENT SOURCES: added',added,'items; by governorate', {g:sum(x.get('governorate')==g for x in data['items']) for g in GOVERNORATES}, 'total',len(data['items']))
