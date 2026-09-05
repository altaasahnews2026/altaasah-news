from pathlib import Path

p = Path('index.html')
s = p.read_text(encoding='utf-8')

# SEO foundation: keep the existing visual design while making the homepage clearer to search engines and social platforms.
seo = '''
<meta name="description" content="التاسعة نيوز — أخبار العراق وكركوك العاجلة، السياسة، الاقتصاد، الأمن، الرياضة وأهم الأخبار المحلية والعربية والدولية. نعلم لتعلم.">
<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">
<meta name="author" content="التاسعة نيوز">
<link rel="canonical" href="https://altaasahnews2026.github.io/altaasah-news/">
<meta property="og:locale" content="ar_IQ">
<meta property="og:type" content="website">
<meta property="og:site_name" content="التاسعة نيوز">
<meta property="og:title" content="التاسعة نيوز | نعلم لتعلم">
<meta property="og:description" content="أخبار العراق وكركوك العاجلة وأهم الأخبار السياسية والاقتصادية والأمنية والرياضية والعربية والدولية.">
<meta property="og:url" content="https://altaasahnews2026.github.io/altaasah-news/">
<meta property="og:image" content="https://altaasahnews2026.github.io/altaasah-news/assets/logo.svg">
<meta property="og:image:alt" content="شعار التاسعة نيوز">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="التاسعة نيوز | نعلم لتعلم">
<meta name="twitter:description" content="أخبار العراق وكركوك العاجلة وأهم الأخبار المحلية والعربية والدولية.">
<meta name="twitter:image" content="https://altaasahnews2026.github.io/altaasah-news/assets/logo.svg">
<script type="application/ld+json">
{"@context":"https://schema.org","@type":"NewsMediaOrganization","name":"التاسعة نيوز","url":"https://altaasahnews2026.github.io/altaasah-news/","logo":"https://altaasahnews2026.github.io/altaasah-news/assets/logo.svg","description":"موقع إخباري عراقي ينشر أخبار العراق وكركوك والأخبار العربية والدولية.","sameAs":[]}
</script>
<script type="application/ld+json">
{"@context":"https://schema.org","@type":"WebSite","name":"التاسعة نيوز","url":"https://altaasahnews2026.github.io/altaasah-news/","potentialAction":{"@type":"SearchAction","target":"https://altaasahnews2026.github.io/altaasah-news/?q={search_term_string}","query-input":"required name=search_term_string"}}
</script>
'''
if 'name="description" content="التاسعة نيوز' not in s:
    s = s.replace('</head>', seo + '</head>', 1)

# Keep the requested section naming and make the category navigation actually land on sections.
s = s.replace('<h2>أبرز الأخبار</h2>', '<h2>كركوك</h2>')
s = s.replace('<div id="featured" class="three">', '<div id="featured" class="three" aria-label="أخبار كركوك">')

# Turn the decorative search box into a real search control.
s = s.replace(
    '<div class="search">ابحث في التاسعة نيوز...</div>',
    '<label class="search" aria-label="البحث في الأخبار"><input id="searchInput" type="search" placeholder="ابحث في التاسعة نيوز..." autocomplete="off"><span>⌕</span></label>'
)

# Add robust search styling without changing the overall visual language.
needle = '.search{justify-self:end;width:170px;height:36px;border:1px solid var(--line);border-radius:20px;display:flex;align-items:center;padding:0 14px;color:#8b97a6;font-size:10px}'
replacement = needle + '.search input{border:0;outline:0;background:transparent;width:100%;font:inherit;color:var(--ink);direction:rtl}.search input::placeholder{color:#8b97a6}.search span{font-size:16px;color:var(--navy);margin-right:5px}'
s = s.replace(needle, replacement)

