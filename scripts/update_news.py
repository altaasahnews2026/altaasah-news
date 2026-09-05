import hashlib
import html
import json
import mimetypes
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


def fetch(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126 Safari/537.36", "Accept": "text/html,application/xhtml+xml,image/avif,image/webp,*/*;q=0.8"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.read(), response.headers.get_content_type()


def category(title):
    if "كركوك" in title: return "كركوك"
    if any(x in title for x in ["اقتصاد", "نفط", "بنزين", "دولار", "تجارة", "زراعة", "أسعار", "الذهب"]): return "اقتصاد"
    if any(x in title for x in ["رياضة", "منتخب", "كرة", "الدوري", "آسيا", "بطولة"]): return "رياضة"
    if any(x in title for x in ["أمن", "الدفاع", "الجيش", "الحشد", "إرهاب", "مخابرات", "اعتقال"]): return "أمن"
    if any(x in title for x in ["سياسة", "وزير", "حكومة", "برلمان", "رئيس", "أمريكا", "إيران", "انتخابات"]): return "سياسة"
    return "محلي"


def clean_url(url, base=""):
    if not url: return ""
    url = urllib.parse.urljoin(base, html.unescape(str(url)).strip().replace("&amp;", "&"))
    if url.startswith("//"): url = "https:" + url
    if url.startswith("http://"): url = "https://" + url[7:]
    return url if url.startswith("https://") else ""


def extract_image(item):
    for tag in ["content", "thumbnail"]:
        for media in item.findall(f"media:{tag}", NS):
            url = clean_url(media.attrib.get("url", ""))
            if url: return url
    for text in [item.findtext("description") or "", item.findtext("content:encoded", namespaces=NS) or ""]:
        match = re.search(r'<img[^>]+(?:src|data-src)\s*=\s*["\']([^"\']+)', text, re.I)
        if match:
            url = clean_url(match.group(1))
            if url: return url
    return ""


def extract_page_image(article_url):
    try:
        raw, content_type = fetch(article_url, 15)
        if not raw or "html" not in content_type: return ""
        text = raw[:3000000].decode("utf-8", errors="ignore")
        for tag in re.findall(r'<meta\b[^>]*>', text, re.I):
            if re.search(r'(?:property|name)\s*=\s*["\'](?:og:image(?::secure_url)?|twitter:image(?::src)?)["\']', tag, re.I):
                m = re.search(r'content\s*=\s*["\']([^"\']+)', tag, re.I)
                if m:
                    url = clean_url(m.group(1), article_url)
                    if url: return url
    except Exception as exc:
        print(f"تعذر استخراج صورة الصفحة: {exc}")
    return ""


def save_image(url):
    url = clean_url(url)
    if not url: return ""
    ext = mimetypes.guess_extension(urllib.parse.urlparse(url).path.split("?")[0]) or ".jpg"
    if ext not in {".jpg", ".jpeg", ".png", ".webp", ".gif"}: ext = ".jpg"
    name = hashlib.sha256(url.encode()).hexdigest()[:20] + ext
    path = os.path.join(NEWS_IMAGE_DIR, name)
    if os.path.exists(path) and os.path.getsize(path) >= 1000: return "./assets/news/" + name
    try:
        data, content_type = fetch(url, 15)
        if not data or len(data) < 1000 or not content_type.startswith("image/"): return ""
        ext = {"image/jpeg":".jpg", "image/png":".png", "image/webp":".webp", "image/gif":".gif"}.get(content_type, ext)
        name = hashlib.sha256(url.encode()).hexdigest()[:20] + ext
        with open(os.path.join(NEWS_IMAGE_DIR, name), "wb") as f: f.write(data)
        return "./assets/news/" + name
    except Exception as exc:
        print(f"تعذر حفظ الصورة: {exc}")
        return ""


def fallback_image(title, cat):
    key = hashlib.sha256(title.encode("utf-8")).hexdigest()[:16]
    path = os.path.join(NEWS_IMAGE_DIR, key + ".svg")
    if not os.path.exists(path):
        t = html.escape(title[:105]); c = html.escape(cat)
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="675"><defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#06192d"/><stop offset="1" stop-color="#1768a5"/></linearGradient></defs><rect width="1200" height="675" fill="url(#g)"/><circle cx="1030" cy="100" r="220" fill="#ed1c24" opacity=".2"/><text x="600" y="125" fill="#ed1c24" font-family="Arial,Tahoma" font-size="42" font-weight="bold" text-anchor="middle">{c}</text><text x="600" y="255" fill="white" font-family="Arial" font-size="62" font-weight="bold" text-anchor="middle">9NEWS</text><foreignObject x="90" y="300" width="1020" height="220"><div xmlns="http://www.w3.org/1999/xhtml" style="font-family:Tahoma,Arial;color:white;font-size:34px;font-weight:bold;text-align:center;line-height:1.6">{t}</div></foreignObject><text x="600" y="620" fill="#c5d5e4" font-family="Tahoma,Arial" font-size="26" text-anchor="middle">التاسعة نيوز — نعلم لتعلم</text></svg>'''
        with open(path, "w", encoding="utf-8") as f: f.write(svg)
    return "./assets/news/" + key + ".svg"

items = []
seen = set()
used_remote_images = set()
for query in QUERIES:
    params = urllib.parse.urlencode({"q": f"{query} when:1d", "hl": "ar", "gl": "IQ", "ceid": "IQ:ar"})
    try:
        raw, _ = fetch("https://news.google.com/rss/search?" + params)
        root = ET.fromstring(raw)
    except Exception as exc:
        print(f"تعذر جلب {query}: {exc}")
        continue
    for item in root.findall("./channel/item"):
        title = (item.findtext("title") or "").strip(); link = (item.findtext("link") or "").strip(); published = (item.findtext("pubDate") or "").strip()
        if not title or not link or title in seen: continue
        seen.add(title); cat = category(title)
        remote = extract_image(item) or extract_page_image(link)
        local = ""
        if remote and remote not in used_remote_images:
            local = save_image(remote)
            if local: used_remote_images.add(remote)
        # إذا تعذر تنزيل الصورة على GitHub Actions، نرسل رابط الصورة الأصلي للمتصفح بدلاً من فقدانها.
        if not local and remote:
            local = remote
        if not local: local = fallback_image(title, cat)
        items.append({"title": title, "url": link, "category": cat, "published": published, "image": local})

if not items:
    print("لا توجد أخبار جديدة؛ لم يتم تغيير news.json.")
    raise SystemExit(0)
items.sort(key=lambda x: x.get("published", ""), reverse=True)
items = items[:30]
with open("news.json", "w", encoding="utf-8") as f:
    json.dump({"updated_at": datetime.now(timezone.utc).isoformat(), "items": items}, f, ensure_ascii=False, indent=2)
print(f"تم تحديث {len(items)} خبرا، ولكل خبر صورة مصدر أو صورة بديلة مختلفة.")
