from pathlib import Path
import re

p=Path('index.html')
s=p.read_text(encoding='utf-8')

# Move/replace the upper control with a real live-broadcast link.
s,n=re.subn(r'<button\s+class="live"\s+id="live"[^>]*>.*?</button>', '<a class="live" id="live" href="https://www.alsumaria.tv/live" target="_blank" rel="noopener">● البث المباشر</a>', s, count=1, flags=re.S)
if n==0:
    s=s.replace('id="live">● عاجل</button>', 'id="live" href="https://www.alsumaria.tv/live" target="_blank" rel="noopener">● البث المباشر</a>', 1)

# Ensure the red urgent strip remains labelled as urgent; the top-right control is not.
s=re.sub(r'(<div class="breakingTicker"\s+id="breakingTicker"><b>)[^<]*(</b>)', r'\1● عاجل\2', s, count=1)

# Make the continuous ticker CSS authoritative.
style='''<style id="force-live-ticker-style">.live{display:inline-flex!important;align-items:center;justify-content:center;background:#df1727!important;color:#fff!important;border:0;border-radius:6px;padding:10px 14px;font-weight:900;font-size:10px;white-space:nowrap}.breakingTicker{height:42px;background:#b4000b;color:#fff;display:flex;overflow:hidden}.breakingTicker>b,.ticker>b{min-width:104px;flex:0 0 104px;display:flex;align-items:center;justify-content:center;font-weight:900}.breakingTicker>b{background:#e21d2b}.breakingWindow,.tickerWindow{overflow:hidden;flex:1;direction:rtl}.breakingTrack,.tickerTrack{height:100%;display:flex;align-items:center;width:max-content;white-space:nowrap;will-change:transform;direction:rtl}.breakingSet,.tickerSet{display:flex;align-items:center;gap:38px;padding:0 36px;direction:rtl;flex-shrink:0}.breakingTrack{animation:forceBreaking 38s linear infinite}.tickerTrack{animation:forceLatest 72s linear infinite}.breakingTrack a{color:#fff;font-size:11px;font-weight:900}.tickerTrack a{color:#14263b;font-size:10px;font-weight:800}.tickerCat{color:#df1727;font-size:9px;margin-left:6px}.breakingTrack:hover,.tickerTrack:hover{animation-play-state:paused}@keyframes forceBreaking{from{transform:translate3d(0,0,0)}to{transform:translate3d(-50%,0,0)}}@keyframes forceLatest{from{transform:translate3d(0,0,0)}to{transform:translate3d(-50%,0,0)}}</style>'''
s=re.sub(r'<style id="force-live-ticker-style">.*?</style>','',s,flags=re.S)
s=s.replace('</head>',style+'</head>',1)

runtime=r'''<script id="force-live-ticker-runtime">
(function(){
 const escT=s=>String(s??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
 const label=x=>x.category==='عراق'?'العراق':x.category==='مشرق أوسط'?'المشرق الأوسط':'دولي';
 const make=x=>`<a href="${escT(x.url||'#')}" target="_blank" rel="noopener"><span class="tickerCat">[${escT(label(x))}]</span>${escT(x.title)}</a>`;
 const put=(id,a)=>{const e=document.getElementById(id);if(!e)return;const v=(a||[]).filter(x=>x&&x.title).slice(0,36),set=`<div class="tickerSet">${v.map(make).join('')}</div>`;e.innerHTML=set+set;};
 async function load(){
  try{const r=await fetch('./ticker.json?ts='+Date.now(),{cache:'no-store'});if(!r.ok)throw 0;const d=await r.json();put('latestTrack',d.latest);put('breakingTrack',d.breaking);}
  catch(_){try{const r=await fetch('./news.json?ts='+Date.now(),{cache:'no-store'});const d=await r.json();const a=(d.items||[]).map(x=>({title:x.title,url:x.url,category:'عراق',breaking:x.breaking}));put('latestTrack',a);put('breakingTrack',a.filter(x=>x.breaking));}catch(e){}}
 }
 load();setInterval(load,120000);
})();
</script>'''
s=re.sub(r'<script id="force-live-ticker-runtime">.*?</script>','',s,flags=re.S)
s=s.replace('</body>',runtime+'</body>',1)

assert 'البث المباشر' in s
assert 'force-live-ticker-runtime' in s
assert 'ticker.json' in s
assert 'id="live" href="https://www.alsumaria.tv/live"' in s
p.write_text(s,encoding='utf-8')
print('FORCED HEADER/TICKER OK')
