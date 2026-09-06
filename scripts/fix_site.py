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
function rawImageFor(x){
  const candidates=[x&&x.image,x&&x.original_image].filter(Boolean);
  for(const value of candidates){
    const p=String(value).replace(/^\\.\\//,'');
    if(/^assets\\/news\\//i.test(p) && !/\\.svg(?:\\?|$)/i.test(p)) return 'https://raw.githubusercontent.com/altaasahnews2026/altaasah-news/main/'+p;
  }
  return '';
}
function img(x,cls=''){
  const src=imageFor(x);
  const original=originalImageFor(x);
  const raw=rawImageFor(x);
  const first=src||original||raw;
  if(!first) return `<div class="${cls}" role="img" aria-label="صورة الخبر غير متاحة"></div>`;
  const chain=[original,raw].filter(u=>u&&u!==first);
  const fallback=chain.length?` onerror="this.dataset.f=(+this.dataset.f||0)+1;if(this.dataset.f<=${chain.length})this.src='${esc(chain[0])}';if(this.dataset.f>${chain.length})this.onerror=null"`:'';
  return `<img class="${cls}" src="${esc(first)}" alt="صورة الخبر" loading="eager" decoding="async"${fallback}>`;
}
'''
    s = s[:marker_a] + replacement + s[marker_b:]

s = re.sub(r"\.onerror\s*=\s*function\(\)\{[^;]*;[^}]*\};?", "", s)
s = re.sub(r'<script id="news-image-runtime-fix">.*?</script>', '', s, flags=re.S)

hardening = '''<style id="news-image-hardening">
.card .thumb,.catItem,.feature,.lead{background:#dbe4ee;overflow:hidden;}
.card .thumb img,.catItem img,.feature img,.lead img{display:block!important;visibility:visible!important;opacity:1!important;width:100%!important;height:100%!important;object-fit:cover!important;}
</style>'''
s = re.sub(r'<style id="news-image-hardening">.*?</style>', '', s, flags=re.S)
s=s.replace('</head>',hardening+'</head>',1)

p.write_text(s,encoding='utf-8')
print('تم تثبيت نظام صور متعدد المسارات: Pages ثم الأصلية ثم raw.githubusercontent، بدون صورة عامة.')
