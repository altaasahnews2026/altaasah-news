import hashlib, html, json, os, re, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

NEWS_IMAGE_DIR='assets/news'; os.makedirs(NEWS_IMAGE_DIR,exist_ok=True)
HEADERS={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36','Accept':'text/html,application/xhtml+xml,image/avif,image/webp,*/*;q=0.8'}
NS={'media':'http://search.yahoo.com/mrss/'}

def fetch(url,timeout=12):
    req=urllib.request.Request(url,headers=HEADERS)
    with urllib.request.urlopen(req,timeout=timeout) as r:return r.read(),r.headers.get_content_type(),r.geturl()

def clean_title(t,src=''):
    t=re.sub(r'\s+',' ',str(t or '')).strip(); src=re.sub(r'\s+',' ',str(src or '')).strip()
    if src:t=re.sub(r'\s*[-–—|]\s*'+re.escape(src)+r'\s*$','',t,flags=re.I).strip()
    return t.rstrip('-–—| ')

def category(t):
    if any(k in t for k in ['كركوك','زاخو']):return 'كركوك'
    if any(k in t for k in ['رياضة','دوري','ملعب','مباراة','منتخب','كرة']):return 'رياضة'
    if any(k in t for k in ['اقتصاد','البنك المركزي','المصارف','الأسعار','تجارة','استثمار','النفط','الذهب']):return 'اقتصاد'
    if any(k in t for k in ['سياسة','حكومة','رئيس الوزراء','برلمان','وزير']):return 'سياسة'
    if any(k in t for k in ['أمن','أمني','شرطة','جيش','هجوم','تفجير','حدود']):return 'أمن'
    if any(k in t for k in ['العالم','دولي','فلسطين','إيران','أمريكا','السعودية','سوريا']):return 'عربي ودولي'
    return 'محلي'

def clean_url(u):
    u=html.unescape(str(u or '').strip())
    if u.startswith('//'):u='https:'+u
    return u if u.startswith('http') else ''

def image_candidates(item):
    out=[]
    for m in item.findall('.//media:content',NS)+item.findall('.//media:thumbnail',NS):
        u=clean_url(m.attrib.get('url'))
        if u:out.append(u)
    for tag in item.findall('enclosure')+item.findall('.//enclosure'):
        u=clean_url(tag.attrib.get('url'))
        if u:out.append(u)
    desc=item.findtext('description') or ''
    for u in re.findall(r'<img[^>]+(?:src|data-src|data-original|data-lazy-src)=["\']([^"\']+)',desc,re.I):
        u=clean_url(u)
        if u:out.append(u)
    return list(dict.fromkeys(out))

def save_image(url):
    try:
        raw,typ,_=fetch(url,10)
        if len(raw)<3000 or not typ.startswith('image/') or 'svg' in typ:return ''
        if not(raw[:3]==b'\xff\xd8\xff' or raw.startswith(b'\x89PNG') or raw[:4]==b'RIFF' or raw[:6] in (b'GIF87a',b'GIF89a')):return ''
        ext={'image/jpeg':'.jpg','image/png':'.png','image/webp':'.webp','image/gif':'.gif'}.get(typ,'')
        if not ext:return ''
        name=hashlib.sha256(raw).hexdigest()[:24]+ext; path=os.path.join(NEWS_IMAGE_DIR,name)
        if not os.path.exists(path):open(path,'wb').write(raw)
        return './assets/news/'+name
    except Exception:return ''

def extract_meta(text,base):
    vals=[]
    for tag in re.findall(r'<meta\b[^>]*>',text,re.I):
        attrs={k.lower():html.unescape(v) for k,v in re.findall(r'([\w:-]+)\s*=\s*["\']([^"\']*)',tag)}
        key=(attrs.get('property') or attrs.get('name') or '').lower()
        if key in ('og:image','og:image:url','og:image:secure_url','twitter:image','twitter:image:src'):
            if attrs.get('content'):vals.append(attrs['content'])
    for tag in re.findall(r'<link\b[^>]*>',text,re.I):
        attrs={k.lower():html.unescape(v) for k,v in re.findall(r'([\w:-]+)\s*=\s*["\']([^"\']*)',tag)}
        if 'image_src' in (attrs.get('rel') or '').lower() and attrs.get('href'):vals.append(attrs['href'])
    # JSON-LD image fields used by many Iraqi news sites.
    for m in re.finditer(r'"(?:image|thumbnailUrl)"\s*:\s*"(https?[^"\\]+)',text,re.I):vals.append(m.group(1).replace('\\/','/'))
    return [urllib.parse.urljoin(base,u) for u in vals]

def html_images(text,base):
    out=[]
    for tag in re.findall(r'<img\b[^>]*>',text,re.I):
        attrs={k.lower():html.unescape(v) for k,v in re.findall(r'([\w:-]+)\s*=\s*["\']([^"\']*)',tag)}
        for k in ('src','data-src','data-original','data-lazy-src'):
            if attrs.get(k):out.append(urllib.parse.urljoin(base,attrs[k]))
        if attrs.get('srcset'):
            for part in attrs['srcset'].split(','):
                u=part.strip().split(' ')[0]
                if u:out.append(urllib.parse.urljoin(base,u))
    return list(dict.fromkeys(out))

def page_image(url):
    try:
        raw,_,final=fetch(url,15); text=raw.decode('utf-8','ignore')[:700000]
        pages=[(final,text)]; seen_pages={final}
        # First try the redirected/canonical page itself.
        for u in extract_meta(text,final)+html_images(text,final)[:20]:
            saved=save_image(u)
            if saved:return saved
        # Google News may expose the publisher article URL in canonical, anchors or JSON.
        links=[]
        for pat in [r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)',r'<a[^>]+href=["\'](https?://[^"\']+)["\']',r'"url"\s*:\s*"(https?[^"\\]+)']:
            links += re.findall(pat,text,re.I)
        for u in links:
            u=clean_url(u).replace('\\/','/')
            if not u or 'news.google.com' in u or u in seen_pages:continue
            try:
                rr,_,ff=fetch(u,10); tt=rr.decode('utf-8','ignore')[:700000]
                pages.append((ff,tt)); seen_pages.add(ff)
            except Exception:pass
            if len(pages)>=8:break
        for base,txt in pages[1:]:
            for u in extract_meta(txt,base)+html_images(txt,base)[:40]:
                saved=save_image(u)
                if saved:return saved
    except Exception:pass
    return ''

params=urllib.parse.urlencode({'q':'العراق when:1d','hl':'ar','gl':'IQ','ceid':'IQ:ar'})
try:
    raw,_,_=fetch('https://news.google.com/rss/search?'+params,15); root=ET.fromstring(raw)
except Exception as e:
    print('تعذر جلب الأخبار:',e); raise SystemExit(0)
items=[]; seen=set(); used=set()
for item in root.findall('./channel/item'):
    title=clean_title(item.findtext('title'),item.findtext('source')); link=clean_url(item.findtext('link'))
    if not title or not link or title in seen:continue
    seen.add(title); local=''
    for u in image_candidates(item):
        local=save_image(u)
        if local and local not in used:used.add(local);break
    if not local:local=page_image(link)
    if local and local not in used:used.add(local)
    if not local:
        print('تجاوز خبر بلا صورة حقيقية:',title)
        continue
    src=item.find('source'); source_url=clean_url(src.attrib.get('url') if src is not None else '')
    items.append({'title':title,'url':link,'category':category(title),'published':item.findtext('pubDate') or '','image':local,'source_url':source_url})
items.sort(key=lambda x:x.get('published',''),reverse=True)
if not items:
    raise SystemExit('لم يتم العثور على أي صورة خبر حقيقية؛ لن يتم نشر بيانات وهمية')
with open('news.json','w',encoding='utf-8') as f:json.dump({'updated_at':datetime.now(timezone.utc).isoformat(),'items':items[:30]},f,ensure_ascii=False,indent=2)
print('تم تحديث',len(items[:30]),'خبراً بصور حقيقية فقط')