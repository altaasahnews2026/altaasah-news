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

QUERIES = [
    "العراق",
    "العراق سياسة أمن اقتصاد",
    "كركوك",
    "العراق رياضة",
]

NS = {
    "media": "http://search.yahoo.com/mrss/",
    "content": "http://purl.org/rss/1.0/modules/content/",
}
NEWS_IMAGE_DIR = "assets/news"
os.makedirs(NEWS_IMAGE_DIR, exist_ok=True)


def fetch(url, timeout=30):
    request = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,image/avif,image/webp,image/apng,*/*;q=0.8",
    })
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read(), response.headers.get_content_type()


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


def clean_image_url(url):
    if not url:
        return ""
    url = html.unescape(url).strip().replace("&amp;", "&")
    if url.startswith("//"):
        url = "https:" + url
    if url.startswith("http://"):
        url = "https://" + url[7:]
    return url if url.startswith("https://") else ""


def extract_image(item):
    for tag in ["content", "thumbnail"]:
        for media in item.findall(f"media:{tag}", NS):
            url = clean_image_url(media.attrib.get("url", ""))
            if url:
                return url
    candidates = [item.findtext("description") or "", item.findtext("content:encoded", namespaces=NS) or ""]
    for text in candidates:
        match = re.search(r"<img[^>]+src=[\"']([^\"']+)[\"']", text, flags=re.I)
        if match:
            url = clean_image_url(match.group(1))
            if url:
                return url
    return ""


def extract_page_image(article_url):
    """Get og:image/twitter:image from the real article page when RSS has no media image."""
    try:
        raw, content_type = fetch(article_url, timeout=12)
        if not raw or "html" not in content_type:
            return ""
        text = raw[:2_000_000].decode("utf-8", errors="ignore")
        patterns = [
            r'<meta[^>]+property=["\']og:image(?::secure_url)?["\'][^>]+content=["\']([^"\']+)["\']',
            r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image(?::secure_url)?["\']',
            r'<meta[^>]+name=["\']twitter:image(?::src)?["\'][^>]+content=["\']([^"\']+)["\']',
            r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']twitter:image(?::src)?["\']',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.I)
            if match:
                value = html.unescape(match.group(1)).strip()
                value = urllib.parse.urljoin(article_url, value)
                value = clean_image_url(value)
                if value:
                    return value
    except Exception as exc:
        print(f"تعذر استخراج صورة الصفحة: {exc}")
    return ""


def save_image(url):
    url = clean_image_url(url)
    if not url:
        return ""
    ext = ".jpg"
    guessed = mimetypes.guess_extension(urllib.parse.urlparse(url).path.split("?")[0])
    if guessed in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
        ext = guessed
    name = hashlib.sha256(url.encode("utf-8")).hexdigest()[:20] + ext
    path = os.path.join(NEWS_IMAGE_DIR, name)
    if not os.path.exists(path) or os.path.getsize(path) < 1000:
        try:
            data, content_type = fetch(url, timeout=15)
            if not data or len(data) < 1000:
                return ""
            if content_type == "image/png":
                ext = ".png"
            elif content_type == "image/webp":
                ext = ".webp"
            elif content_type == "image/gif":
                ext = ".gif"
            elif content_type in {"image/jpeg", "image/jpg"}:
                ext = ".jpg"
            name = hashlib.sha256(url.encode("utf-8")).hexdigest()[:20] + ext
            path = os.path.join(NEWS_IMAGE_DIR, name)
            with open(path, "wb") as file:
                file.write(data)
        except Exception as exc:
            print(f"تعذر حفظ الصورة: {exc}")
            return ""
    return "./assets/news/" + name


items = []
seen = set()
for query in QUERIES:
    params = urllib.parse.urlencode({"q": f"{query} when:1d", "hl": "ar", "gl": "IQ", "ceid": "IQ:ar"})
    url = "https://news.google.com/rss/search?" + params
    try:
        raw, _ = fetch(url)
        root = ET.fromstring(raw)
    except Exception as exc:
        print(f"تعذر جلب المصدر للبحث {query}: {exc}")
        continue
    for item in root.findall("./channel/item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        published = (item.findtext("pubDate") or "").strip()
        if not title or not link or title in seen:
            continue
        seen.add(title)
        remote_image = extract_image(item)
        if not remote_image:
            remote_image = extract_page_image(link)
        local_image = save_image(remote_image)
        items.append({
            "title": title,
            "url": link,
            "category": category(title),
            "published": published,
            "image": local_image,
        })

if not items:
    print("لم يتم العثور على أخبار جديدة؛ تم الإبقاء على news.json الحالي.")
    raise SystemExit(0)

items.sort(key=lambda x: x.get("published", ""), reverse=True)
items = items[:30]
data = {"updated_at": datetime.now(timezone.utc).isoformat(), "items": items}
with open("news.json", "w", encoding="utf-8") as file:
    json.dump(data, file, ensure_ascii=False, indent=2)
print(f"تم تحديث {len(items)} خبرا بنجاح.")