# Small responsive polish: preserve the approved layout while making it safer on narrow screens.
responsive = '''<style id="responsive-polish">
@media (max-width: 800px){
  .headIn{height:auto!important;min-height:78px!important;grid-template-columns:1fr!important;gap:8px!important;padding:10px 0!important}
  .logo{width:180px!important;height:64px!important;justify-self:center}
  .search{width:100%!important;justify-self:stretch!important;box-sizing:border-box}
  nav{overflow-x:auto;white-space:nowrap;-webkit-overflow-scrolling:touch}
  .ticker{overflow:hidden}
  .hero{grid-template-columns:1fr!important}
  .hero img{min-height:220px}
  .three{grid-template-columns:1fr!important}
  .categoryGrid{grid-template-columns:1fr!important}
  .foot{grid-template-columns:1fr 1fr!important}
}
@media (max-width:480px){
  .foot{grid-template-columns:1fr!important}
  .hero img{min-height:190px}
}
</style>'''
if 'id="responsive-polish"' not in s:
    s = s.replace('</head>', responsive + '</head>', 1)

# Replace the client-side image logic and renderer with a resilient version.
start = s.index('const DATA=')
end = s.index('</script>', start)
script = r'''const DATA='./news.json?v='+Date.now();
const fallbackByCat={
  'محلي':['https://commons.wikimedia.org/wiki/Special:FilePath/Baghdad_iraq.jpg?width=1200','https://commons.wikimedia.org/wiki/Special:FilePath/Tigris%2C_Baghdad.jpg?width=1200'],
  'سياسة':['https://commons.wikimedia.org/wiki/Special:FilePath/Parlamentsgeb%C3%A4ude_Bagdad.jpg?width=1200','https://commons.wikimedia.org/wiki/Special:FilePath/Baghdad.JPG?width=1200'],
  'اقتصاد':['https://commons.wikimedia.org/wiki/Special:FilePath/Iraq%27s_petroleum_and_gas_infrastructure._LOC_2007629280.jpg?width=1200','https://commons.wikimedia.org/wiki/Special:FilePath/Baghdad%2C_Iraq.JPG?width=1200'],
  'رياضة':['https://commons.wikimedia.org/wiki/Special:FilePath/Al-Shorta_Stadium_%282025%29.jpg?width=1200','https://commons.wikimedia.org/wiki/Special:FilePath/Baghdad_iraq.jpg?width=1200'],
  'كركوك':['https://commons.wikimedia.org/wiki/Special:FilePath/Kirkuk_City.jpg?width=1200','https://commons.wikimedia.org/wiki/Special:FilePath/Tigris%2C_Baghdad.jpg?width=1200'],
  'أمن':['https://commons.wikimedia.org/wiki/Special:FilePath/Baghdad%2C_Iraq.JPG?width=1200','https://commons.wikimedia.org/wiki/Special:FilePath/Baghdad_iraq.jpg?width=1200'],
  'عربي ودولي':['https://commons.wikimedia.org/wiki/Special:FilePath/Baghdad%2C_the_capital_and_largest_city_in_Iraq%2C_pictured_at_night_%28iss073e0134535%29.jpg?width=1200','https://commons.wikimedia.org/wiki/Special:FilePath/Baghdad%2C_the_capital_and_largest_city_in_Iraq%2C_pictured_at_night_%28iss073e0515117%29.jpg?width=1200'],
  'تعلم':['https://commons.wikimedia.org/wiki/Special:FilePath/Iraqi_schoolgirls.jpg?width=1200','https://commons.wikimedia.org/wiki/Special:FilePath/Baghdad_.jpg?width=1200']
};
const emergencyImage='./6deaa228-fef4-472c-819d-400fa6c78630.jpg';
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const clean=u=>{try{return new URL(u,document.baseURI).href}catch{return ''}};
function hash(s){let h=0;for(let i=0;i<String(s||'').length;i++)h=((h<<5)-h)+String(s||'').charCodeAt(i)|0;return Math.abs(h)}
function pickFallback(x){const arr=fallbackByCat[x?.category]||fallbackByCat['محلي'];return arr[hash(x?.title)%arr.length]||emergencyImage}
function imageFor(x){const u=clean(x&&x.image);if(u && !/\.svg(?:\?|$)/i.test(u))return u;return pickFallback(x)}
function img(x,cls=''){const src=imageFor(x);const fallback=pickFallback(x);return `<img class="${cls}" src="${esc(src)}" alt="صورة توضيحية للخبر" loading="lazy" decoding="async" referrerpolicy="no-referrer" onerror="this.onerror=null;this.src='${esc(fallback)}';this.onerror=function(){this.onerror=null;this.src='${emergencyImage}'}">`}
function date(s){try{return new Date(s).toLocaleDateString('ar-IQ',{day:'2-digit',month:'2-digit',year:'numeric'})}catch{return ''}}
function tickerMarkup(items){const html=items.slice(0,12).map(x=>`<span>${esc(x.title)}</span>`).join('');return `<div class="tickerSet">${html}</div><div class="tickerSet" aria-hidden="true">${html}</div>`}
let ALL_ITEMS=[];
function render(items){
  if(!items.length){document.getElementById('heroTitle').textContent='لا توجد نتائج مطابقة';return}
  const hero=items[0];
  const hi=document.getElementById('heroImage');hi.src=imageFor(hero);hi.onerror=function(){this.onerror=null;this.src=pickFallback(hero)};
  document.getElementById('heroCat').textContent=hero.category||'أخبار العراق';
  document.getElementById('heroTitle').textContent=hero.title;
  document.getElementById('sideNews').innerHTML=items.slice(1,7).map(x=>`<a class="latestItem" href="${esc(x.url||'#')}" target="_blank" rel="noopener"><small>${esc(x.category)} • ${esc(date(x.published))}</small><strong>${esc(x.title)}</strong></a>`).join('');
  document.getElementById('ticker').innerHTML=tickerMarkup(items);
  document.getElementById('newsCards').innerHTML=items.slice(0,8).map(x=>`<article class="card"><a href="${esc(x.url||'#')}" target="_blank" rel="noopener"><div class="thumb">${img(x)}</div><div class="body"><h3>${esc(x.title)}</h3><div class="meta">${esc(x.category)} • ${esc(date(x.published))}</div></div></a></article>`).join('');
  const kirkuk=items.filter(x=>x.category==='كركوك');
  const featured=(kirkuk.length?kirkuk:items.slice(0,3)).slice(0,3);
  document.getElementById('featured').innerHTML=featured.map(x=>`<a class="feature" href="${esc(x.url||'#')}" target="_blank" rel="noopener">${img(x)}<div class="featureText"><span class="tag">${esc(x.category)}</span><h3>${esc(x.title)}</h3></div></a>`).join('');
  const groups=['سياسة','اقتصاد','رياضة','كركوك','أمن','تعلم'];
  document.getElementById('categoryGrid').innerHTML=groups.map(cat=>{const arr=items.filter(x=>x.category===cat).slice(0,3);const list=(arr.length?arr:items.slice(0,3)).map(x=>`<a class="catItem" href="${esc(x.url||'#')}" target="_blank" rel="noopener">${img(x)}<strong>${esc(x.title)}</strong></a>`).join('');return `<section id="${cat==='كركوك'?'kirkuk':cat==='سياسة'?'politics':cat==='اقتصاد'?'economy':cat==='رياضة'?'sports':cat==='أمن'?'security':'education'}" class="catBox"><div class="catTitle"><span>—</span>${cat}</div>${list}</section>`}).join('');
}
function doSearch(){const q=(document.getElementById('searchInput')?.value||'').trim().toLowerCase();if(!q){render(ALL_ITEMS);return}render(ALL_ITEMS.filter(x=>`${x.title} ${x.category}`.toLowerCase().includes(q)));document.getElementById('latest')?.scrollIntoView({behavior:'smooth',block:'start'})}
fetch(DATA).then(r=>{if(!r.ok)throw new Error('news.json');return r.json()}).then(d=>{ALL_ITEMS=Array.isArray(d.items)?d.items:[];render(ALL_ITEMS);const input=document.getElementById('searchInput');if(input){input.addEventListener('keydown',e=>{if(e.key==='Enter')doSearch()});input.addEventListener('input',()=>{if(!input.value)render(ALL_ITEMS)})}}).catch(()=>{document.getElementById('heroTitle').textContent='تعذر تحميل الأخبار مؤقتاً';document.getElementById('ticker').innerHTML='<div class="tickerSet"><span>تعذر تحميل الأخبار مؤقتاً</span></div>'});
'''
s = s[:start] + script + s[end:]
p.write_text(s, encoding='utf-8')
print('تم تحسين SEO والاستجابة للموبايل وإصلاح الصور والبحث وقسم كركوك وربط الأقسام.')
