import json,re,unicodedata
from datetime import datetime,timezone
from pathlib import Path
from difflib import SequenceMatcher

P=Path('news.json')
D=json.loads(P.read_text(encoding='utf-8'))
items=D.get('items',[])

JUNK=('إعلان','إعلانات','وظائف شاغرة','اضغط هنا','اشترك الآن','نشرة بريدية','رأي القارئ','حظك اليوم')
SPORT=('رياضة','رياضي','كرة','منتخب','مباراة','دوري','اتحاد الكرة','بطولة','لاعب','لاعبة','هدف','أهداف','تصفيات','كأس','ملعب','فوز','خسارة','تعادل','مدرب','فيفا','أولمبي','أولمبياد','آسيا','الدوري العراقي','المحترفين','نادي','أندية','ملاعب','كرة القدم','كرة السلة','كرة الطائرة','مصارعة','ملاكمة','تنس','فورمولا')
POLITICS=('حكومة','حكومي','وزير','وزارة','رئيس الوزراء','برلمان','نائب','نواب','حزب','انتخابات','انتخابية','سياسة','سياسي','رئاسة','رئيس الجمهورية','مجلس الوزراء','جلسة البرلمان','قانون','تشريع','ائتلاف','تحالف','كتلة','سيادي','سيادة','موازنة','قرار حكومي')
LOCAL=('محليات','محلي','بغداد','بلدية','بلديات','خدمات','كهرباء','ماء','مدارس','مدرسة','جامعة','جامعات','صحة','مستشفى','رواتب','تقاعد','طرق','مرور','طقس','دوائر','موظفين','موظفون','تظاهرة','احتجاج','تموين','تعليم','مواطنين','مواطنون')
ECON=('دولار','ذهب','اقتصاد','مصرف','بنك','نفط','استثمار','أسعار','تجارة','بورصة','مالية')
SECURITY=('هجوم','انفجار','شرطة','جيش','أمن','إرهاب','مسيرة','مخدرات','سلاح','اعتقال','مقتل','قتلى','حريق')
INTL=('إيران','سوريا','فلسطين','غزة','إسرائيل','اسرائيل','لبنان','أمريكا','أميركا','تركيا','دولي','دولية','اليمن','السعودية','الإمارات','الكويت','قطر','الأردن','مصر','روسيا','أوكرانيا','الصين')
KIRKUK=('كركوك','التون كوبري','التونكوبري','آلتون كوبري','الدبس','داقوق','الحويجة','ليلان','الرشاد','الرياض','الزاب','قره تبه','جيمن','باي حسن','بابا كركر','محمد سمعان','محمد سمعان آغا','سمعان آغا','محافظ كركوك')
NOISE=('شفق نيوز','السومرية نيوز','شبكة 964','وكالة شفق','عاجل','بالصور','بالفيديو','خاص','متابعة')

def norm(s):
    s=re.sub(r'\s+',' ',str(s or '').strip()).replace('ـ','')
    s=''.join(c for c in unicodedata.normalize('NFKD',s) if not unicodedata.combining(c)).lower()
    return re.sub(r'[^\w\u0600-\u06ff ]',' ',s)

def tokens(s):return set(norm(s).split())
def dt(x):
    try:return datetime.fromisoformat(str(x).replace('Z','+00:00')).astimezone(timezone.utc)
    except:return datetime.min.replace(tzinfo=timezone.utc)
def has(t,words):return any(w in t for w in words)
def title_key(s):
    t=norm(s)
    for w in NOISE:t=t.replace(norm(w),' ')
    return re.sub(r'\s+',' ',t).strip()
def subject_tokens(s):
    stop={'العراق','العراقي','السعودية','السعوديه','كركوك','اليوم','بعد','قبل','على','في','من','عن','مع','الى','إلى','هذا','هذه','وقال','تعلن','يعلن','بيان','بيانات'}
    return {w for w in title_key(s).split() if len(w)>=3 and w not in stop}

