import json,re,unicodedata
from datetime import datetime,timezone
from pathlib import Path
from difflib import SequenceMatcher
P=Path('news.json');D=json.loads(P.read_text(encoding='utf-8'));items=D.get('items',[])
JUNK=('إعلان','إعلانات','وظائف شاغرة','اضغط هنا','اشترك الآن','نشرة بريدية','رأي القارئ','حظك اليوم')
SPORT=('رياضة','رياضي','كرة','منتخب','مباراة','دوري','اتحاد الكرة','بطولة','لاعب','لاعبة','هدف','أهداف','تصفيات','كأس','ملعب','فوز','خسارة','تعادل','مدرب','فيفا','أولمبي','أولمبياد','آسيا','الدوري العراقي','المحترفين','نادي','أندية','ملاعب','كرة القدم','كرة السلة','كرة الطائرة','مصارعة','ملاكمة','تنس','فورمولا')
POLITICS=('حكومة','حكومي','وزير','وزارة','رئيس الوزراء','برلمان','نائب','نواب','حزب','انتخابات','انتخابية','سياسة','سياسي','رئاسة','رئيس الجمهورية','مجلس الوزراء','جلسة البرلمان','قانون','تشريع','ائتلاف','تحالف','كتلة','سيادي','سيادة','موازنة','قرار حكومي')
LOCAL=('محليات','محلي','بغداد','بلدية','بلديات','خدمات','كهرباء','ماء','مدارس','مدرسة','جامعة','جامعات','صحة','مستشفى','رواتب','تقاعد','طرق','مرور','طقس','دوائر','موظفين','موظفون','تظاهرة','احتجاج','تموين','تعليم','مواطنين','مواطنون')
ECON=('دولار','ذهب','اقتصاد','مصرف','بنك','نفط','استثمار','أسعار','تجارة','بورصة','مالية')
SECURITY=('هجوم','انفجار','شرطة','جيش','أمن','إرهاب','مسيرة','مخدرات','سلاح','اعتقال','مقتل','قتلى','حريق')
INTL=('إيران','سوريا','فلسطين','غزة','إسرائيل','اسرائيل','لبنان','أمريكا','أميركا','تركيا','دولي','دولية','اليمن','السعودية','الإمارات','الكويت','قطر','الأردن','مصر','روسيا','أوكرانيا','الصين')
GOV={
'بغداد':('بغداد','الكرخ','الرصافة','أبو غريب','ابو غريب','المدائن','التاجي','المحمودية','الطارمية'),'البصرة':('البصرة','الزبير','أبو الخصيب','ابو الخصيب','الفاو','القرنة','شط العرب','سفوان'),'نينوى':('نينوى','الموصل','تلعفر','سنجار','الحمدانية','بعشيقة','الحضر','القيارة','زمار','ربيعة'),'الأنبار':('الأنبار','الانبار','الرمادي','الفلوجة','حديثة','هيت','القائم','الرطبة','عانة','راوة'),'صلاح الدين':('صلاح الدين','تكريت','سامراء','بيجي','بلد','الدور','الشرقاط','طوزخورماتو','طوز خورماتو'),'ديالى':('ديالى','بعقوبة','المقدادية','الخالص','خانقين','بلدروز','مندلي','جلولاء','قرة تبة'),'واسط':('واسط','الكوت','الحي','الصويرة','النعمانية','بدرة','العزيزية'),'ميسان':('ميسان','العمارة','المجر الكبير','قلعة صالح','الكحلاء','علي الغربي'),'ذي قار':('ذي قار','الناصرية','سوق الشيوخ','الشطرة','الرفاعي','الجبايش'),'المثنى':('المثنى','السماوة','الرميثة','الخضر','الوركاء'),'بابل':('بابل','الحلة','المسيب','المحاويل','الهاشمية','القاسم','الإسكندرية'),'كربلاء':('كربلاء','كربلاء المقدسة','الهندية','عين التمر'),'النجف':('النجف','النجف الأشرف','الكوفة','المناذرة','المشخاب'),'القادسية':('القادسية','الديوانية','الدغارة','الشامية','عفك','الحمزة'),'دهوك':('دهوك','زاخو','العمادية','سميل','عقرة'),'أربيل':('أربيل','اربيل','شقلاوة','سوران','كويسنجق','رواندوز','حرير'),'السليمانية':('السليمانية','حلبجة','رانية','دوكان','كلار','شاربازير'),'كركوك':('كركوك','التون كوبري','التونكوبري','آلتون كوبري','الدبس','داقوق','الحويجة','ليلان','الرشاد','الرياض','الزاب','قره تبه','جيمن','باي حسن','بابا كركر','محمد سمعان','محمد سمعان آغا','سمعان آغا','محافظ كركوك')}
NOISE=('شفق نيوز','السومرية نيوز','شبكة 964','وكالة شفق','عاجل','بالصور','بالفيديو','خاص','متابعة')
def norm(s):
 s=re.sub(r'\s+',' ',str(s or '').strip()).replace('ـ','');s=''.join(c for c in unicodedata.normalize('NFKD',s) if not unicodedata.combining(c)).lower();return re.sub(r'[^\w\u0600-\u06ff ]',' ',s)
