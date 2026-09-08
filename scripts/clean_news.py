import json,re,unicodedata
from datetime import datetime,timezone
from pathlib import Path

P=Path('news.json')
D=json.loads(P.read_text(encoding='utf-8'))
items=D.get('items',[])

JUNK=('إعلان','إعلانات','وظائف شاغرة','اضغط هنا','اشترك الآن','نشرة بريدية','رأي القارئ','حظك اليوم')
SPORT=('رياضة','رياضي','كرة','منتخب','مباراة','دوري','اتحاد الكرة','بطولة','لاعب','لاعبة','هدف','أهداف','تصفيات','كأس','ملعب','فوز','خسارة','تعادل','مدرب','فيفا','أولمبي','أولمبياد','آسيا','الدوري العراقي','المحترفين','نادي','أندية','ملاعب')
POLITICS=('حكومة','حكومي','وزير','وزارة','رئيس الوزراء','برلمان','نائب','نواب','حزب','انتخابات','انتخابية','سياسة','سياسي','رئاسة','رئيس الجمهورية','مجلس الوزراء','جلسة البرلمان','قانون','تشريع','ائتلاف','تحالف','كتلة','سيادي','سيادة','موازنة','قرار حكومي')
LOCAL=('محليات','محلي','بغداد','بلدية','بلديات','خدمات','كهرباء','ماء','مدارس','مدرسة','جامعة','جامعات','صحة','مستشفى','رواتب','تقاعد','طرق','مرور','طقس','دوائر','موظفين','موظفون','تظاهرة','احتجاج','تموين','تعليم','مواطنين','مواطنون')
ECON=('دولار','ذهب','اقتصاد','مصرف','بنك','نفط','استثمار','أسعار','تجارة','بورصة','مالية')
SECURITY=('هجوم','انفجار','شرطة','جيش','أمن','إرهاب','مسيرة','مخدرات','سلاح','اعتقال','مقتل','قتلى','حريق')
INTL=('إيران','سوريا','فلسطين','غزة','إسرائيل','اسرائيل','لبنان','أمريكا','أميركا','تركيا','دولي','دولية','اليمن','السعودية','الإمارات','الكويت','قطر','الأردن','مصر','روسيا','أوكرانيا','الصين')
KIRKUK=('كركوك','التون كوبري','التونكوبري','آلتون كوبري','الدبس','داقوق','الحويجة','ليلان','الرشاد','الرياض','الزاب','قره تبه','جيمن','باي حسن','بابا كركر')

def norm(s):
    s=re.sub(r'\s+',' ',str(s or '').strip()).replace('ـ','')
    return ''.join(c for c in unicodedata.normalize('NFKD',s) if not unicodedata.combining(c)).lower()

def dt(x):
    try:return datetime.fromisoformat(str(x).replace('Z','+00:00')).astimezone(timezone.utc)
    except:return datetime.min.replace(tzinfo=timezone.utc)

def has(t,words):return any(w in t for w in words)

def recategorize(x):
    t=str(x.get('title') or '')
    u=str(x.get('url') or x.get('source_url') or '').lower()
    if has(t,KIRKUK):
        x['category']='كركوك';x['region']='كركوك';x['kirkuk']=True;return
    if '/sport' in u or '/sports' in u or '/رياضة' in u or has(t,SPORT):x['category']='رياضة'
    elif '/politic' in u or '/سياسة' in u or has(t,POLITICS):x['category']='سياسة'
    elif '/local' in u or '/محليات' in u or has(t,LOCAL):x['category']='محليات'
    elif has(t,ECON):x['category']='اقتصاد'
    elif has(t,SECURITY):x['category']='أمن'
    elif has(t,INTL):x['category']='عربي ودولي'
    else:x['category']='محليات'
    x['region']='العراق' if x.get('category') not in ('عربي ودولي','كركوك') else x['category']

def score(x):
    title=str(x.get('title') or '')
    r=x.get('region');c=x.get('category');s=0
    if x.get('breaking'):s+=80
    if r=='كركوك' or x.get('kirkuk'):s+=60
    elif r=='العراق':s+=35
    else:s+=10
    if c in ('سياسة','أمن','اقتصاد'):s+=12
    if c=='رياضة':s+=7
    if c=='محليات':s+=8
    age=max(0,(datetime.now(timezone.utc)-dt(x.get('published'))).total_seconds()/3600)
    s-=min(age,30)*1.2
    return s

clean=[];seen=set()
for x in items:
    t=str(x.get('title') or '').strip();key=norm(t)
    if len(t)<18 or key in seen or any(w in t for w in JUNK):continue
    if not x.get('image') or not x.get('url') or not x.get('published'):continue
    recategorize(x)
    seen.add(key);clean.append(x)

clean.sort(key=lambda x:(score(x),dt(x.get('published'))),reverse=True)
# Category quotas keep the front page visibly balanced instead of allowing breaking/international news to consume every slot.
QUOTAS={'كركوك':8,'محليات':6,'سياسة':6,'رياضة':6,'اقتصاد':5,'أمن':5,'عربي ودولي':6}
chosen=[];chosen_keys=set()
for cat,limit in QUOTAS.items():
    for x in clean:
        if x.get('category')==cat and norm(x.get('title')) not in chosen_keys:
            chosen.append(x);chosen_keys.add(norm(x.get('title')))
            if sum(1 for y in chosen if y.get('category')==cat)>=limit:break
for x in clean:
    if len(chosen)>=60:break
    k=norm(x.get('title'))
    if k not in chosen_keys:chosen.append(x);chosen_keys.add(k)
clean=chosen[:60]
# Editorial display order: breaking first, then Kirkuk, then Iraqi/local/political/sports, while retaining freshness.
priority={'كركوك':5,'سياسة':4,'محليات':4,'رياضة':4,'أمن':3,'اقتصاد':3,'العراق':2,'عربي ودولي':1}
clean.sort(key=lambda x:(bool(x.get('breaking')),priority.get(x.get('category'),0),dt(x.get('published'))),reverse=True)
D['items']=clean
D['updated_at']=datetime.now(timezone.utc).isoformat()
P.write_text(json.dumps(D,ensure_ascii=False,indent=2),encoding='utf-8')
print('CLEAN NEWS:',len(clean),'items; categories', {c:sum(1 for x in clean if x.get('category')==c) for c in QUOTAS})
