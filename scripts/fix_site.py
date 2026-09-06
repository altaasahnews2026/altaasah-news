from pathlib import Path

p = Path('index.html')
s = p.read_text(encoding='utf-8')

# Repair the generated search listener if present.
s = s.replace("input.addEventListener('keydown',e=>{if(e.key==='Enter')doSearch());input.addEventListener('input',()=>{if(!input.value)render(ALL_ITEMS)})", "input.addEventListener('keydown',e=>{if(e.key==='Enter')doSearch()});input.addEventListener('input',()=>{if(!input.value)render(ALL_ITEMS)})")
p.write_text(s, encoding='utf-8')
print('تم تصحيح JavaScript.')
