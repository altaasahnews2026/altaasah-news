from pathlib import Path
import re
p=Path('index.html')
s=p.read_text(encoding='utf-8')
# Remove the complete breaking-news block (outer div + nested window + track).
s=re.sub(r'<div\s+class="breakingTicker"[^>]*id="breakingTicker"[^>]*>.*?</div>\s*</div>\s*</div>\s*', '', s, count=1, flags=re.S)
# Also handle the inverse attribute order if present.
s=re.sub(r'<div\s+id="breakingTicker"[^>]*class="breakingTicker"[^>]*>.*?</div>\s*</div>\s*</div>\s*', '', s, count=1, flags=re.S)
# Remove all previous ticker override styles/runtimes so this script is authoritative.
for sid in ('force-live-ticker-style','news-bars-style'):
    s=re.sub(r'<style id="'+re.escape(sid)+r'">.*?</style>', '', s, flags=re.S)
for sid in ('force-live-ticker-runtime','live-news-ticker-runtime','final-ticker-runtime'):
    s=re.sub(r'<script id="'+re.escape(sid)+r'">.*?</script>', '', s, flags=re.S)
style='''<style id="force-live-ticker-style">
.ticker{height:48px;background:#fff;color:#14263b;display:flex;overflow:hidden;border-bottom:1px solid var(--line);box-shadow:0 1px 3px rgba(0,0,0,.04)}
.ticker>b{min-width:128px;flex:0 0 128px;display:flex;align-items:center;justify-content:center;background:#071b33;color:#fff;font-size:12px;font-weight:900;z-index:3}
.tickerWindow{overflow:hidden;flex:1;position:relative;direction:ltr}.tickerTrack{height:100%;display:flex;align-items:center;width:max-content;white-space:nowrap;will-change:transform;transform:translate3d(0,0,0)}
.tickerSet{display:flex;flex-direction:row;align-items:center;gap:52px;padding:0 42px;direction:rtl;flex:0 0 auto;width:max-content;height:100%}
.tickerTrack a{display:inline-flex;align-items:center;flex:0 0 auto;direction:rtl;unicode-bidi:plaintext;white-space:nowrap;color:#14263b;font-size:12px;font-weight:800}
.tickerCat{color:#df1727;font-size:10px;margin-left:7px;font-weight:900}
@media(max-width:700px){.ticker{height:42px}.ticker>b{min-width:82px;font-size:10px}.tickerSet{gap:34px;padding:0 24px}.tickerTrack a{font-size:10px}.tickerCat{font-size:9px}}
</style>'''
s=s.replace('</head>',style+'</head>',1)
runtime=r'''<script id="force-live-ticker-runtime">
(function(){
 const esc=s=>String(s??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
 const label=x=>x.category==='عراق'?'العراق':(x.category==='مشرق أوسط'||x.category==='المشرق الأوسط'?'المشرق الأوسط':'دولي');
 const track=document.getElementById('latestTrack'); if(!track)return;
 let set=null,width=0,x=0,last=0,signature='';
 const speed=14; // px/sec: slow, calm and easy to read
 function render(items){
   const clean=(items||[]).filter(x=>x&&x.title).slice(0,48); if(!clean.length)return;
   const sig=clean.map(x=>(x.title||'')+'|'+(x.url||'')).join('||'); if(sig===signature&&set)return;
   signature=sig; track.innerHTML='';
   set=document.createElement('div'); set.className='tickerSet';
   clean.forEach(item=>{const a=document.createElement('a');a.href=item.url||'#';a.target='_blank';a.rel='noopener';a.innerHTML='<span class="tickerCat">['+esc(label(item))+']</span>'+esc(item.title);set.appendChild(a);});
   track.append(set,set.cloneNode(true)); x=0;
   requestAnimationFrame(()=>{width=set.getBoundingClientRect().width;});
 }
 async function load(){try{const r=await fetch('./ticker.json?ts='+Date.now(),{cache:'no-store'});if(!r.ok)throw 0;const d=await r.json();render(d.latest||[]);}catch(e){try{const r=await fetch('./news.json?ts='+Date.now(),{cache:'no-store'});const d=await r.json();render((d.items||[]).map(v=>({title:v.title,url:v.url,category:v.category||'عراق'})));}catch(_){}}}
 function loop(t){if(!last)last=t;const dt=Math.min(50,t-last);last=t;if(width){x-=speed*dt/1000;if(x<=-width)x+=width;track.style.transform='translate3d('+x+'px,0,0)';}requestAnimationFrame(loop)}
 load();setInterval(load,60000);requestAnimationFrame(loop);
})();
</script>'''
s=s.replace('</body>',runtime+'</body>',1)
assert 'breakingTicker' not in s and 'force-live-ticker-runtime' in s and 'ticker.json' in s
p.write_text(s,encoding='utf-8')
print('SINGLE SLOW LATEST-NEWS TICKER OK: 14px/s')
