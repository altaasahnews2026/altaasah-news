from pathlib import Path
import re

p = Path('index.html')
s = p.read_text(encoding='utf-8')

# Repair the generated search listener if present.
s = s.replace("input.addEventListener('keydown',e=>{if(e.key==='Enter')doSearch());input.addEventListener('input',()=>{if(!input.value)render(ALL_ITEMS)})", "input.addEventListener('keydown',e=>{if(e.key==='Enter')doSearch()});input.addEventListener('input',()=>{if(!input.value)render(ALL_ITEMS)})")

# Remove accidental repeated search CSS blocks produced by earlier generations.
block = ".search input{border:0;outline:0;background:transparent;width:100%;font:inherit;color:var(--ink);direction:rtl}.search input::placeholder{color:#8b97a6}.search span{font-size:16px;color:var(--navy);margin-right:5px}"
if s.count(block) > 1:
    first = s.find(block)
    s = s[:first] + block + s[first+len(block):].replace(block, '')

# Never replace a real news image with a generic city/emergency image.
start = s.find('const fallbackByCat=')
end = s.find("const esc=", start)
if start >= 0 and end >= 0:
    s = s[:start] + "const emergencyImage='';\n" + s[end:]

s = re.sub(r"function pickFallback\(x\)\{.*?\}\nfunction imageFor\(x\)\{.*?\}\nfunction img\(x,cls=''\)\{.*?\}", "function imageFor(x){const u=clean(x&&x.image);return u&&!/\\.svg(?:\\?|$)/i.test(u)?u:''}\nfunction img(x,cls=''){const src=imageFor(x);return src?`<img class=\"${cls}\" src=\"${esc(src)}\" alt=\"صورة الخبر\" loading=\"lazy\" decoding=\"async\" referrerpolicy=\"no-referrer\">`:`<div class=\"${cls}\" role=\"img\" aria-label=\"صورة الخبر غير متاحة\"></div>`}", s, flags=re.S)

s = s.replace("hi.src=imageFor(hero);hi.onerror=function(){this.onerror=null;this.src=pickFallback(hero)};", "hi.src=imageFor(hero);")
s = s.replace("document.getElementById('ticker').innerHTML=tickerMarkup(items);", "")
s = s.replace("const fallback=pickFallback(x);return `<img", "return `<img")
s = s.replace(" referrerpolicy=\"no-referrer\" onerror=\"this.onerror=null;this.src='${esc(fallback)}';this.onerror=function(){this.onerror=null;this.src='${emergencyImage}'}\">", " referrerpolicy=\"no-referrer\">")

p.write_text(s, encoding='utf-8')
print('تم تنظيف الواجهة وإلغاء صور السقوط العامة.')