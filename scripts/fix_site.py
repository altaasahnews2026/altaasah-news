from pathlib import Path
import re

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
  const src=imageFor(x), original=originalImageFor(x), raw=rawImageFor(x), first=src||original||raw;
  if(!first) return `<div class="${cls}" role="img" aria-label="صورة الخبر غير متاحة"></div>`;
  const chain=[original,raw].filter(u=>u&&u!==first);
  const fallback=chain.length?` onerror="this.dataset.f=(+this.dataset.f||0)+1;if(this.dataset.f<=${chain.length})this.src='${esc(chain[0])}';if(this.dataset.f>${chain.length})this.onerror=null"`:'';
  return `<img class="${cls}" src="${esc(first)}" alt="صورة الخبر" loading="eager" decoding="async"${fallback}>`;
}
'''
    s = s[:marker_a] + replacement + s[marker_b:]

# The upper-right red control is now the live broadcast button, not an urgent-news label.
s = s.replace('<button class="live" id="live">● عاجل</button>', '<div class="search"><input id="q" placeholder="ابحث في الأخبار..."></div>')
# The original first tools block has two search elements after the replacement; normalize it.
s = re.sub(r'<div class="tools"><div class="search"><input id="q" placeholder="ابحث في الأخبار\.\.\.\"></div><div class="search"><input id="q" placeholder="ابحث في الأخبار\.\.\.\"></div></div>', '<div class="tools"><div class="search"><input id="q" placeholder="ابحث في الأخبار..."></div></div>', s)
s = s.replace('<div class="tools"><span style="font-size:10px;color:#748196">أخبار العراق أولاً</span></div>', '<div class="tools"><a class="live" id="live" href="https://www.alsumaria.tv/live" target="_blank" rel="noopener">● البث المباشر</a></div>')

# Continuous headline strips: the runtime refreshes ticker.json without reloading the page.
s = re.sub(r'<style id="news-bars-style">.*?</style>', '', s, flags=re.S)
style = '''<style id="news-bars-style">
.breakingTicker{height:42px;background:#b4000b;color:#fff;display:flex;overflow:hidden}.breakingTicker>b,.ticker>b{min-width:104px;display:flex;align-items:center;justify-content:center;font-weight:900;flex:0 0 104px}.breakingTicker>b{background:#e21d2b}.breakingWindow,.tickerWindow{overflow:hidden;flex:1;direction:rtl;position:relative}.breakingTrack,.tickerTrack{height:100%;display:flex;align-items:center;width:max-content;white-space:nowrap;will-change:transform;direction:rtl}.breakingTrack{animation:breakingMove 38s linear infinite}.ticker{height:40px;background:#fff;display:flex;border-bottom:1px solid var(--line)}.ticker>b{background:#071b33;color:#fff}.tickerTrack{animation:tickerMove 72s linear infinite}.breakingSet,.tickerSet{display:flex;align-items:center;gap:38px;direction:rtl;padding-right:36px;padding-left:36px;flex-shrink:0}.breakingTrack a{color:#fff;font-size:11px;font-weight:900}.tickerTrack a{color:var(--ink);font-size:10px;font-weight:800}.tickerTrack a .tickerCat{color:var(--r);font-size:9px;margin-left:6px}.breakingTrack:hover,.tickerTrack:hover{animation-play-state:paused}.live{display:inline-flex;align-items:center;justify-content:center;border:0;background:var(--r);color:#fff;border-radius:6px;padding:10px 14px;font-weight:900;font-size:10px;cursor:pointer;white-space:nowrap}.live:hover{background:#b80f1c}@keyframes breakingMove{from{transform:translate3d(0,0,0)}to{transform:translate3d(-50%,0,0)}}@keyframes tickerMove{from{transform:translate3d(0,0,0)}to{transform:translate3d(-50%,0,0)}}
</style>'''
s=s.replace('</head>',style+'</head>',1)

# Inject the live ticker controller once, after the existing page script.
if 'id="live-news-ticker-runtime"' not in s:
    runtime = r'''<script id="live-news-ticker-runtime">
(function(){
  const escT=s=>String(s??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
  const link=x=>x.url||'#';
  const label=x=>x.category==='عراق'?'العراق':x.category==='مشرق أوسط'?'المشرق الأوسط':'دولي';
  const item=x=>`<a href="${escT(link(x))}" target="_blank" rel="noopener"><span class="tickerCat">[${escT(label(x))}]</span>${escT(x.title)}</a>`;
  function put(id,items){
    const el=document.getElementById(id); if(!el)return;
    const safe=(items||[]).filter(x=>x&&x.title).slice(0,36);
    const set=`<div class="tickerSet">${safe.map(item).join('')}</div>`;
    el.innerHTML=set+set;
    el.style.animationPlayState='running';
  }
  async function loadTicker(){
    try{
      const r=await fetch('./ticker.json?ts='+Date.now(),{cache:'no-store'});
      if(!r.ok)throw new Error('ticker');
      const d=await r.json();
      put('latestTrack',d.latest||[]);
      put('breakingTrack',d.breaking||[]);
    }catch(e){
      try{
        const r=await fetch('./news.json?ts='+Date.now(),{cache:'no-store'}); if(!r.ok)return;
        const d=await r.json(); const a=(d.items||[]).map(x=>({title:x.title,url:x.url,category:'عراق',breaking:x.breaking}));
        put('latestTrack',a); put('breakingTrack',a.filter(x=>x.breaking));
      }catch(_){ }
    }
  }
  loadTicker();
  setInterval(loadTicker,120000);
})();
</script>'''
    s=s.replace('</body>',runtime+'</body>',1)

p.write_text(s,encoding='utf-8')
print('تم تثبيت البث المباشر أعلى اليمين وشريط الأخبار العراقي والعربي والدولي والشريط العاجل المتجدد.')
