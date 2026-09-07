from pathlib import Path
import json
p=Path('news.json')
d=json.loads(p.read_text(encoding='utf-8'))
items=d.get('items',[])
# أخبار كركوك أولاً، وداخل كل مجموعة الأحدث أولاً.
items.sort(key=lambda x: str(x.get('published') or ''), reverse=True)
items.sort(key=lambda x: bool(x.get('kirkuk')), reverse=True)
d['items']=items[:48]
p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
print('تم ترتيب الأخبار: كركوك أولاً ثم الأحدث، العدد:',len(d['items']))
