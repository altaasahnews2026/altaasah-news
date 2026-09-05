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


def fetch(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 Chrome/126 Safari/537.36", "Accept": "text/html,application/xhtml+xml,image/*,*/*;q=0.8"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read(), r.headers.get_content_type()


def clean_url(url, base=""):
    if not url:
        return ""
    url = urllib.parse.urljoin(base, html.unescape(str(url)).strip().replace("&amp;", "&"))
    if url.startswith("//"):
        url = "https:" + url
    if url.startswith("http://"):
        url = "https://" + url[7:]
    return url if url.startswith("https://") else ""


def category(title):
    if "كركوك" in title:
        return "كركوك"
    if any(x in title for x in ["اقتصاد", "نفط", "بنزين", "دولار", "تجارة", "زراعة", "أسعار", "الذهب"]):
        return "اقتصاد"
    if any(x in title for x in ["رياضة", "منتخب", "كرة", "الدوري", "آسيا", "بطولة"]):
        return "رياضة"
    if any(x in title for x in ["أمن", "الدفاع", "الجيش", "الحشد", "إرهاب", "مخابرات", "اعتقال"]):
        return "أمن"
    if any(x in title for x in ["سياسة", "وزير", "حكومة", "برلمان", "رئيس", "أمريكا", "إيران", "انتخابات"]):
        return "سياسة"
    return "محلي"


def page_image(url):
    try:
        raw, typ = fetch(url, 12)
        if "html" not in typ:
            return ""
        text = raw[:4000000].decode("utf-8", errors="ignore")
        tags = re.findall(r'<meta\b[^>]*>', text, re.I)
        for tag in tags:
            if re.search(r'(?:property|name)\s*=\s*["\'](?:og:image(?::secure_url)?|twitter:image(?::src)?)["\']', tag, re.I):
                m = re.search(r'content\s*=\s*["\']([^"\']+)', tag, re.I)
                if m:
                    u = clean_url(m.group(1), url)
                    if u:
                        return u
    except Exception as e:
        print("تعذر استخراج صورة الصفحة:", e)
    return ""


def rss_images(item):
    out = []
    for tag in ["content", "thumbnail"]:
        for media in item.findall(f"media:{tag}", NS):
            u = clean_url(media.attrib.get("url", ""))
            if u and u not in out:
                out.append(u)
    for text in [item.findtext("description") or "", item.findtext("content:encoded", namespaces=NS) or ""]:
        m = re.search(r'<img[^>]+(?:src|data-src)\s*=\s*["\']([^"\']+)', text, re.I)
        if m:
            u = clean_url(m.group(1))
            if u and u not in out:
                out.append(u)
    return out


def save_image(url):
    try:
        raw, typ = fetch(url, 15)
        if not raw or len(raw) < 1000 or not typ.startswith("image/"):
            return ""
        ext = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp", "image/gif": ".gif"}.get(typ, ".jpg")
        name = hashlib.sha256(url.encode()).hexdigest()[:20] + ext
        path = os.path.join(NEWS_IMAGE_DIR, name)
        with open(path, "wb") as f:
            f.write(raw)
        return "./assets/news/" + name
    except Exception as e:
        print("تعذر حفظ الصورة:", e)
        return ""


def fallback_image(title, cat):
    key = hashlib.sha256(title.encode("utf-8")).hexdigest()[:16]
    path = os.path.join(NEWS_IMAGE_DIR, key + ".svg")
    if not os.path.exists(path):
        t = html.escape(title[:90]).replace("\n", " ")
        c = html.escape(cat)
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="675"><rect width="1200" height="675" fill="#06192d"/><rect x="0" y="0" width="1200" height="10" fill="#ed1c24"/><text x="600" y="115" fill="#ed1c24" font-family="Arial,Tahoma" font-size="42" font-weight="bold" text-anchor="middle">{c}</text><text x="600" y="205" fill="white" font-family="Arial" font-size="58" font-weight="bold" text-anchor="middle">9NEWS</text><text x="600" y="310" fill="white" font-family="Tahoma,Arial" font-size="30" text-anchor="middle">{t[:55]}</text><text x="600" y="365" fill="white" font-family="Tahoma,Arial" font-size="30" text-anchor="middle">{t[55:]}</text><text x="600" y="610" fill="#b9c7d5" font-family="Tahoma,Arial" font-size="25" text-anchor="middle">التاسعة نيوز — نعلم لتعلم</text></svg>'''
        with open(path, "w", encoding="utf-8") as f:
            f.write(svg)
    return "./assets/news/" + key + ".svg"


items, seen, used_images = [], set(), set()
for query in QUERIES:
    params = urllib.parse.urlencode({"q": f"{query} when:1d", "hl": "ar", "gl": "IQ", "ceid": "IQ:ar"})
    try:
        raw, _ = fetch("https://news.google.com/rss/search?" + params)
        root = ET.fromstring(raw)
    except Exception as e:
        print("تعذر جلب الأخبار:", e)
        continue
    for item in root.findall("./channel/item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        published = (item.findtext("pubDate") or "").strip()
        if not title or not link or title in seen:
            continue
        seen.add(title)
        cat = category(title)
        candidates = []
        p = page_image(link)
        if p:
            candidates.append(p)
        candidates.extend(rss_images(item))
        local = ""
        remote = ""
        for u in candidates:
            if not u or u in used_images:
                continue
            saved = save_image(u)
            if saved:
                local = saved
                used_images.add(u)
                break
            remote = u
            used_images.add(u)
            break
        if not local:
            local = remote or fallback_image(title, cat)
        items.append({"title": title, "url": link, "category": cat, "published": published, "image": local})

if not items:
    print("لا توجد أخبار جديدة")
    raise SystemExit(0)
items.sort(key=lambda x: x.get("published", ""), reverse=True)
with open("news.json", "w", encoding="utf-8") as f:
    json.dump({"updated_at": datetime.now(timezone.utc).isoformat(), "items": items[:30]}, f, ensure_ascii=False, indent=2)
print(f"تم تحديث {min(len(items), 30)} خبرا بصور مستقلة قدر الإمكان")
