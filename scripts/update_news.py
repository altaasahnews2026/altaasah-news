import json
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


def fetch(url):
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "AltaasahNewsBot/1.0"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def category(title):
    if "كركوك" in title:
        return "كركوك"
    if any(x in title for x in ["اقتصاد", "نفط", "بنزين", "دولار", "تجارة", "زراعة", "أسعار"]):
        return "اقتصاد"
    if any(x in title for x in ["رياضة", "منتخب", "كرة", "الدوري", "آسيا"]):
        return "رياضة"
    if any(x in title for x in ["أمن", "الدفاع", "الجيش", "الحشد", "إرهاب", "مخابرات", "اعتقال"]):
        return "أمن"
    if any(x in title for x in ["سياسة", "وزير", "حكومة", "برلمان", "رئيس", "أمريكا", "إيران"]):
        return "سياسة"
    return "محلي"


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
            }
        )

if not items:
    print("لم يتم العثور على أخبار جديدة؛ تم الإبقاء على news.json الحالي.")
    raise SystemExit(0)

# الأحدث أولاً عندما تكون تواريخ النشر قابلة للتحليل.
items.sort(key=lambda x: x.get("published", ""), reverse=True)
items = items[:30]

data = {
    "updated_at": datetime.now(timezone.utc).isoformat(),
    "items": items,
}

with open("news.json", "w", encoding="utf-8") as file:
    json.dump(data, file, ensure_ascii=False, indent=2)

print(f"تم تحديث {len(items)} خبرا بنجاح.")
