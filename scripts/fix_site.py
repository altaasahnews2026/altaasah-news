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

# Replace the complete image helper block. This also removes the malformed
# duplicate fragment that previously appeared after img().
marker_a = s.find('function imageFor(x){')
marker_b = s.find('function date(s){', marker_a)
if marker_a >= 0 and marker_b >= 0:
    replacement = '''function imageFor(x){
  const u=clean(x&&x.image);
  return u && !/\\.svg(?:\\?|$)/i.test(u) ? u : '';
}
function img(x,cls=''){
  const src=imageFor(x);
  if(!src) return `<div class="${cls}" role="img" aria-label="صورة الخبر غير متاحة"></div>`;
  return `<img class="${cls}" src="${esc(src)}" alt="صورة الخبر" loading="lazy" decoding="async">`;
}
'''
    s = s[:marker_a] + replacement + s[marker_b:]

# Remove legacy image fallback/onerror code so a broken image is not replaced
# by a template/emergency picture.
s = re.sub(r"\.onerror\s*=\s*function\(\)\{[^;]*;[^}]*\};?", "", s)
s = s.replace("this.onerror=null;this.src=pickFallback(hero);", "")
s = s.replace("this.onerror=null;this.src=pickFallback(x);", "")

# Add a small runtime repair: if a local image fails, leave the card intact
# rather than inserting a generic image.
if 'id="news-image-runtime-fix"' not in s:
    runtime = '''<script id="news-image-runtime-fix">
document.addEventListener('error',function(e){
  const im=e.target;
  if(im && im.tagName==='IMG' && im.closest('.card,.lead,.feature,.catItem')){
    im.removeAttribute('src');
    im.style.display='none';
  }
},true);
</script>'''
    s=s.replace('</body>',runtime+'</body>')

p.write_text(s,encoding='utf-8')
print('تم إصلاح JavaScript الخاص بصور الأخبار وإزالة أي fallback عام.')
