import json,re,unicodedata
from datetime import datetime,timezone
from pathlib import Path
from difflib import SequenceMatcher
P=Path('news.json');D=json.loads(P.read_text(encoding='utf-8'));items=D.get('items',[])
JUNK=('إعلان','إعلانات','وظائف شاغرة','اضغط هنا','اشترك الآن','نشرة بريدية','رأي القارئ','حظك اليوم')
SPORT=('رياضة','رياضي','كرة','منتخب','مباراة','دوري','اتحاد الكرة','بطولة','لاعب','لاعبة','هدف','أهداف','تصفيات','كأس','ملعب','فوز','خسارة','تعادل','مدرب','فيفا','أولمبياد','الدوري العراقي','المحترفين','نادي','أندية','ملاعب','كرة القدم','كرة السلة','كرة الطائرة','مصارعة','ملاكمة','تنس','فورمولا')
POLITICS=('حكومة','حكومي','وزير','وزارة','رئيس الوزراء','برلمان','نائب','نواب','حزب','انتخابات','انتخابية','سياسة','سياسي','رئاسة','رئيس الجمهورية','مجلس الوزراء','جلسة البرلمان','قانون','تشريع','ائتلاف','تحالف','كتلة','سيادي','سيادة','موازنة','قرار حكومي')
LOCAL=('محليات','محلي','بلدية','بلديات','خدمات','كهرباء','ماء','مدارس','مدرسة','جامعة','جامعات','صحة','مستشفى','رواتب','تقاعد','طرق','مرور','طقس','دوائر','موظفين','موظفون','تظاهرة','احتجاج','تموين','تعليم','مواطنين','مواطنون')
ECON=('دولار','ذهب','اقتصاد','مصرف','بنك','نفط','استثمار','أسعار','تجارة','بورصة','مالية','أنابيب النفط','خط أنابيب')
SECURITY=('هجوم','انفجار','شرطة','جيش','أمن','إرهاب','مسيرة','مخدرات','سلاح','اعتقال','مقتل','قتلى','حريق','اغتيال','اشتباك','ضربة')
INTL=('إيران','سوريا','فلسطين','غزة','إسرائيل','اسرائيل','لبنان','أمريكا','أميركا','تركيا','دولي','دولية','اليمن','السعودية','الإمارات','الكويت','قطر','الأردن','مصر','روسيا','أوكرانيا','الصين','البحرين','عمان','المغرب','الجزائر','تونس','السودان','ليبيا')
GOV={'بغداد':('بغداد','الكرخ','الرصافة','أبو غريب','ابو غريب','المدائن','التاجي','المحمودية','الطارمية'),'البصرة':('البصرة','الزبير','أبو الخصيب','ابو الخصيب','الفاو','القرنة','شط العرب','سفوان'),'نينوى':('نينوى','الموصل','تلعفر','سنجار','الحمدانية','بعشيقة','الحضر','القيارة','زمار','ربيعة'),'الأنبار':('الأنبار','الانبار','الرمادي','الفلوجة','حديثة','هيت','القائم','الرطبة','عانة','راوة'),'صلاح الدين':('صلاح الدين','تكريت','سامراء','بيجي','بلد','الدور','الشرقاط','طوزخورماتو','طوز خورماتو'),'ديالى':('ديالى','بعقوبة','المقدادية','الخالص','خانقين','بلدروز','مندلي','جلولاء','قرة تبة'),'واسط':('واسط','الكوت','الحي','الصويرة','النعمانية','بدرة','العزيزية'),'ميسان':('ميسان','العمارة','المجر الكبير','قلعة صالح','الكحلاء','علي الغربي'),'ذي قار':('ذي قار','الناصرية','سوق الشيوخ','الشطرة','الرفاعي','الجبايش'),'المثنى':('المثنى','السماوة','الرميثة','الخضر','الوركاء'),'بابل':('بابل','الحلة','المسيب','المحاويل','الهاشمية','القاسم','الإسكندرية'),'كربلاء':('كربلاء','كربلاء المقدسة','الهندية','عين التمر'),'النجف':('النجف','النجف الأشرف','الكوفة','المناذرة','المشخاب'),'القادسية':('القادسية','الديوانية','الدغارة','الشامية','عفك','الحمزة'),'دهوك':('دهوك','زاخو','العمادية','سميل','عقرة'),'أربيل':('أربيل','اربيل','شقلاوة','سوران','كويسنجق','رواندوز','حرير'),'السليمانية':('السليمانية','حلبجة','رانية','دوكان','كلار','شاربازير'),'كركوك':('كركوك','التون كوبري','التونكوبري','آلتون كوبري','الدبس','داقوق','الحويجة','ليلان','الرشاد','الرياض','الزاب','قره تبه','جيمن','باي حسن','بابا كركر','محمد سمعان','سمعان آغا','محافظ كركوك')}
NOISE=('شفق نيوز','السومرية نيوز','شبكة 964','وكالة شفق','عاجل','بالصور','بالفيديو','خاص','متابعة')
STOP={'العراق','العراقي','العراقية','السعودية','السعوديه','كركوك','اليوم','بعد','قبل','على','في','من','عن','مع','الى','إلى','هذا','هذه','وقال','تعلن','يعلن','بيان','بيانات','مصدر','مصادر','تصريح','تصريحات'}
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
 return {w for w in title_key(s).split() if len(w)>=3 and w not in STOP}
