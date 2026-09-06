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
    replacement = '''function rawizeImage(u){
  u=clean(u);
  if(!u || /\\.svg(?:\\?|$)/i.test(u)) return '';
  const base='https://altaasahnews2026.github.io/altaasah-news/';
  const raw='https://raw.githubusercontent.com/altaasahnews2026/altaasah-news/main/';
  if(u.startsWith(base+'assets/news/')) return raw+u.slice((base).length);
  if(/^assets\\/news\\//i.test(u.replace(/^\\.\\//,''))) return raw+u.replace(/^\\.\\//,'');
  return u;
}
function imageFor(x){ return rawizeImage(x&&x.image); }
function originalImageFor(x){ return rawizeImage(x&&x.original_image); }
function rawImageFor(x){
  const candidates=[x&&x.image,x&&x.original_image].filter(Boolean);
  for(const value of candidates){
    const u=rawizeImage(value);
    if(u && u.includes('/assets/news/')) return u;
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

s = re.sub(r"\\.onerror\\s*=\\s*function\\(\\)\\{[^;]*;[^}]*\\};?", "", s)
s = re.sub(r'<script id="news-image-runtime-fix">.*?</script>', '', s, flags=re.S)

hardening = '''<style id="news-image-hardening">
.card .thumb,.catItem,.feature,.lead{background:#dbe4ee;overflow:hidden;}
.card .thumb img,.catItem img,.feature img,.lead img{display:block!important;visibility:visible!important;opacity:1!important;width:100%!important;height:100%!important;object-fit:cover!important;}
</style>'''
s = re.sub(r'<style id="news-image-hardening">.*?</style>', '', s, flags=re.S)
s=s.replace('</head>',hardening+'</head>',1)

p.write_text(s,encoding='utf-8')
print('تم تثبيت الصور على raw.githubusercontent مباشرة مع بدائل لنفس الصورة، بدون صورة عامة.')
