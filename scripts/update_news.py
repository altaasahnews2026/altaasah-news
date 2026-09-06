import hashlib, html, json, os, re, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
NEWS_IMAGE_DIR='assets/news'
os.makedirs(NEWS_IMAGE_DIR, exist_ok=True)
HEADERS={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36','Accept':'text/html,application/xhtml+xml,image/avif,image/webp,application/json,*/*;q=0.8'}
NS={'media':'http://search.yahoo.com/mrss/'}

def fetch(url, timeout=15):
    req=urllib.request.Request(url,headers=HEADERS)
    with urllib.request.urlopen(req,timeout=timeout) as r:return r.read(),r.headers.get_content_type(),r.geturl()

def clean_url(u):
    u=html.unescape(str(u or '').strip())
    if u.startswith('//'):u='https:'+u
    return u if u.startswith('http') else ''

def clean_title(t,src=''):
    t=re.sub(r'\s+',' ',str(t or '')).strip(); src=re.sub(r'\s+',' ',str(src or '')).strip()
    if src:t=re.sub(r'\s*[-–—|]\s*'+re.escape(src)+r'\s*$','',t,flags=re.I).strip()
    return t.rstrip('-–—| ')

def category(t):
    if any(k in t for k in ['كركوك','زاخو']):return 'كركوك'
    if any(k in t for k in ['رياضة','دوري','ملعب','مباراة','منتخب','كرة','آسياد']):return 'رياضة'
    if any(k in t for k in ['اقتصاد','البنك المركزي','المصارف','الأسعار','تجارة','استثمار','النفط','الذهب']):return 'اقتصاد'
    if any(k in t for k in ['سياسة','حكومة','رئيس الوزراء','برلمان','وزير']):return 'سياسة'
    if any(k in t for k in ['أمن','أمني','شرطة','جيش','هجوم','تفجير','حدود']):return 'أمن'
    if any(k in t for k in ['العالم','دولي','فلسطين','إيران','أمريكا','السعودية','سوريا']):return 'عربي ودولي'
    return 'محلي'

def image_candidates(item):
    out=[]
    for m in item.findall('media:content',NS)+item.findall('media:thumbnail',NS):
        u=clean_url(m.attrib.get('url'))
        if u:out.append(u)
    e=item.find('enclosure')
    if e is not None:
        u=clean_url(e.attrib.get('url'))
        if u:out.append(u)
    desc=item.findtext('description') or ''
    for u in re.findall(r'<img[^>]+(?:src|data-src|data-original)=["\']([^"\']+)',desc,re.I):
        u=clean_url(u)
        if u:out.append(u)
    return list(dict.fromkeys(out))

def save_image(url,used):
    try:
        raw,typ,_=fetch(url,12)
        if len(raw)<3000 or not typ.startswith('image/') or 'svg' in typ:return ''
        if not(raw[:3]==b'\xff\xd8\xff' or raw.startswith(b'\x89PNG') or raw[:4]==b'RIFF' or raw[:6] in (b'GIF87a',b'GIF89a')):return ''
        digest=hashlib.sha256(raw).hexdigest()
        if digest in used:return ''
        ext={'image/jpeg':'.jpg','image/png':'.png','image/webp':'.webp','image/gif':'.gif'}.get(typ,'')
        if not ext:return ''
        name=digest[:24]+ext; path=os.path.join(NEWS_IMAGE_DIR,name)
        if not os.path.exists(path):open(path,'wb').write(raw)
        used.add(digest)
        return './assets/news/'+name
    except Exception:return ''

def extract_meta(text,base):
    vals=[]
    pats=[r'<meta[^>]+(?:property|name)=["\']og:image(?::secure_url)?["\'][^>]+content=["\']([^"\']+)',r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name)=["\']og:image(?::secure_url)?["\']',r'<meta[^>]+(?:property|name)=["\']twitter:image[^"\']*["\'][^>]+content=["\']([^"\']+)',r'<link[^>]+rel=["\']image_src["\'][^>]+href=["\']([^"\']+)']
    for p in pats:vals += re.findall(p,text,re.I)
    return [urllib.parse.urljoin(base,html.unescape(u)) for u in vals]

def google_images(title,used):
    try:
        q=urllib.parse.quote(title+' العراق خبر')
        url='https://www.google.com/search?tbm=isch&hl=ar&gl=iq&q='+q
        raw,_,_=fetch(url,18); text=raw.decode('utf-8','ignore')[:1500000]
        candidates=[]
        # Google image result pages embed many direct image URLs in JSON-like HTML.
        for u in re.findall(r'https?://[^"\\<> ]+?(?:jpg|jpeg|png|webp)(?:\?[^"\\<> ]*)?',text,re.I):
            u=html.unescape(u).replace('\\u003d','=').replace('\\u0026','&').replace('\\/','/')
            if any(x in u.lower() for x in ['gstatic.com','google.com','googleusercontent.com']):continue
            candidates.append(u)
        for u in dict.fromkeys(candidates):
            saved=save_image(u,used)
            if saved:return saved
    except Exception:pass
    return ''

def gdelt_image(title,used):
    try:
        q=urllib.parse.quote('"'+title.replace('"','')+'"')
        api='https://api.gdeltproject.org/api/v2/doc/doc?query='+q+'&mode=artlist&maxrecords=10&timespan=2d&sort=datedesc&format=json'
        raw,_,_=fetch(api,15); data=json.loads(raw.decode('utf-8','ignore'))
        for a in data.get('articles',[]):
            u=clean_url(a.get('socialimage') or a.get('socialImage') or a.get('image'))
            if u:
                saved=save_image(u,used)
                if saved:return saved
    except Exception:pass
    return ''

def page_image(url,used):
    try:
        raw,_,final=fetch(url,12); text=raw.decode('utf-8','ignore')[:700000]; pages=[(final,text)]
        try:
            jr,_,_=fetch('https://r.jina.ai/'+final,15); pages.append((final,jr.decode('utf-8','ignore')[:700000]))
        except Exception:pass
        links=[]
        for p in [r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)',r'<a[^>]+href=["\'](https?://[^"\']+)["\']']:
            links += re.findall(p,text,re.I)
        for u in links:
            u=clean_url(u)
            if u and 'news.google.com' not in u and u not in [x[0] for x in pages]:
                try:
                    rr,_,ff=fetch(u,10); pages.append((ff,rr.decode('utf-8','ignore')[:600000]))
                except Exception:pass
            if len(pages)>=5:break
        for base,txt in pages:
            for u in extract_meta(txt,base):
                saved=save_image(u,used)
                if saved:return saved
            for u in re.findall(r'<img[^>]+(?:src|data-src|data-original|srcset)=["\']([^"\']+)',txt,re.I):
                u=u.split(',')[0].strip().split(' ')[0]
                saved=save_image(urllib.parse.urljoin(base,html.unescape(u)),used)
                if saved:return saved
    except Exception:pass
    return ''

params=urllib.parse.urlencode({'q':'العراق when:1d','hl':'ar','gl':'IQ','ceid':'IQ:ar'})
raw,_,_=fetch('https://news.google.com/rss/search?'+params,20); root=ET.fromstring(raw)
items=[]; seen=set(); used=set()
for item in root.findall('./channel/item'):
    title=clean_title(item.findtext('title'),item.findtext('source')); link=clean_url(item.findtext('link'))
    if not title or not link or title in seen:continue
    seen.add(title); local=''
    for u in image_candidates(item):
        local=save_image(u,used)
        if local:break
    if not local:local=page_image(link,used)
    if not local:local=google_images(title,used)
    if not local:local=gdelt_image(title,used)
    if not local:
        print('تم استبعاد خبر بلا صورة حقيقية:',title); continue
    src=item.find('source'); source_url=clean_url(src.attrib.get('url') if src is not None else '')
    items.append({'title':title,'url':link,'category':category(title),'published':item.findtext('pubDate') or '','image':local,'source_url':source_url})
    if len(items)>=30:break
items.sort(key=lambda x:x.get('published',''),reverse=True)
with open('news.json','w',encoding='utf-8') as f:json.dump({'updated_at':datetime.now(timezone.utc).isoformat(),'items':items},f,ensure_ascii=False,indent=2)
print('تم تحديث',len(items),'خبراً بصور حقيقية فريدة')
if len(items)<10:raise SystemExit('عدد الأخبار ذات الصور الحقيقية أقل من الحد الآمن: '+str(len(items)))
