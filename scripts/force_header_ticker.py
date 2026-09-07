from pathlib import Path
import re

p=Path('index.html')
s=p.read_text(encoding='utf-8')

# Top-right control: live broadcast only.
s=re.sub(r'<button\s+class="live"\s+id="live"[^>]*>.*?</button>', '<a class="live" id="live" href="https://www.alsumaria.tv/live" target="_blank" rel="noopener">● البث المباشر</a>', s, count=1, flags=re.S)
s=s.replace('id="live">● عاجل</button>', 'id="live" href="https://www.alsumaria.tv/live" target="_blank" rel="noopener">● البث المباشر</a>', 1)

# Keep the separate red breaking strip labelled as عاجل.
s=re.sub(r'(<div class="breakingTicker"\s+id="breakingTicker"><b>)[^<]*(</b>)', r'\1● عاجل\2', s, count=1)

# Remove previous ticker styles/runtime so this is the single authoritative implementation.
s=re.sub(r'<style id="force-live-ticker-style">.*?</style>', '', s, flags=re.S)
s=re.sub(r'<style id="news-bars-style">.*?</style>', '', s, flags=re.S)
s=re.sub(r'<script id="force-live-ticker-runtime">.*?</script>', '', s, flags=re.S)
s=re.sub(r'<script id="live-news-ticker-runtime">.*?</script>', '', s, flags=re.S)

style='''<style id="force-live-ticker-style">
.live{display:inline-flex!important;align-items:center;justify-content:center;background:#df1727!important;color:#fff!important;border:0;border-radius:6px;padding:10px 14px;font-weight:900;font-size:10px;white-space:nowrap}
.breakingTicker{height:42px;background:#b4000b;color:#fff;display:flex;overflow:hidden}
.breakingTicker>b,.ticker>b{min-width:104px;flex:0 0 104px;display:flex;align-items:center;justify-content:center;font-weight:900;z-index:2}
.breakingTicker>b{background:#e21d2b}
.breakingWindow,.tickerWindow{overflow:hidden;flex:1;position:relative}
.breakingTrack,.tickerTrack{height:100%;display:flex;align-items:center;width:max-content;white-space:nowrap;will-change:transform;direction:ltr}
.ticker{height:40px;background:#fff;display:flex;border-bottom:1px solid var(--line)}
.ticker>b{background:#071b33;color:#fff}
.tickerSet,.breakingSet{display:flex;align-items:center;gap:38px;padding:0 36px;direction:rtl;flex-shrink:0}
.breakingTrack a{color:#fff;font-size:11px;font-weight:900;direction:rtl}
.tickerTrack a{color:#14263b;font-size:10px;font-weight:800;direction:rtl}
.tickerCat{color:#df1727;font-size:9px;margin-left:6px}
.liveTickerItem{display:inline-flex;align-items:center}
</style>'''
s=s.replace('</head>',style+'</head>',1)

runtime=r'''<script id="force-live-ticker-runtime">
(function(){
  const esc=s=>String(s??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
  const label=x=>x.category==='عراق'?'العراق':x.category==='مشرق أوسط'?'المشرق الأوسط':'دولي';
  const make=x=>`<a class="liveTickerItem" href="${esc(x.url||'#')}" target="_blank" rel="noopener"><span class="tickerCat">[${esc(label(x))}]</span>${esc(x.title)}</a>`;
  const state={latest:{el:null,x:0,width:0,speed:58,items:[],paused:false,sig:''},breaking:{el:null,x:0,width:0,speed:82,items:[],paused:false,sig:''}};
  function setItems(kind,items){
    const st=state[kind], el=st.el||document.getElementById(kind==='latest'?'latestTrack':'breakingTrack');
    if(!el)return; st.el=el;
    const clean=(items||[]).filter(x=>x&&x.title).slice(0,48);
    const sig=clean.map(x=>x.title+'|'+(x.url||'')).join('||');
    if(sig===st.sig && el.firstElementChild)return;
    st.sig=sig;
    const oldW=st.width, ratio=oldW?(((-st.x)%oldW)+oldW)%oldW/oldW:0;
    const set=`<div class="${kind}Set">${clean.map(make).join('')}</div>`;
    el.innerHTML=set+set;
    requestAnimationFrame(()=>{
      st.width=el.firstElementChild?el.firstElementChild.getBoundingClientRect().width:el.scrollWidth/2;
      st.x=-(st.width*ratio);
      el.style.transform=`translate3d(${st.x}px,0,0)`;
    });
  }
  function animate(now){
    Object.values(state).forEach(st=>{
      if(!st.el||!st.width||st.paused)return;
      if(!st.last)st.last=now;
      const dt=Math.min(80,now-st.last);st.last=now;
      st.x-=st.speed*dt/1000;
      if(st.x<=-st.width)st.x+=st.width;
      st.el.style.transform=`translate3d(${st.x}px,0,0)`;
    });
    requestAnimationFrame(animate);
  }
  function wireHover(st){
    if(!st.el||st.el.dataset.hoverWired)return;
    st.el.dataset.hoverWired='1';
    st.el.parentElement.addEventListener('mouseenter',()=>st.paused=true);
    st.el.parentElement.addEventListener('mouseleave',()=>{st.paused=false;st.last=performance.now()});
  }
  async function load(){
    try{
      const r=await fetch('./ticker.json?ts='+Date.now(),{cache:'no-store'});if(!r.ok)throw new Error('ticker');
      const d=await r.json();setItems('latest',d.latest||[]);setItems('breaking',d.breaking||[]);
      requestAnimationFrame(()=>{wireHover(state.latest);wireHover(state.breaking)});
    }catch(e){
      try{
        const r=await fetch('./news.json?ts='+Date.now(),{cache:'no-store'});if(!r.ok)throw e;
        const d=await r.json();const a=(d.items||[]).map(x=>({title:x.title,url:x.url,category:'عراق',breaking:x.breaking}));
        setItems('latest',a);setItems('breaking',a.filter(x=>x.breaking));
      }catch(_){ }
    }
  }
  load();
  setInterval(load,60000);
  requestAnimationFrame(animate);
})();
</script>'''
s=s.replace('</body>',runtime+'</body>',1)

assert 'البث المباشر' in s
assert 'force-live-ticker-runtime' in s
assert 'ticker.json' in s
assert 'id="live" href="https://www.alsumaria.tv/live"' in s
p.write_text(s,encoding='utf-8')
print('CONTINUOUS TICKER OK')
