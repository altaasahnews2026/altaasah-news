from pathlib import Path
import json
from datetime import datetime, timezone

p = Path('news.json')
d = json.loads(p.read_text(encoding='utf-8'))
items = d.get('items', [])

def dt(x):
    try:
        return datetime.fromisoformat(str(x.get('published', '')).replace('Z', '+00:00')).astimezone(timezone.utc)
    except Exception:
        return datetime.min.replace(tzinfo=timezone.utc)

def fresh_sort(x):
    # الأولوية للخبر العاجل، ثم الأحدث زمنياً، من دون تفضيل محافظة أو موضوع بعينه.
    return (0 if x.get('breaking') else 1, -dt(x).timestamp())

# توزيع متوازن حسب القسم الفعلي للخبر، مع إبقاء كركوك قسماً مستقلاً من دون رفعها إلى واجهة الموقع تلقائياً.
section_plan = [
    ('محليات', 10),
    ('سياسة', 8),
    ('كركوك', 7),
    ('رياضة', 6),
    ('اقتصاد', 6),
    ('أمن', 7),
    ('عربي ودولي', 8),
]

selected = []
used = set()
for category, quota in section_plan:
    pool = [x for x in items if x.get('category') == category and id(x) not in used]
    pool.sort(key=fresh_sort)
    for x in pool[:quota]:
        selected.append(x)
        used.add(id(x))

remaining = [x for x in items if id(x) not in used]
remaining.sort(key=fresh_sort)
selected.extend(remaining)

# الترتيب النهائي للصفحة الرئيسية: الأحدث أولاً، مع تقديم العاجل فقط عند وجوده.
selected.sort(key=fresh_sort)
d['items'] = selected[:60]
p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding='utf-8')

counts = {}
for x in d['items']:
    c = x.get('category', 'غير مصنف')
    counts[c] = counts.get(c, 0) + 1
print('EDITORIAL SECTIONS:', counts,
      '— Kirkuk:', sum(x.get('category') == 'كركوك' or x.get('kirkuk') for x in d['items']))
