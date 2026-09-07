from pathlib import Path
import json
p=Path('news.json')
d=json.loads(p.read_text(encoding='utf-8'))
items=d.get('items',[])

def rank(x):
    return {'كركوك':0,'العراق':1,'عربي ودولي':2}.get(x.get('region'),1)

# الترتيب التحريري للموقع: كركوك أولاً، ثم العراق، ثم العربي والدولي.
items.sort(key=lambda x: str(x.get('published') or ''), reverse=True)
items.sort(key=rank)
d['items']=items[:48]
p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
k=sum(1 for x in d['items'] if x.get('region')=='كركوك' or x.get('kirkuk'))
r=sum(1 for x in d['items'] if (x.get('region')=='كركوك' or x.get('kirkuk')) and x.get('report'))
print('تم ترتيب الأخبار: كركوك ثم العراق ثم عربي ودولي — كركوك:',k,'— تقارير كركوك:',r,'— العدد:',len(d['items']))
