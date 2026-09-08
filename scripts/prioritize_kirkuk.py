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
    return (0 if x.get('breaking') else 1, -dt(x).timestamp())


# Editorial homepage order: local/Kirkuk first, then Iraqi politics and sports,
# followed by security/economy and Arab/international coverage.
section_plan = [
    ('كركوك', 8),
    ('محليات', 8),
    ('سياسة', 8),
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

# Fill any remaining slots by freshness without allowing one section to dominate.
remaining = [x for x in items if id(x) not in used]
remaining.sort(key=fresh_sort)
for x in remaining:
    if len(selected) >= 48:
        break
    selected.append(x)

# Final stable editorial order keeps the requested sections visible in the homepage dataset.
d['items'] = selected[:48]
p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding='utf-8')

counts = {}
for x in d['items']:
    c = x.get('category', 'غير مصنف')
    counts[c] = counts.get(c, 0) + 1
print('EDITORIAL SECTIONS:', counts, '— total:', len(d['items']))
