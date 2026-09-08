from pathlib import Path
import json
import re

p = Path('index.html')
s = p.read_text(encoding='utf-8')

# Build a zero-network fallback directly into the generated homepage.
# The page can therefore display the latest generated news even when a browser,
# extension, DNS filter, or transient GitHub Pages request blocks news.json.
news_path = Path('news.json')
if news_path.exists():
    try:
        data = json.loads(news_path.read_text(encoding='utf-8'))
        items = [x for x in data.get('items', []) if isinstance(x, dict) and x.get('title')]
        payload = json.dumps({'items': items}, ensure_ascii=False, separators=(',', ':'))
        embedded = '<script id="embedded-news-fallback">window.__NEWS_FALLBACK__=' + payload.replace('</script>', '<\\/script>') + ';</script>'
        s = re.sub(r'<script id="embedded-news-fallback">.*?</script>', '', s, flags=re.S)
        s = s.replace('</head>', embedded + '</head>', 1)
    except Exception as exc:
        print('embedded fallback skipped:', exc)

# Use the same-origin generated file first. Do not make the homepage depend on
# cross-origin raw GitHub requests; the embedded data is the final fallback.
old = "async function fetchNewsData(){const urls=[DATA+'?v='+Date.now(),'https://altaasahnews2026.github.io/altaasah-news/news.json?v='+Date.now(),'https://raw.githubusercontent.com/altaasahnews2026/altaasah-news/main/news.json?v='+Date.now()];let last;for(const u of urls){try{const r=await fetch(u,{cache:'no-store',mode:'cors'});if(!r.ok)throw Error('HTTP '+r.status);const d=await r.json();if(Array.isArray(d.items))return d;}catch(e){last=e}}throw last||Error('news.json')}"
new = "async function fetchNewsData(){try{const r=await fetch(DATA+'?v='+Date.now(),{cache:'no-store'});if(!r.ok)throw Error('HTTP '+r.status);const d=await r.json();if(Array.isArray(d.items))return d;}catch(e){}const fallback=window.__NEWS_FALLBACK__;if(fallback&&Array.isArray(fallback.items))return fallback;throw Error('news.json')}"
if old in s:
    s = s.replace(old, new, 1)
else:
    print('fetchNewsData pattern not found; leaving existing loader')

# If the network request fails, render the embedded dataset instead of showing
# an error page. Keep periodic retries so a fresh network dataset replaces it.
s = s.replace(
    "document.getElementById('hero').innerHTML='<div class=\"empty\">تعذر الاتصال بمصدر الأخبار. ستتم إعادة المحاولة تلقائياً.</div>';setTimeout(boot,15000)",
    "const f=window.__NEWS_FALLBACK__;if(f&&Array.isArray(f.items)){ALL=f.items.filter(x=>x&&x.title);render(ALL);return;}document.getElementById('hero').innerHTML='<div class=\"empty\">تعذر تحميل الأخبار حالياً.</div>';setTimeout(boot,15000)",
    1,
)

p.write_text(s, encoding='utf-8')
print('تم إصلاح مصدر الأخبار: تحميل same-origin مع نسخة أخبار مدمجة داخل الصفحة وإعادة المحاولة تلقائياً')
