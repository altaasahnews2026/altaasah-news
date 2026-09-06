import hashlib
import html
import json
import os
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

NEWS_IMAGE_DIR='assets/news'
os.makedirs(NEWS_IMAGE_DIR,exist_ok=True)
HEADERS={'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126 Safari/537.36'}
NS={'media':'http://search.yahoo.com/mrss/'}

def fetch(url,timeout=10):
    req=urllib.request.Request(url,headers=HEADERS)
    with urllib.request.urlopen(req,timeout=timeout) as r:return r.read(),r.headers.get_content_type()

def clean_title(t,src=''):
    t=re.sub(r'\s+',' ',str(t or '')).strip()
    src=re.sub(r'\s+',' ',str(src or '')).strip()
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
    for u in re.findall(r'<img[^>]+(?:src|data-src)=["\']([^"\']+)',desc,re.I):
        u=clean_url(u)
        if u:out.append(u)
    return list(dict.fromkeys(out))

def save_image(url):
    try:
        raw,typ=fetch(url,8)
        if len(raw)<8000 or not typ.startswith('image/') or 'svg' in typ:return ''
        if not(raw[:3]==b'\xff\xd8\xff' or raw.startswith(b'\x89PNG') or raw[:4]==b'RIFF' or raw[:6] in (b'GIF87a',b'GIF89a')):return ''
        ext={'image/jpeg':'.jpg','image/png':'.png','image/webp':'.webp','image/gif':'.gif'}.get(typ,'')
        if not ext:return ''
        name=hashlib.sha256(raw).hexdigest()[:24]+ext
        path=os.path.join(NEWS_IMAGE_DIR,name)
        if not os.path.exists(path):open(path,'wb').write(raw)
        return './assets/news/'+name
    except Exception:return ''

def placeholder(title):
    name='no-image-'+hashlib.sha256(title.encode()).hexdigest()[:16]+'.svg'
    p=os.path.join(NEWS_IMAGE_DIR,name)
    if not os.path.exists(p):open(p,'w',encoding='utf-8').write('<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="700"><rect width="100%" height="100%" fill="#e9eef4"/><text x="50%" y="50%" text-anchor="middle" font-family="Arial" font-size="38" fill="#18324d">لا تتوفر صورة لهذا الخبر</text></svg>')
    return './assets/news/'+name

params=urllib.parse.urlencode({'q':'العراق when:1d','hl':'ar','gl':'IQ','ceid':'IQ:ar'})
try:
    raw,_=fetch('https://news.google.com/rss/search?'+params,12)
    root=ET.fromstring(raw)
except Exception as e:
    print('تعذر جلب الأخبار:',e);raise SystemExit(0)
items=[];seen=set();used=set()
for item in root.findall('./channel/item'):
    title=clean_title(item.findtext('title'),item.findtext('source'))
    link=clean_url(item.findtext('link'))
    if not title or not link or title in seen:continue
    seen.add(title)
    local=''
    for u in image_candidates(item):
        local=save_image(u)
        if local and local not in used:used.add(local);break
    if not local:local=placeholder(title)
    items.append({'title':title,'url':link,'category':category(title),'published':item.findtext('pubDate') or '','image':local,'source_url':clean_url((item.find('source').attrib.get('url') if item.find('source') is not None else ''))})
items.sort(key=lambda x:x.get('published',''),reverse=True)
with open('news.json','w',encoding='utf-8') as f:json.dump({'updated_at':datetime.now(timezone.utc).isoformat(),'items':items[:30]},f,ensure_ascii=False,indent=2)
print('تم تحديث',len(items[:30]),'خبراً بسرعة')