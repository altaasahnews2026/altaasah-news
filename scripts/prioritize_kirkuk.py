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


def fresh_sort(x):
    governor = is_governor(x)
    kirkuk = x.get('category') == 'كركوك' or x.get('kirkuk')
    return (0 if x.get('breaking') else 1, 2 if governor else (1 if kirkuk else 0), -dt(x).timestamp())

# Keep the lead free for general Iraq news, while guaranteeing a strong dedicated
# Kirkuk block and giving the governor's latest items priority inside that block.
section_plan = [
    ('محليات', 8),
    ('سياسة', 8),
    ('كركوك', 8),
    ('رياضة', 6),
    ('اقتصاد', 5),
    ('أمن', 5),
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
for x in remaining:
    if len(selected) >= 48:
        break
    selected.append(x)

# Final order: general Iraq stories can lead; Kirkuk is guaranteed substantial coverage.
selected.sort(key=lambda x: (is_governor(x), x.get('category') == 'كركوك', dt(x)), reverse=True)
# Move the first non-Kirkuk Iraqi story to the front so the site does not become a single-topic homepage.
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
print('EDITORIAL SECTIONS:', counts, '— Kirkuk:', sum(x.get('category') == 'كركوك' for x in d['items']), '— Governor:', sum(is_governor(x) for x in d['items']))
