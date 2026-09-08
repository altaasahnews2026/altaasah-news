from pathlib import Path

p = Path('index.html')
s = p.read_text(encoding='utf-8')
old = "async function boot(){try{let r=await fetch(DATA,{cache:'no-store'});if(!r.ok)throw 0;let d=await r.json();ALL=Array.isArray(d.items)?d.items.filter(x=>x&&x.title):[];"
new = "async function fetchNewsData(){const urls=[DATA+'?v='+Date.now(),'https://altaasahnews2026.github.io/altaasah-news/news.json?v='+Date.now(),'https://raw.githubusercontent.com/altaasahnews2026/altaasah-news/main/news.json?v='+Date.now()];let last;for(const u of urls){try{const r=await fetch(u,{cache:'no-store',mode:'cors'});if(!r.ok)throw Error('HTTP '+r.status);const d=await r.json();if(Array.isArray(d.items))return d;}catch(e){last=e}}throw last||Error('news.json')}async function boot(){try{let d=await fetchNewsData();ALL=Array.isArray(d.items)?d.items.filter(x=>x&&x.title):[];"
if old not in s:
    raise SystemExit('news loader pattern not found')
s = s.replace(old, new, 1)
s = s.replace("document.getElementById('hero').innerHTML='<div class=\"empty\">تعذر تحميل الأخبار حالياً.</div>'", "document.getElementById('hero').innerHTML='<div class=\"empty\">تعذر الاتصال بمصدر الأخبار. ستتم إعادة المحاولة تلقائياً.</div>';setTimeout(boot,15000)", 1)
p.write_text(s, encoding='utf-8')
print('تم إصلاح تحميل الأخبار مع 3 مصادر احتياطية وإعادة المحاولة التلقائية')
