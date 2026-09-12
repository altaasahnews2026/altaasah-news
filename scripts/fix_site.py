from pathlib import Path
import re, json, html

p = Path('index.html')
s = p.read_text(encoding='utf-8')

# Remove visible source identity, source badges and source-logo blocks from the public UI.
source_ui = r'''<style id="source-brand-removal-final">
.source,.source-name,.source-logo,.news-source,.article-source,.publisher,.publisher-name,.publisher-logo,[class*="sourceName"],[class*="source-name"],[class*="sourceLogo"],[class*="source-logo"],[data-source],[data-publisher]{display:none!important;visibility:hidden!important;width:0!important;height:0!important;overflow:hidden!important}
</style>
<script id="source-brand-removal-final-runtime">
(function(){
 const names=['رووداو','روداو','الشرقية','الفلوجة','العربية','السومرية نيوز','السومرية','شفق نيوز','شفق','قناة العراقية','وكالة نينا','مجلس القضاء الأعلى','كركوك ناو'];
 const domains=['rudaw.net','alsharqiya.com','alfallujah.tv','alarabiya.net','alsumaria.tv','shafaq.com','ninanews.com','sjc.iq','kirkuknow.com','news.imn.iq'];
 const n=v=>String(v||'').replace(/\s+/g,' ').trim().toLowerCase();
 function hide(el){el.style.setProperty('display','none','important');el.style.setProperty('visibility','hidden','important');}
 function scan(){
   document.querySelectorAll('img,a,span,small,strong,div,p,li,figure').forEach(el=>{
     const a=[el.getAttribute('alt'),el.getAttribute('title'),el.getAttribute('aria-label'),el.getAttribute('href'),el.getAttribute('src')].filter(Boolean).join(' ');
     const c=String(el.className||''); const text=n(el.textContent);
     if(/source|publisher|origin|المصدر|مصدر الخبر/.test((c+' '+a).toLowerCase())) hide(el);
     if(domains.some(d=>n(a).includes(d)) && (el.tagName==='IMG'||el.tagName==='A')) hide(el);
     if(el.children.length===0 && names.some(x=>text===n(x)||text===n('المصدر: '+x)||text===n('المصدر '+x))) hide(el);
   });
 }
 scan(); new MutationObserver(scan).observe(document.documentElement,{subtree:true,childList:true});
})();
</script>'''
if 'source-brand-removal-final' not in s:
    s=s.replace('</head>',source_ui+'</head>',1)

# Prevent the same story from appearing more than once across homepage cards/lists.
dedupe = r'''<script id="homepage-news-dedupe">
(function(){
 const selectors='.card,.side,.feature,.mini a,.cat a,.result';
 const norm=v=>String(v||'').replace(/[\u064B-\u065F\u0670]/g,'').replace(/ـ/g,'').replace(/\s+/g,' ').replace(/^(عاجل|بالصور|بالفيديو|خاص|متابعة)\s*[:：-]?\s*/,'').trim().toLowerCase();
 function run(){
   const seen=new Set(); document.querySelectorAll(selectors).forEach(el=>{
     if(el.closest('header,.ticker,.breakingTicker,footer')) return;
     const a=el.querySelector('a[href]'); const h=el.querySelector('h1,h2,h3,strong');
     const key=norm((a&&a.href)||'')+'|'+norm(h?h.textContent:el.textContent);
     if(key==='|' || key.endsWith('|')) return;
     if(seen.has(key)) el.style.setProperty('display','none','important'); else seen.add(key);
   });
 }
 run(); new MutationObserver(run).observe(document.body,{subtree:true,childList:true});
})();
</script>'''
if 'homepage-news-dedupe' not in s:
    s=s.replace('</body>',dedupe+'</body>',1)

p.write_text(s,encoding='utf-8')
print('تم تثبيت الإخفاء النهائي لهوية المصادر ومنع تكرار الخبر في واجهة الصفحة الرئيسية.')
