import hashlib
import html
import json
import os
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

QUERIES = ["العراق", "العراق سياسة أمن اقتصاد", "كركوك", "العراق رياضة"]
NS = {"media": "http://search.yahoo.com/mrss/", "content": "http://purl.org/rss/1.0/modules/content/"}
NEWS_IMAGE_DIR = "assets/news"
os.makedirs(NEWS_IMAGE_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
}

def fetch(url, timeout=15):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read(), r.headers.get_content_type()

def clean_url(url, base=""):
    if not url:
        return ""
    u = urllib.parse.urljoin(base, html.unescape(str(url)).strip().replace("&amp;", "&"))
    if u.startswith("//"):
        u = "https:" + u
    if u.startswith("http://"):
        u = "https://" + u[7:]
    return u if u.startswith("https://") else ""

def category(title):
    t = str(title or "")
    if any(k in t for k in ["كركوك", "زاخو", "الفيحاء"]): return "كركوك"
    if any(k in t for k in ["رياضة", "دوري", "ملعب", "مباراة", "منتخب", "كرة"]): return "رياضة"
    if any(k in t for k in ["اقتصاد", "البنك المركزي", "المصارف", "الأسعار", "تجارة", "استثمار", "النفط", "الذهب"]): return "اقتصاد"
    if any(k in t for k in ["سياسة", "حكومة", "رئيس الوزراء", "برلمان", "وزير", "مليشيات"]): return "سياسة"
    if any(k in t for k in ["أمن", "أمني", "أمنية", "شرطة", "جيش", "هجوم", "تفجير", "حدود"]): return "أمن"
    if any(k in t for k in ["العالم", "دولي", "فلسطين", "إيران", "أمريكا", "السعودية", "سوريا"]): return "عربي ودولي"
    return "محلي"

def publisher_url(item):
    src = item.find("source")
    if src is not None:
        u = clean_url(src.attrib.get("url", ""))
        if u: return u
    return clean_url(item.findtext("link") or "")

def page_candidates(url):
    out = []
    try:
        raw, typ = fetch(url, 12)
        if "html" not in typ: return out
        text = raw[:5000000].decode("utf-8", errors="ignore")
        tags = re.findall(r'<meta\b[^>]*>', text, re.I)
        for tag in tags:
            if re.search(r'(?:property|name)\s*=\s*["\'](?:og:image(?::secure_url)?|twitter:image(?::src)?)["\']', tag, re.I):
                m = re.search(r'content\s*=\s*["\']([^"\']+)', tag, re.I)
                if m: out.append(clean_url(m.group(1), url))
        for tag in re.findall(r'<link\b[^>]*>', text, re.I):
            if re.search(r'rel\s*=\s*["\']image_src["\']', tag, re.I):
                m = re.search(r'href\s*=\s*["\']([^"\']+)', tag, re.I)
                if m: out.append(clean_url(m.group(1), url))
        for m in re.finditer(r'\"image\"\s*:\s*(\"([^\"]+)\"|\[(.*?)\])', text, re.I):
            val = m.group(2) or ""
            if val: out.append(clean_url(val, url))
        for m in re.finditer(r'<img\b[^>]*(?:src|data-src|data-lazy-src)\s*=\s*["\']([^"\']+)', text, re.I):
            u = clean_url(m.group(1), url)
            if u: out.append(u)
    except Exception as e:
        print("تعذر تحليل صفحة المصدر:", e)
    return unique_urls(out)

def rss_candidates(item):
    out = []
    for tag in ["content", "thumbnail"]:
        for media in item.findall(f"media:{tag}", NS):
            u = clean_url(media.attrib.get("url", ""))
            if u: out.append(u)
    enc = item.find("enclosure")
    if enc is not None:
        u = clean_url(enc.attrib.get("url", ""))
        if u: out.append(u)
    for text in [item.findtext("description") or "", item.findtext("content:encoded", namespaces=NS) or ""]:
        for m in re.finditer(r'<img[^>]+(?:src|data-src)\s*=\s*["\']([^"\']+)', text, re.I):
            u = clean_url(m.group(1))
            if u: out.append(u)
    return unique_urls(out)