def governorate(t):
 t=norm(t)
 for g,words in GOV.items():
  if any(norm(w) in t for w in words):return g
 return ''
def classify(t,u=''):
 s=norm(t);u=u.lower()
 if any(norm(w) in s for w in SPORT) or '/sports' in u or '/sport/' in u:return 'رياضة'
 if any(norm(w) in s for w in ECON):return 'اقتصاد'
 if any(norm(w) in s for w in SECURITY):return 'أمن'
 if any(norm(w) in s for w in POLITICS) or '/politic' in u:return 'سياسة'
 if any(norm(w) in s for w in INTL):return 'عربي ودولي'
 if any(norm(w) in s for w in LOCAL):return 'محليات'
 return 'محليات'
def recategorize(x):
 t=str(x.get('title') or '');u=str(x.get('url') or x.get('source_url') or '');g=governorate(t)
 x['category']=classify(t,u);x['governorate']=g;x['kirkuk']=g=='كركوك';x['region']=g or ('عربي ودولي' if x['category']=='عربي ودولي' else 'العراق')
def duplicate(a,b):
 ka,kb=title_key(a.get('title')),title_key(b.get('title'))
 if ka==kb or (a.get('url') and str(a.get('url'))==str(b.get('url'))):return True
 ta,tb=subject_tokens(a.get('title')),subject_tokens(b.get('title'))
 if not ta or not tb:return False
 inter=len(ta&tb);overlap=inter/max(1,min(len(ta),len(tb)));jaccard=inter/max(1,len(ta|tb));sim=SequenceMatcher(None,ka,kb).ratio()
 # catch copied headlines and minor rewrites without merging merely related stories
 if sim>=0.82:return True
 if overlap>=0.84 and inter>=3:return True
 if inter>=4 and jaccard>=0.58 and overlap>=0.68 and abs(len(ta)-len(tb))<=4:return True
 return False
clean=[]
for x in items:
 t=str(x.get('title') or '').strip()
 if len(t)<18 or any(w in t for w in JUNK):continue
 if not x.get('image') or not x.get('url') or not x.get('published'):continue
 recategorize(x);clean.append(x)
clean.sort(key=dt,reverse=True)
dedup=[]
for x in clean:
 if not any(duplicate(x,y) for y in dedup):dedup.append(x)
clean=dedup
QUOTAS={'كركوك':12,'محليات':18,'سياسة':8,'رياضة':8,'اقتصاد':7,'أمن':8,'عربي ودولي':12}
chosen=[];used=set()
for cat,limit in QUOTAS.items():
 pool=[x for x in clean if (x.get('governorate')=='كركوك' if cat=='كركوك' else x.get('category')==cat and x.get('governorate')!='كركوك')]
 pool.sort(key=lambda x:(bool(x.get('breaking')),dt(x)),reverse=True)
 for x in pool:
  k=title_key(x.get('title'))
  if k in used:continue
  chosen.append(x);used.add(k)
  if sum(1 for y in chosen if (y.get('governorate')=='كركوك' if cat=='كركوك' else y.get('category')==cat and y.get('governorate')!='كركوك'))>=limit:break
for x in sorted(clean,key=lambda z:(bool(z.get('breaking')),dt(z)),reverse=True):
 if len(chosen)>=100:break
 k=title_key(x.get('title'))
 if k not in used:chosen.append(x);used.add(k)
chosen.sort(key=lambda x:(bool(x.get('breaking')),dt(x)),reverse=True)
D['items']=chosen[:100];D['updated_at']=datetime.now(timezone.utc).isoformat();P.write_text(json.dumps(D,ensure_ascii=False,indent=2),encoding='utf-8')
print('CLEAN NEWS:',len(D['items']),'unique; Kirkuk',sum(x.get('governorate')=='كركوك' for x in D['items']),'local provinces',sum(bool(x.get('governorate')) and x.get('governorate')!='كركوك' for x in D['items']))
