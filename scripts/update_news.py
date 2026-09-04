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

def fetch(url):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 AltaasahNewsBot/1.0"}
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read()

def category(title):
    t = title.lower()
    if any(x in t for x in ["كركوك"]):
        return "كركوك"
    if any(x in t for x in ["اقتصاد", "نفط", "بنزين", "دولار", "تجارة", "زراعة", "أسعار"]):
        return "اقتصاد"
    if any(x in t for x in ["رياضة", "منتخب", "كرة", "الدوري", "آسيا"]):
        return "رياضة"
    if any(x in t for x in ["أمن", "الدفاع", "الجيش", "الحشد", "إرهاب", "مخابرات", "اعتقال"]):
        return "أمن"
    if any(x in t for x in ["سياسة", "وزير", "حكومة", "برلمان", "رئيس", "أمريكا", "إيران"]):
        return "سياسة"
    return "محلي"

items = []
seen = set()

for q in QUERIES:
    params = urllib.parse.urlencode({
        "q": f"{q} when:1d",
        "hl": "ar",
        "gl": "IQ",
        "ceid": "IQ:ar",
    })
    url = "https://news.google.com/rss/search?" + params
    try:
        root = ET.fromstring(fetch(url))
    except Exception:
        continue

    for item in root.findall("./channel/item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub = (item.findtext("pubDate") or "").strip()
        if not title or not link or title in seen:
            continue
        seen.add(title)
        items.append({
            "title": title,
            "url": link,
            "category": category(title),
            "published": pub,
        })

items = items[:30]

if not items:
    print("لا توجد أخبار جديدة؛ تم الإبقاء على news.json الحالي.")
    raise SystemExit(0)

data = {
    "updated_at": datetime.now(timezone.utc).isoformat(),
    "items": items
}

with open("news.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"تم تحديث {len(items)} خبرا.")
