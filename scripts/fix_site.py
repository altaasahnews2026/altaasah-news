from pathlib import Path
import re, json, html

p = Path('index.html')
s = p.read_text(encoding='utf-8')

# Keep the image/runtime fixes already used by the site.
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
  if(u.startsWith(base+'assets/news/')) return raw+u.slice(base.length);
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
  const src=imageFor(x), original=originalImageFor(x), raw=rawImageFor(x), first=src||original||raw;
  if(!first) return `<div class="${cls}" role="img" aria-label="صورة الخبر غير متاحة"></div>`;
  const chain=[original,raw].filter(u=>u&&u!==first);
  const fallback=chain.length?` onerror="this.dataset.f=(+this.dataset.f||0)+1;if(this.dataset.f<=${chain.length})this.src='${esc(chain[0])}';if(this.dataset.f>${chain.length})this.onerror=null"`:'';
  return `<img class="${cls}" src="${esc(first)}" alt="صورة الخبر" loading="eager" decoding="async"${fallback}>`;
}
'''
    s = s[:marker_a] + replacement + s[marker_b:]

# The upper-right control is the live broadcast button.
s = s.replace('<button class="live" id="live">● عاجل</button>', '<div class="search"><input id="q" placeholder="ابحث في الأخبار..."></div>')
s = re.sub(r'<div class="tools"><div class="search"><input id="q" placeholder="ابحث في الأخبار\\.\\.\\.\"></div><div class="search"><input id="q" placeholder="ابحث في الأخبار\\.\\.\\.\"></div></div>', '<div class="tools"><div class="search"><input id="q" placeholder="ابحث في الأخبار..."></div></div>', s)
s = s.replace('<div class="tools"><span style="font-size:10px;color:#748196">أخبار العراق أولاً</span></div>', '<div class="tools"><a class="live" id="live" href="https://www.alsumaria.tv/live" target="_blank" rel="noopener">● البث المباشر</a></div>')

# Rebuild the ticker markup and CSS so the page always contains visible headlines even before JS runs.
s = re.sub(r'<style id="news-bars-style">.*?</style>', '', s, flags=re.S)
style = '''<style id="news-bars-style">
.breakingTicker{height:42px;background:#b4000b;color:#fff;display:flex;overflow:hidden}.breakingTicker>b,.ticker>b{min-width:104px;display:flex;align-items:center;justify-content:center;font-weight:900;flex:0 0 104px}.breakingTicker>b{background:#e21d2b}.breakingWindow,.tickerWindow{overflow:hidden;flex:1;position:relative}.breakingTrack,.tickerTrack{height:100%;display:flex;align-items:center;width:max-content;white-space:nowrap;will-change:transform;direction:ltr}.breakingSet,.tickerSet{display:flex;align-items:center;gap:38px;direction:rtl;padding:0 36px;flex-shrink:0}.breakingTrack a{color:#fff;font-size:11px;font-weight:900;direction:rtl}.tickerTrack a{color:var(--ink);font-size:10px;font-weight:800;direction:rtl}.tickerCat{color:var(--r);font-size:9px;margin-left:6px}.breakingTrack,.tickerTrack{animation-timing-function:linear;animation-iteration-count:infinite}.breakingTrack{animation:breakingMove 42s linear infinite}.tickerTrack{animation:tickerMove 90s linear infinite}.breakingTrack:hover,.tickerTrack:hover{animation-play-state:paused}.live{display:inline-flex!important;align-items:center;justify-content:center;border:0;background:var(--r);color:#fff;border-radius:6px;padding:10px 14px;font-weight:900;font-size:10px;cursor:pointer;white-space:nowrap}@keyframes breakingMove{from{transform:translate3d(0,0,0)}to{transform:translate3d(-50%,0,0)}}@keyframes tickerMove{from{transform:translate3d(0,0,0)}to{transform:translate3d(-50%,0,0)}}
</style>'''
s=s.replace('</head>',style+'</head>',1)

# Load current ticker data into the HTML itself. This removes the blank-strip failure mode.
ticker_path=Path('ticker.json')
if ticker_path.exists():
    try:
        td=json.loads(ticker_path.read_text(encoding='utf-8'))
        def esc_t(v): return html.escape(str(v or ''), quote=True)
        def make_item(x):
            cat=x.get('category','عراق')
            label='العراق' if cat=='عراق' else ('المشرق الأوسط' if cat in ('مشرق أوسط','المشرق الأوسط') else 'دولي')
            return f'<a href="{esc_t(x.get("url","#"))}" target="_blank" rel="noopener"><span class="tickerCat">[{label}]</span>{esc_t(x.get("title",""))}</a>'
        latest=[x for x in td.get('latest',[]) if x.get('title')][:36]
        breaking=[x for x in td.get('breaking',[]) if x.get('title')][:36]
        def double(items):
            block=''.join(make_item(x) for x in items)
            return f'<div class="tickerSet">{block}</div><div class="tickerSet">{block}</div>'
        s=re.sub(r'(<div class="tickerWindow"><div class="tickerTrack" id="latestTrack">).*?(</div></div>)',r'\1'+double(latest)+r'\2',s,count=1,flags=re.S)
        s=re.sub(r'(<div class="breakingWindow"><div class="breakingTrack" id="breakingTrack">).*?(</div></div>)',r'\1'+double(breaking)+r'\2',s,count=1,flags=re.S)
    except Exception as exc:
        print('ticker static build skipped:',exc)

# Final runtime controller: refresh data without page reload and preserve continuous movement.
runtime = r'''<script id="final-ticker-runtime">
(function(){
  const escT=s=>String(s??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
  const make=x=>{const c=x.category==='عراق'?'العراق':(x.category==='مشرق أوسط'||x.category==='المشرق الأوسط'?'المشرق الأوسط':'دولي');return `<a href="${escT(x.url||'#')}" target="_blank" rel="noopener"><span class="tickerCat">[${c}]</span>${escT(x.title)}</a>`};
  const put=(id,a)=>{const e=document.getElementById(id);if(!e)return;const v=(a||[]).filter(x=>x&&x.title).slice(0,36);if(!v.length)return;const block=v.map(make).join('');e.innerHTML=`<div class="tickerSet">${block}</div><div class="tickerSet">${block}</div>`;e.style.animation='none';void e.offsetWidth;e.style.animation=id==='breakingTrack'?'breakingMove 42s linear infinite':'tickerMove 90s linear infinite';};
  async function load(){try{const r=await fetch('./ticker.json?ts='+Date.now(),{cache:'no-store'});if(!r.ok)throw 0;const d=await r.json();put('latestTrack',d.latest);put('breakingTrack',d.breaking);}catch(e){}}
  load();setInterval(load,60000);
})();
</script>'''
s=re.sub(r'<script id="final-ticker-runtime">.*?</script>','',s,flags=re.S)
s=s.replace('</body>',runtime+'</body>',1)

# Hide source names/logos from the public UI while keeping source data internal for fetching.
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

# Hide duplicate story cards on the homepage, including near-identical headlines.
dedupe = r'''<script id="homepage-news-dedupe">
(function(){
 const selectors='.card,.side,.feature,.mini,.cat,.result,article,[data-news-id]';
 const norm=v=>String(v||'').replace(/[\u064B-\u065F\u0670]/g,'').replace(/ـ/g,'').replace(/\s+/g,' ').replace(/^(عاجل|بالصور|بالفيديو|خاص|متابعة)\s*[:：-]?\s*/,'').trim().toLowerCase();
 const words=v=>norm(v).split(/\s+/).filter(w=>w.length>2);
 function similar(a,b){
   if(!a||!b)return false;
   if(a===b)return true;
   const A=words(a),B=words(b), set=new Set(B), shared=A.filter(x=>set.has(x)).length;
   const ratio=shared/Math.max(1,Math.min(A.length,B.length));
   return ratio>=0.78 && shared>=4;
 }
 function run(){
   const seenUrls=new Set(), seenTitles=[];
   document.querySelectorAll(selectors).forEach(el=>{
     if(el.closest('header,.ticker,.breakingTicker,footer')) return;
     if(el.closest('[data-duplicate-hidden="1"]')) return;
     const a=el.querySelector('a[href]');
     const h=el.querySelector('h1,h2,h3,h4,strong');
     const title=norm(h?h.textContent:el.textContent);
     const url=norm(a&&a.href);
     if(!title || title.length<8) return;
     if(url && seenUrls.has(url)){el.setAttribute('data-duplicate-hidden','1');el.style.setProperty('display','none','important');return;}
     if(seenTitles.some(t=>similar(t,title))){el.setAttribute('data-duplicate-hidden','1');el.style.setProperty('display','none','important');return;}
     if(url) seenUrls.add(url); seenTitles.push(title);
   });
 }
 run();
 new MutationObserver(run).observe(document.body,{subtree:true,childList:true});
})();
</script>'''
if 'homepage-news-dedupe' not in s:
    s=s.replace('</body>',dedupe+'</body>',1)

p.write_text(s,encoding='utf-8')
print('تم استعادة إصلاح الصور والشريط الإخباري، مع إخفاء هوية المصادر ومنع تكرار الأخبار في الواجهة.')
