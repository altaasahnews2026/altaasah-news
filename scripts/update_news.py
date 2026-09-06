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
    pats=[r'<meta[^>]+(?:property|name)=["\']og:image(?::secure_url)?["\'][^>]+content=["\']([^"\']+)',r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name)=["\']og:image(?::secure_url)?["\']',r'<meta[^>]+(?:property|name)=["\']twitter:image[^"\']*["\'][^>]+content=["\']([^"\']+)',r'<link[^>]+rel=["\']image_src["\'][^>]+href=["\']([^"\']+)']
    for p in pats: vals += re.findall(p,text,re.I)
    return [urllib.parse.urljoin(base,html.unescape(u)) for u in vals]
def markdown_images(text,base):
    vals=[]
    for u in re.findall(r'!\[[^\]]*\]\((https?://[^)\s]+)',text): vals.append(urllib.parse.urljoin(base,u))
    return vals
def page_image(url):
    try:
        raw,_,final=fetch(url,12); text=raw.decode('utf-8','ignore')[:700000]
        pages=[(final,text)]
        # Jina Reader is used only as a fallback parser for pages that block normal metadata extraction.
        if final.startswith('http'):
            for scheme in ('https://r.jina.ai/http://','https://r.jina.ai/https://'):
                if final.startswith(scheme.replace('r.jina.ai/','')): continue
            try:
                jr,_,jf=fetch('https://r.jina.ai/'+final,15)
                jt=jr.decode('utf-8','ignore')[:700000]
                pages.append((final,jt))
            except Exception: pass
        links=[]
        for p in [r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)',r'<a[^>]+href=["\'](https?://[^"\']+)["\']']:
            links += re.findall(p,text,re.I)
        for u in links:
            u=clean_url(u)
            if u and 'news.google.com' not in u and u not in [x[0] for x in pages]:
                try:
                    rr,_,ff=fetch(u,8); tt=rr.decode('utf-8','ignore')[:600000]; pages.append((ff,tt))
                except Exception: pass
            if len(pages)>=5: break
        for base,txt in pages:
            candidates=extract_meta(txt,base)+markdown_images(txt,base)
            for u in candidates:
                saved=save_image(u)
                if saved:return saved
            for u in re.findall(r'<img[^>]+(?:src|data-src|data-original|srcset)=["\']([^"\']+)',txt,re.I):
                u=u.split(',')[0].strip().split(' ')[0]; u=urllib.parse.urljoin(base,html.unescape(u)); saved=save_image(u)
                if saved:return saved
    except Exception as e: print('image error',e)
    return ''
def placeholder(title):
    name='no-image-'+hashlib.sha256(title.encode()).hexdigest()[:16]+'.svg'; p=os.path.join(NEWS_IMAGE_DIR,name)
    if not os.path.exists(p):open(p,'w',encoding='utf-8').write('<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="700"><rect width="100%" height="100%" fill="#e9eef4"/><text x="50%" y="50%" text-anchor="middle" font-family="Arial" font-size="38" fill="#18324d">لا تتوفر صورة لهذا الخبر</text></svg>')
    return './assets/news/'+name
params=urllib.parse.urlencode({'q':'العراق when:1d','hl':'ar','gl':'IQ','ceid':'IQ:ar'})
raw,_,_=fetch('https://news.google.com/rss/search?'+params,15); root=ET.fromstring(raw)
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
    if not local:local=placeholder(title)
    src=item.find('source'); source_url=clean_url(src.attrib.get('url') if src is not None else '')
    items.append({'title':title,'url':link,'category':category(title),'published':item.findtext('pubDate') or '','image':local,'source_url':source_url})
items.sort(key=lambda x:x.get('published',''),reverse=True)
with open('news.json','w',encoding='utf-8') as f:json.dump({'updated_at':datetime.now(timezone.utc).isoformat(),'items':items[:30]},f,ensure_ascii=False,indent=2)
print('تم تحديث',len(items[:30]),'خبراً مع تحسين استخراج الصور الحقيقية')