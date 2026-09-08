import json,re,unicodedata
from datetime import datetime,timezone
from pathlib import Path

P=Path('news.json')
D=json.loads(P.read_text(encoding='utf-8'))
items=D.get('items',[])

JUNK=('إعلان','إعلانات','وظائف شاغرة','اضغط هنا','اشترك الآن','نشرة بريدية','رأي القارئ','حظك اليوم')

def norm(s):
    s=re.sub(r'\s+',' ',str(s or '').strip())
    s=s.replace('ـ','')
    return ''.join(c for c in unicodedata.normalize('NFKD',s) if not unicodedata.combining(c)).lower()

def dt(x):
    try:return datetime.fromisoformat(str(x).replace('Z','+00:00')).astimezone(timezone.utc)
    except:return datetime.min.replace(tzinfo=timezone.utc)

def score(x):
    title=str(x.get('title') or '')
    r=x.get('region')
    c=x.get('category')
    s=0
    if x.get('breaking'):s+=80
    if r=='كركوك' or x.get('kirkuk'):s+=60
    elif r=='العراق':s+=35
    else:s+=10
    if c in ('سياسة','أمن','اقتصاد'):s+=12
    if c=='رياضة':s+=5
    age=max(0,(datetime.now(timezone.utc)-dt(x.get('published'))).total_seconds()/3600)
    s-=min(age,30)*1.2
    return s

clean=[];seen=set()
for x in items:
    t=str(x.get('title') or '').strip()
    key=norm(t)
    if len(t)<18 or key in seen or any(w in t for w in JUNK):continue
    if not x.get('image') or not x.get('url') or not x.get('published'):continue
    seen.add(key);clean.append(x)

clean.sort(key=lambda x:(score(x),dt(x.get('published'))),reverse=True)
# Keep a balanced front page: freshest 60, while preserving at least a few Kirkuk stories when available.
k=[x for x in clean if x.get('region')=='كركوك' or x.get('kirkuk')]
if k:
    chosen=[];chosen_keys=set()
    for x in k[:8]:chosen.append(x);chosen_keys.add(norm(x.get('title')))
    for x in clean:
        if len(chosen)>=60:break
        if norm(x.get('title')) not in chosen_keys:
            chosen.append(x);chosen_keys.add(norm(x.get('title')))
    clean=chosen
clean=clean[:60]
# Final display order: newest within editorial priority, with breaking first and Kirkuk prominently represented.
clean.sort(key=lambda x:(bool(x.get('breaking')), x.get('region')=='كركوك', x.get('region')=='العراق', dt(x.get('published'))),reverse=True)
D['items']=clean
D['updated_at']=datetime.now(timezone.utc).isoformat()
P.write_text(json.dumps(D,ensure_ascii=False,indent=2),encoding='utf-8')
print('CLEAN NEWS:',len(clean),'items; Kirkuk',sum(1 for x in clean if x.get('region')=='كركوك' or x.get('kirkuk')))
