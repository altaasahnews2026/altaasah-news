from pathlib import Path
import re

p = Path('index.html')
s = p.read_text(encoding='utf-8')

# Fix the search listener if an old malformed version exists.
s = s.replace(
    "input.addEventListener('keydown',e=>{if(e.key==='Enter')doSearch());input.addEventListener('input',()=>{if(!input.value)render(ALL_ITEMS)})",
    "input.addEventListener('keydown',e=>{if(e.key==='Enter')doSearch()});input.addEventListener('input',()=>{if(!input.value)render(ALL_ITEMS)})"
)

# Never use a generic/emergency image as a news image.
start = s.find('const fallbackByCat=')
end = s.find('const esc=', start)
if start >= 0 and end >= 0:
    s = s[:start] + "const emergencyImage='';\n" + s[end:]

# Replace the complete image helper block. Every card gets the generated
# template image first; if that file ever fails to load, the locally stored
# original source image is used instead of hiding the image or showing a fake.
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

# Remove all legacy handlers that could hide or replace the real news image.
s = re.sub(r"\\.onerror\\s*=\\s*function\\(\\)\\{[^;]*;[^}]*\\};?", "", s)
s = s.replace("this.onerror=null;this.src=pickFallback(hero);", "")
s = s.replace("this.onerror=null;this.src=pickFallback(x);", "")

# Remove the old runtime listener that hid broken images. The image element
# now handles its own fallback to original_image.
s = re.sub(r'<script id="news-image-runtime-fix">.*?</script>', '', s, flags=re.S)

# Force news thumbnails to remain visible and reserve their layout space.
if 'id="news-image-hardening"' not in s:
    hardening = '''<style id="news-image-hardening">
.card .thumb,.catItem,.feature,.lead{background:#dbe4ee;}
.card .thumb img,.catItem img,.feature img,.lead img{display:block!important;visibility:visible!important;opacity:1!important;}
</style>'''
    s=s.replace('</head>',hardening+'</head>',1)

p.write_text(s,encoding='utf-8')
print('تم إصلاح عرض صور الأخبار جذرياً: القالب أولاً ثم الصورة الأصلية عند تعذر التحميل، بدون صور وهمية.')
