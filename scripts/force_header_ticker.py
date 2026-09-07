from pathlib import Path
import re

p=Path('index.html')
s=p.read_text(encoding='utf-8')
s=re.sub(r'<button\s+class="live"\s+id="live"[^>]*>.*?</button>', '<a class="live" id="live" href="https://www.alsumaria.tv/live" target="_blank" rel="noopener">● البث المباشر</a>', s, count=1, flags=re.S)
s=s.replace('id="live">● عاجل</button>', 'id="live" href="https://www.alsumaria.tv/live" target="_blank" rel="noopener">● البث المباشر</a>', 1)
s=re.sub(r'(<div class="breakingTicker"\s+id="breakingTicker"><b>)[^<]*(</b>)', r'\1● عاجل\2', s, count=1)
for sid in ('force-live-ticker-style','news-bars-style'):
    s=re.sub(r'<style id="'+re.escape(sid)+r'">.*?</style>', '', s, flags=re.S)
for sid in ('force-live-ticker-runtime','live-news-ticker-runtime','final-ticker-runtime'):
    s=re.sub(r'<script id="'+re.escape(sid)+r'">.*?</script>', '', s, flags=re.S)
style='''<style id="force-live-ticker-style">
.breakingTicker{height:42px;background:#b4000b;color:#fff;display:flex;overflow:hidden}.ticker{height:40px;background:#fff;color:#14263b;display:flex;overflow:hidden;border-bottom:1px solid var(--line)}
.breakingTicker>b,.ticker>b{min-width:104px;flex:0 0 104px;display:flex;align-items:center;justify-content:center;font-weight:900;z-index:3}.breakingTicker>b{background:#e21d2b}.ticker>b{background:#071b33;color:#fff}
.breakingWindow,.tickerWindow{overflow:hidden;flex:1;position:relative;direction:ltr}.breakingTrack,.tickerTrack{height:100%;display:flex;align-items:center;width:max-content;white-space:nowrap;will-change:transform;transform:translate3d(0,0,0)}
.breakingSet,.tickerSet{display:flex;flex-direction:row;align-items:center;gap:38px;padding:0 36px;direction:rtl;flex:0 0 auto;width:max-content;height:100%}.breakingTrack a,.tickerTrack a{display:inline-flex;align-items:center;flex:0 0 auto;direction:rtl;unicode-bidi:plaintext;white-space:nowrap}.breakingTrack a{color:#fff;font-size:11px;font-weight:900}.tickerTrack a{color:#14263b;font-size:10px;font-weight:800}.tickerCat{color:#df1727;font-size:9px;margin-left:6px}.live{display:inline-flex!important;align-items:center;justify-content:center;background:#df1727!important;color:#fff!important;border:0;border-radius:6px;padding:10px 14px;font-weight:900;font-size:10px;white-space:nowrap}
</style>'''
s=s.replace('</head>',style+'</head>',1)
runtime=r'''<script id="force-live-ticker-runtime">
(function(){
 const esc=s=>String(s??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
 const label=x=>x.category==='عراق'?'العراق':(x.category==='مشرق أوسط'||x.category==='المشرق الأوسط'?'المشرق الأوسط':'دولي');
 const make=x=>`<a class="liveTickerItem" href="${esc(x.url||'#')}" target="_blank" rel="noopener"><span class="tickerCat">[${esc(label(x))}]</span>${esc(x.title)}</a>`;
 const state={latest:{el:null,width:0,x:0,speed:52,paused:false,last:0,sig:''},breaking:{el:null,width:0,x:0,speed:76,paused:false,last:0,sig:''}};
 function get(k){const st=state[k];if(!st.el)st.el=document.getElementById(k==='latest'?'latestTrack':'breakingTrack');return st;}
 function render(k,items){const st=get(k);if(!st.el)return;const clean=(items||[]).filter(x=>x&&x.title).slice(0,48);if(!clean.length)return;const sig=clean.map(x=>(x.title||'')+'|'+(x.url||'')).join('||');if(sig===st.sig&&st.el.firstElementChild)return;st.sig=sig;const oldW=st.width;const ratio=oldW?((((-st.x)%oldW)+oldW)%oldW)/oldW:0;st.el.innerHTML='';const a=document.createElement('div');a.className=k+'Set';clean.forEach(x=>a.insertAdjacentHTML('beforeend',make(x)));const b=a.cloneNode(true);st.el.append(a,b);requestAnimationFrame(()=>{st.width=a.getBoundingClientRect().width;st.x=-(st.width*ratio);st.el.style.transform=`translate3d(${st.x}px,0,0)`;});}
 function loop(now){Object.values(state).forEach(st=>{if(!st.el||!st.width||st.paused){st.last=now;return;}if(!st.last)st.last=now;const dt=Math.min(50,Math.max(0,now-st.last));st.last=now;st.x-=st.speed*dt/1000;if(st.x<=-st.width)st.x+=st.width;st.el.style.transform=`translate3d(${st.x}px,0,0)`;});requestAnimationFrame(loop);}
 function wire(k){const st=get(k);if(!st.el||st.el.dataset.wired)return;st.el.dataset.wired='1';const w=st.el.parentElement;w.addEventListener('mouseenter',()=>st.paused=true);w.addEventListener('mouseleave',()=>{st.paused=false;st.last=performance.now()});}
 async function load(){try{const r=await fetch('./ticker.json?ts='+Date.now(),{cache:'no-store'});if(!r.ok)throw 0;const d=await r.json();render('latest',d.latest||[]);render('breaking',d.breaking||[]);wire('latest');wire('breaking');}catch(e){try{const r=await fetch('./news.json?ts='+Date.now(),{cache:'no-store'});if(!r.ok)throw e;const d=await r.json();const a=(d.items||[]).map(x=>({title:x.title,url:x.url,category:'عراق',breaking:x.breaking}));render('latest',a);render('breaking',a.filter(x=>x.breaking));wire('latest');wire('breaking');}catch(_){}}}
 load();setInterval(load,60000);requestAnimationFrame(loop);
})();
</script>'''
s=s.replace('</body>',runtime+'</body>',1)
assert 'البث المباشر' in s and 'force-live-ticker-runtime' in s and 'ticker.json' in s
assert '@keyframes breakingMove' not in s and '@keyframes tickerMove' not in s
p.write_text(s,encoding='utf-8')
print('AUTHORITATIVE RTL TICKER OK')