def recategorize(x):
    t=str(x.get('title') or '')
    u=str(x.get('url') or x.get('source_url') or '').lower()
    if has(t,KIRKUK):x['category']='كركوك';x['region']='كركوك';x['kirkuk']=True;return
    if '/sport' in u or '/sports' in u or '/رياضة' in u or has(t,SPORT):x['category']='رياضة'
    elif '/politic' in u or '/سياسة' in u or has(t,POLITICS):x['category']='سياسة'
    elif '/local' in u or '/محليات' in u or has(t,LOCAL):x['category']='محليات'
    elif has(t,ECON):x['category']='اقتصاد'
    elif has(t,SECURITY):x['category']='أمن'
    elif has(t,INTL):x['category']='عربي ودولي'
    else:x['category']='سياسة'
    x['region']='العراق' if x.get('category') not in ('عربي ودولي','كركوك') else x['category']

def score(x):
    r=x.get('region');c=x.get('category');s=0
    if x.get('breaking'):s+=80
    if r=='كركوك' or x.get('kirkuk'):s+=60
    elif r=='العراق':s+=35
    else:s+=10
    if c in ('سياسة','أمن','اقتصاد'):s+=12
    if c=='رياضة':s+=15
    if c=='عربي ودولي':s+=12
    age=max(0,(datetime.now(timezone.utc)-dt(x.get('published'))).total_seconds()/3600)
    s-=min(age,30)*1.2
    if has(str(x.get('title') or ''),('محمد سمعان','سمعان آغا','محافظ كركوك')):s+=35
    return s

clean=[]
for x in items:
    t=str(x.get('title') or '').strip()
    if len(t)<18 or any(w in t for w in JUNK):continue
    if not x.get('image') or not x.get('url') or not x.get('published'):continue
    recategorize(x)
    if x.get('category')=='محليات':continue
    clean.append(x)

# إزالة التكرار الحقيقي وشبه المتطابق بين المصادر، مع الاحتفاظ بالأحدث.
clean.sort(key=dt,reverse=True)
dedup=[]
for x in clean:
    k=title_key(x.get('title'))
    xt=subject_tokens(x.get('title'))
    duplicate=False
    for y in dedup:
        yk=title_key(y.get('title'))
        yt=subject_tokens(y.get('title'))
        if k==yk or str(x.get('url'))==str(y.get('url')):
            duplicate=True;break
        if not xt or not yt:continue
        overlap=len(xt & yt)/max(1,min(len(xt),len(yt)))
        similarity=SequenceMatcher(None,k,yk).ratio()
        same_entities=len(xt & yt)>=2
        if similarity>=0.84 or overlap>=0.86 or (same_entities and similarity>=0.72 and overlap>=0.70):
            duplicate=True;break
    if duplicate:continue
    dedup.append(x)

clean=dedup
QUOTAS={'كركوك':10,'سياسة':8,'رياضة':10,'اقتصاد':6,'أمن':6,'عربي ودولي':12}
chosen=[];chosen_keys=set()
for cat,limit in QUOTAS.items():
    pool=[x for x in clean if x.get('category')==cat]
    pool.sort(key=lambda x:(score(x),dt(x)),reverse=True)
    for x in pool:
        k=title_key(x.get('title'))
        if k in chosen_keys:continue
        chosen.append(x);chosen_keys.add(k)
        if sum(1 for y in chosen if y.get('category')==cat)>=limit:break
for x in sorted(clean,key=lambda x:(score(x),dt(x)),reverse=True):
    if len(chosen)>=60:break
    k=title_key(x.get('title'))
    if k not in chosen_keys:chosen.append(x);chosen_keys.add(k)

priority={'كركوك':5,'سياسة':4,'رياضة':4,'أمن':3,'اقتصاد':3,'عربي ودولي':3,'العراق':2}
chosen.sort(key=lambda x:(bool(x.get('breaking')),priority.get(x.get('category'),0),dt(x)),reverse=True)
D['items']=chosen[:60]
D['updated_at']=datetime.now(timezone.utc).isoformat()
P.write_text(json.dumps(D,ensure_ascii=False,indent=2),encoding='utf-8')
print('CLEAN NEWS:',len(D['items']),'items; duplicates removed; Kirkuk',sum(x.get('category')=='كركوك' for x in D['items']))
