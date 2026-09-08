from pathlib import Path
import json,re
from datetime import datetime,timezone
p=Path('news.json')
d=json.loads(p.read_text(encoding='utf-8'))
items=d.get('items',[])

def dt(x):
    try:return datetime.fromisoformat(str(x.get('published','')).replace('Z','+00:00')).astimezone(timezone.utc)
    except:return datetime.min.replace(tzinfo=timezone.utc)

def rank(x):
    r=x.get('region')
    base={'كركوك':0,'العراق':1,'عربي ودولي':2}.get(r,1)
    # Breaking news outranks ordinary items, while Kirkuk remains the lead regional priority.
    return (0 if x.get('breaking') else 1, base, -dt(x).timestamp())

items.sort(key=rank)
d['items']=items[:48]
p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
k=sum(1 for x in d['items'] if x.get('region')=='كركوك' or x.get('kirkuk'))
b=sum(1 for x in d['items'] if x.get('breaking'))
print('EDITORIAL ORDER: breaking, Kirkuk, Iraq, Arab/International — Kirkuk:',k,'— breaking:',b,'— total:',len(d['items']))
