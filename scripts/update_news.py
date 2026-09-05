import html
import json
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


def fetch(url):
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "AltaasahNewsBot/2.0"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


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
    url = html.unescape(url).strip()
    url = url.replace("&amp;", "&")
    if url.startswith("//"):
        url = "https:" + url
    if url.startswith("http://"):
        url = "https://" + url[7:]
    if not url.startswith("https://"):
        return ""
    return url


def extract_image(item):
    # 1) Media RSS image/thumbnail when supplied by the publisher.
    for tag in ["content", "thumbnail"]:
        for media in item.findall(f"media:{tag}", NS):
            url = clean_image_url(media.attrib.get("url", ""))
            if url:
                return url

    # 2) Namespaced content:encoded or normal description may contain <img src="...">.
    candidates = [
        item.findtext("description") or "",
        item.findtext("content:encoded", namespaces=NS) or "",
    ]
    for text in candidates:
        match = re.search(r"<img[^>]+src=[\"']([^\"']+)[\"']", text, flags=re.I)
        if match:
            url = clean_image_url(match.group(1))
            if url:
                return url

    return ""


items = []
seen = set()

for query in QUERIES:
    params = urllib.parse.urlencode(
        {
            "q": f"{query} when:1d",
            "hl": "ar",
            "gl": "IQ",
            "ceid": "IQ:ar",
        }
    )
    url = "https://news.google.com/rss/search?" + params
    try:
        root = ET.fromstring(fetch(url))
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
        items.append(
            {
                "title": title,
                "url": link,
                "category": category(title),
                "published": published,
                "image": extract_image(item),
            }
        )

if not items:
    print("لم يتم العثور على أخبار جديدة؛ تم الإبقاء على news.json الحالي.")
    raise SystemExit(0)

items.sort(key=lambda x: x.get("published", ""), reverse=True)
items = items[:30]

data = {
    "updated_at": datetime.now(timezone.utc).isoformat(),
    "items": items,
}

with open("news.json", "w", encoding="utf-8") as file:
    json.dump(data, file, ensure_ascii=False, indent=2)

print(f"تم تحديث {len(items)} خبرا بنجاح.")