def dt(x):
 try:return datetime.fromisoformat(str(x).replace('Z','+00:00')).astimezone(timezone.utc)
 except:return datetime.min.replace(tzinfo=timezone.utc)
def title_key(s):
 t=norm(s)
 for w in NOISE:t=t.replace(norm(w),' ')
 return re.sub(r'\s+',' ',t).strip()
def subject_tokens(s):
 stop={'العراق','العراقي','السعودية','السعوديه','كركوك','اليوم','بعد','قبل','على','في','من','عن','مع','الى','إلى','هذا','هذه','وقال','تعلن','يعلن','بيان','بيانات'}
 return {w for w in title_key(s).split() if len(w)>=3 and w not in stop}
def governorate(t):
 for g,words in GOV.items():
  if any(w in t for w in words):return g
 return ''
def recategorize(x):
 t=str(x.get('title') or '');g=governorate(t)
 if g:
  x['governorate']=g;x['region']=g;x['category']='كركوك' if g=='كركوك' else 'المحافظات';x['kirkuk']=g=='كركوك';return
 u=str(x.get('url') or x.get('source_url') or '').lower()
 if '/sport' in u or '/sports' in u or '/رياضة' in u or any(w in t for w in SPORT):x['category']='رياضة'
 elif '/politic' in u or '/سياسة' in u or any(w in t for w in POLITICS):x['category']='سياسة'
 elif any(w in t for w in ECON):x['category']='اقتصاد'
 elif any(w in t for w in SECURITY):x['category']='أمن'
 elif any(w in t for w in INTL):x['category']='عربي ودولي'
 elif any(w in t for w in LOCAL):x['category']='محليات'
 else:x['category']='سياسة'
 x['region']='العراق';x['governorate']=''
def score(x):
 s=100 if x.get('breaking') else 0
 c=x.get('category')
 s+=12 if c=='سياسة' else 11 if c in ('أمن','اقتصاد') else 10 if c=='رياضة' else 8
 age=max(0,(datetime.now(timezone.utc)-dt(x.get('published'))).total_seconds()/3600)
 return s-min(age,30)*1.5
clean=[]
for x in items:
 t=str(x.get('title') or '').strip()
 if len(t)<18 or any(w in t for w in JUNK):continue
 if not x.get('image') or not x.get('url') or not x.get('published'):continue
 recategorize(x);clean.append(x)
clean.sort(key=dt,reverse=True);dedup=[]
for x in clean:
 k=title_key(x.get('title'));xt=subject_tokens(x.get('title'));dup=False
 for y in dedup:
  yk=title_key(y.get('title'));yt=subject_tokens(y.get('title'))
  if k==yk or str(x.get('url'))==str(y.get('url')):dup=True;break
  if xt and yt:
   overlap=len(xt&yt)/max(1,min(len(xt),len(yt)));sim=SequenceMatcher(None,k,yk).ratio()
   if sim>=0.84 or overlap>=0.86 or (len(xt&yt)>=2 and sim>=0.72 and overlap>=0.70):dup=True;break
 if not dup:dedup.append(x)
clean=dedup
QUOTAS={'كركوك':10,'المحافظات':18,'سياسة':8,'رياضة':10,'اقتصاد':6,'أمن':6,'عربي ودولي':12}
chosen=[];keys=set()
for cat,limit in QUOTAS.items():
 pool=sorted([x for x in clean if x.get('category')==cat],key=lambda x:(score(x),dt(x)),reverse=True)
 for x in pool:
  k=title_key(x.get('title'))
  if k in keys:continue
  chosen.append(x);keys.add(k)
  if sum(y.get('category')==cat for y in chosen)>=limit:break
for x in sorted(clean,key=lambda x:(score(x),dt(x)),reverse=True):
 if len(chosen)>=100:break
 k=title_key(x.get('title'))
 if k not in keys:chosen.append(x);keys.add(k)
# الترتيب النهائي مهني: عاجل أولاً، ثم الأحدث والأكثر أهمية؛ لا توجد أولوية للمحافظات.
chosen.sort(key=lambda x:(bool(x.get('breaking')),score(x),dt(x)),reverse=True)
D['items']=chosen[:100];D['updated_at']=datetime.now(timezone.utc).isoformat();P.write_text(json.dumps(D,ensure_ascii=False,indent=2),encoding='utf-8')
print('CLEAN NEWS:',len(D['items']),'items; provinces',sum(x.get('category')=='المحافظات' for x in D['items']),'Kirkuk',sum(x.get('category')=='كركوك' for x in D['items']))
