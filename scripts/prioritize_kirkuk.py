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
    # الخبر العاجل أولاً، ثم الأحدث. لا نرفع خبراً لمجرد المحافظة أو المنطقة.
    return (bool(x.get('breaking')), dt(x))

# توزيع تحريري متوازن. كركوك تُعامل كموقع جغرافي مستقل وليس كتصنيف موضوعي.
section_plan = [
    ('محليات', 12),
    ('كركوك', 10),
    ('سياسة', 8),
    ('رياضة', 7),
    ('اقتصاد', 7),
    ('أمن', 8),
    ('عربي ودولي', 10),
]

selected = []
used = set()

def key(x):
    return str(x.get('url') or x.get('title') or id(x))

for section, quota in section_plan:
    if section == 'كركوك':
        pool = [x for x in items if x.get('governorate') == 'كركوك' or x.get('kirkuk')]
    else:
        pool = [x for x in items if x.get('category') == section and x.get('governorate') != 'كركوك']
    pool.sort(key=fresh_sort, reverse=True)
    for x in pool:
        k = key(x)
        if k in used:
            continue
        selected.append(x)
        used.add(k)
        if len([y for y in selected if (y.get('governorate') == 'كركوك' or y.get('kirkuk'))] if section == 'كركوك' else [y for y in selected if y.get('category') == section and y.get('governorate') != 'كركوك']) >= quota:
            break

remaining = [x for x in items if key(x) not in used]
remaining.sort(key=fresh_sort, reverse=True)
selected.extend(remaining)

# الصفحة الرئيسية تبدأ دائماً بالأهم زمنياً: عاجل ثم الأحدث، من دون فرض كركوك أو أي محافظة على الخبر الرئيسي.
selected.sort(key=fresh_sort, reverse=True)
d['items'] = selected[:60]
p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding='utf-8')

counts = {}
for x in d['items']:
    c = x.get('category', 'غير مصنف')
    counts[c] = counts.get(c, 0) + 1
print('EDITORIAL SECTIONS:', counts,
      '— Kirkuk:', sum(1 for x in d['items'] if x.get('governorate') == 'كركوك' or x.get('kirkuk')),
      '— Provinces:', sum(1 for x in d['items'] if x.get('governorate') and x.get('governorate') != 'كركوك'))