def unique_urls(values):
    seen = set(); out = []
    for u in values:
        if not u or u in seen or "googleusercontent.com" in u: continue
        seen.add(u); out.append(u)
    return out

def looks_like_real_photo(raw, typ, url):
    if not raw or len(raw) < 12000 or not typ.startswith("image/"): return False
    if typ in {"image/svg+xml", "image/x-icon", "image/vnd.microsoft.icon"}: return False
    low = url.lower()
    if any(x in low for x in ["logo", "favicon", "icon", "avatar", "sprite"]): return False
    if raw[:3] == b"\xff\xd8\xff" or raw.startswith(b"\x89PNG") or raw[:4] == b"RIFF" or raw[:6] in (b"GIF87a", b"GIF89a"): return True
    return False

def save_image(url):
    try:
        raw, typ = fetch(url, 15)
        if not looks_like_real_photo(raw, typ, url): return ""
        digest = hashlib.sha256(raw).hexdigest()
        ext = {"image/jpeg":".jpg","image/png":".png","image/webp":".webp","image/gif":".gif"}.get(typ)
        if not ext: return ""
        name = digest[:24] + ext
        path = os.path.join(NEWS_IMAGE_DIR, name)
        if not os.path.exists(path):
            with open(path, "wb") as f: f.write(raw)
        return "./assets/news/" + name
    except Exception as e:
        print("تعذر حفظ الصورة:", e)
        return ""

def neutral_placeholder(title):
    digest = hashlib.sha256(title.encode("utf-8")).hexdigest()[:16]
    path = os.path.join(NEWS_IMAGE_DIR, f"no-image-{digest}.svg")
    if not os.path.exists(path):
        safe = html.escape(title[:55])
        path_text = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="700" viewBox="0 0 1200 700"><rect width="1200" height="700" fill="#e9eef3"/><rect x="70" y="70" width="1060" height="560" rx="28" fill="#dbe3eb"/><text x="600" y="330" text-anchor="middle" font-family="Arial" font-size="42" fill="#34495e">لا تتوفر صورة أصلية لهذا الخبر</text><text x="600" y="395" text-anchor="middle" font-family="Arial" font-size="24" fill="#66788a">{safe}</text></svg>'''
        with open(path, "w", encoding="utf-8") as f: f.write(path_text)
    return "./assets/news/" + os.path.basename(path)

items, seen_titles, used_sources = [], set(), set()
for query in QUERIES:
    params = urllib.parse.urlencode({"q": f"{query} when:1d", "hl":"ar", "gl":"IQ", "ceid":"IQ:ar"})
    try:
        raw, _ = fetch("https://news.google.com/rss/search?" + params)
        root = ET.fromstring(raw)
    except Exception as e:
        print("تعذر جلب الأخبار:", e); continue
    for item in root.findall("./channel/item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        published = (item.findtext("pubDate") or "").strip()
        if not title or not link or title in seen_titles: continue
        seen_titles.add(title)
        cat = category(title)
        source = publisher_url(item)
        candidates = rss_candidates(item)
        if source: candidates += page_candidates(source)
        local = ""
        for u in unique_urls(candidates):
            saved = save_image(u)
            if saved:
                local = saved; break
        if not local:
            local = neutral_placeholder(title)
        items.append({"title":title,"url":link,"category":cat,"published":published,"image":local,"source_url":source})

if not items:
    print("لا توجد أخبار جديدة"); raise SystemExit(0)
items.sort(key=lambda x:x.get("published", ""), reverse=True)
with open("news.json", "w", encoding="utf-8") as f:
    json.dump({"updated_at":datetime.now(timezone.utc).isoformat(),"items":items[:30]}, f, ensure_ascii=False, indent=2)
print(f"تم تحديث {min(len(items),30)} خبرا مع صور مصدرية حقيقية أو placeholder محايد")
