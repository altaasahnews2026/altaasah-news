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


def is_governor(x):
    t = str(x.get('title') or '')
    return any(k in t for k in ('محمد سمعان', 'سمعان آغا', 'محافظ كركوك'))


def is_iraq_saudi(x):
    t = str(x.get('title') or '')
    keywords = ('السعودية', 'السعودي', 'الرياض', 'العراق يدين', 'أراضينا', 'مسيرات من العراق', 'السعودية والعراق')
    return any(k in t for k in keywords)


def is_kirkuk(x):
    return x.get('category') == 'كركوك' or x.get('kirkuk')


def fresh_sort(x):
    governor = is_governor(x)
    kirkuk = is_kirkuk(x)
    iraq_saudi = is_iraq_saudi(x)
    return (
        0 if x.get('breaking') else 1,
        0 if iraq_saudi else 1,
        1 if governor else (0 if kirkuk else 2),
        -dt(x).timestamp(),
    )

# الصفحة الرئيسية: العراق أولاً، مع أولوية واضحة لكركوك والبيانات/التطورات العراقية-السعودية.
section_plan = [
    ('محليات', 8),
    ('سياسة', 8),
    ('كركوك', 10),
    ('رياضة', 6),
    ('اقتصاد', 5),
    ('أمن', 6),
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

# Ensure the current Iraq-Saudi developments are represented whenever the feed provides them.
iraq_saudi_pool = sorted([x for x in items if is_iraq_saudi(x)], key=fresh_sort)
for x in iraq_saudi_pool[:6]:
    if id(x) not in used:
        selected.append(x)
        used.add(id(x))

remaining = [x for x in items if id(x) not in used]
remaining.sort(key=fresh_sort)
for x in remaining:
    if len(selected) >= 48:
        break
    selected.append(x)

# Final order: current Iraq-Saudi developments first, then fresh Iraqi/Kirkuk coverage.
selected.sort(key=lambda x: (is_iraq_saudi(x), is_governor(x), is_kirkuk(x), dt(x)), reverse=True)

# Keep the lead from becoming single-topic: if no Iraq-Saudi item exists, lead with the freshest non-Kirkuk Iraqi story.
if not any(is_iraq_saudi(x) for x in selected[:3]):
    for i, x in enumerate(selected):
        if x.get('category') not in ('كركوك',):
            selected.insert(0, selected.pop(i))
            break

d['items'] = selected[:48]
p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding='utf-8')

counts = {}
for x in d['items']:
    c = x.get('category', 'غير مصنف')
    counts[c] = counts.get(c, 0) + 1
print('EDITORIAL SECTIONS:', counts,
      '— Kirkuk:', sum(is_kirkuk(x) for x in d['items']),
      '— Iraq-Saudi:', sum(is_iraq_saudi(x) for x in d['items']),
      '— Governor:', sum(is_governor(x) for x in d['items']))
