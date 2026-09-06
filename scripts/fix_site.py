from pathlib import Path
import re

p = Path('index.html')
s = p.read_text(encoding='utf-8')

# Repair the generated search listener if present.
s = s.replace("input.addEventListener('keydown',e=>{if(e.key==='Enter')doSearch());input.addEventListener('input',()=>{if(!input.value)render(ALL_ITEMS)})", "input.addEventListener('keydown',e=>{if(e.key==='Enter')doSearch()});input.addEventListener('input',()=>{if(!input.value)render(ALL_ITEMS)})")

# Remove accidental repeated search CSS blocks produced by earlier generations.
block = ".search input{border:0;outline:0;background:transparent;width:100%;font:inherit;color:var(--ink);direction:rtl}.search input::placeholder{color:#8b97a6}.search span{font-size:16px;color:var(--navy);margin-right:5px}"
while s.count(block) > 1:
    first = s.find(block)
    s = s[:first] + block + s[first+len(block):].replace(block, '', 1)

# Never replace a real news image with a generic city/emergency image.
start = s.find('const fallbackByCat=')
end = s.find("const esc=", start)
if start >= 0 and end >= 0:
    s = s[:start] + "const emergencyImage='';\n" + s[end:]

# Replace the whole image helper section safely, avoiding fragile regex matching of JS template literals.
marker_a = s.find('function imageFor(x){')
marker_b = s.find('function date(s){', marker_a)
if marker_a >= 0 and marker_b >= 0:
    replacement = "function imageFor(x){const u=clean(x&&x.image);return u&&!/\\.svg(?:\\?|$)/i.test(u)?u:''}\nfunction img(x,cls=''){const src=imageFor(x);return src?`<img class=\"${cls}\" src=\"${esc(src)}\" alt=\"صورة الخبر\" loading=\"lazy\" decoding=\"async\" referrerpolicy=\"no-referrer\">`:`<div class=\"${cls}\" role=\"img\" aria-label=\"صورة الخبر غير متاحة\"></div>`}\n"
    s = s[:marker_a] + replacement + s[marker_b:]

# Remove any legacy fallback handlers.
s = s.replace("hi.src=imageFor(hero);hi.onerror=function(){this.onerror=null;this.src=pickFallback(hero)};", "hi.src=imageFor(hero);")
s = s.replace("document.getElementById('ticker').innerHTML=tickerMarkup(items);", "")
s = re.sub(r"const fallback=pickFallback\(x\);return `<img", "return `<img", s)
s = re.sub(r" referrerpolicy=\\\"no-referrer\\\" onerror=\\\"this\.onerror=null;this\.src='\$\{esc\(fallback\)\}';this\.onerror=function\(\)\{this\.onerror=null;this\.src='\$\{emergencyImage\}'\}\">", " referrerpolicy=\\\"no-referrer\\\">", s)

p.write_text(s, encoding='utf-8')
print('تم إصلاح JavaScript الخاص بصور الأخبار.')