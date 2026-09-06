from pathlib import Path
import re

p = Path('index.html')
s = p.read_text(encoding='utf-8')

s = s.replace(
    "input.addEventListener('keydown',e=>{if(e.key==='Enter')doSearch());input.addEventListener('input',()=>{if(!input.value)render(ALL_ITEMS)})",
    "input.addEventListener('keydown',e=>{if(e.key==='Enter')doSearch()});input.addEventListener('input',()=>{if(!input.value)render(ALL_ITEMS)})"
)

start = s.find('const fallbackByCat=')
end = s.find('const esc=', start)
if start >= 0 and end >= 0:
    s = s[:start] + "const emergencyImage='';\n" + s[end:]

marker_a = s.find('function imageFor(x){')
marker_b = s.find('function date(s){', marker_a)
if marker_a >= 0 and marker_b >= 0:
    replacement = '''function imageFor(x){
  const u=clean(x&&x.image);
  return u && !/\\.svg(?:\\?|$)/i.test(u) ? u : '';
}
function originalImageFor(x){
  const u=clean(x&&x.original_image);
  return u && !/\\.svg(?:\\?|$)/i.test(u) ? u : '';
}
function img(x,cls=''){
  const src=imageFor(x);
  const original=originalImageFor(x);
  if(!src && !original) return `<div class="${cls}" role="img" aria-label="صورة الخبر غير متاحة"></div>`;
  const first=src||original;
  const fallback=(original && original!==first)?` onerror="this.onerror=null;this.src='${esc(original)}'"`:'';
  return `<img class="${cls}" src="${esc(first)}" alt="صورة الخبر" loading="eager" decoding="async"${fallback}>`;
}
'''
    s = s[:marker_a] + replacement + s[marker_b:]

s = re.sub(r"\.onerror\s*=\s*function\(\)\{[^;]*;[^}]*\};?", "", s)
s = s.replace("this.onerror=null;this.src=pickFallback(hero);", "")
s = s.replace("this.onerror=null;this.src=pickFallback(x);", "")
s = re.sub(r'<script id="news-image-runtime-fix">.*?</script>', '', s, flags=re.S)

if 'id="news-image-hardening"' not in s:
    hardening = '''<style id="news-image-hardening">
.card .thumb,.catItem,.feature,.lead{background:#dbe4ee;}
.card .thumb img,.catItem img,.feature img,.lead img{display:block!important;visibility:visible!important;opacity:1!important;}
</style>'''
    s=s.replace('</head>',hardening+'</head>',1)

p.write_text(s,encoding='utf-8')
print('تم إصلاح عرض صور الأخبار جذرياً: القالب أولاً ثم الصورة الأصلية عند تعذر التحميل، بدون صور وهمية.')
