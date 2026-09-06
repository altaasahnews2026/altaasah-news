from pathlib import Path

p = Path('index.html')
s = p.read_text(encoding='utf-8')

# Keep the existing approved visual identity and strengthen SEO/accessibility.
seo = '''
<meta name="description" content="التاسعة نيوز — أخبار العراق وكركوك العاجلة، السياسة، الاقتصاد، الأمن، الرياضة وأهم الأخبار المحلية والعربية والدولية. نعلم لتعلم.">
<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">
<meta name="author" content="التاسعة نيوز">
<link rel="canonical" href="https://altaasahnews2026.github.io/altaasah-news/">
<meta property="og:locale" content="ar_IQ"><meta property="og:type" content="website"><meta property="og:site_name" content="التاسعة نيوز">
<meta property="og:title" content="التاسعة نيوز | نعلم لتعلم"><meta property="og:description" content="أخبار العراق وكركوك العاجلة وأهم الأخبار السياسية والاقتصادية والأمنية والرياضية والعربية والدولية.">
<meta property="og:url" content="https://altaasahnews2026.github.io/altaasah-news/"><meta property="og:image" content="https://altaasahnews2026.github.io/altaasah-news/assets/logo.svg"><meta property="og:image:alt" content="شعار التاسعة نيوز">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="التاسعة نيوز | نعلم لتعلم"><meta name="twitter:description" content="أخبار العراق وكركوك العاجلة وأهم الأخبار المحلية والعربية والدولية."><meta name="twitter:image" content="https://altaasahnews2026.github.io/altaasah-news/assets/logo.svg">
<script type="application/ld+json">{"@context":"https://schema.org","@type":"NewsMediaOrganization","name":"التاسعة نيوز","url":"https://altaasahnews2026.github.io/altaasah-news/","logo":"https://altaasahnews2026.github.io/altaasah-news/assets/logo.svg","description":"موقع إخباري عراقي ينشر أخبار العراق وكركوك والأخبار العربية والدولية.","sameAs":[]}</script>
<script type="application/ld+json">{"@context":"https://schema.org","@type":"WebSite","name":"التاسعة نيوز","url":"https://altaasahnews2026.github.io/altaasah-news/","potentialAction":{"@type":"SearchAction","target":"https://altaasahnews2026.github.io/altaasah-news/?q={search_term_string}","query-input":"required name=search_term_string"}}</script>
'''
if 'name="description" content="التاسعة نيوز' not in s: s = s.replace('</head>', seo + '</head>', 1)

s = s.replace('<h2>أبرز الأخبار</h2>', '<h2>كركوك</h2>')
s = s.replace('<div id="featured" class="three">', '<div id="featured" class="three" aria-label="أخبار كركوك">')
s = s.replace('<div class="search">ابحث في التاسعة نيوز...</div>', '<label class="search" aria-label="البحث في الأخبار"><input id="searchInput" type="search" placeholder="ابحث في التاسعة نيوز..." autocomplete="off"><span>⌕</span></label>')

needle = '.search{justify-self:end;width:170px;height:36px;border:1px solid var(--line);border-radius:20px;display:flex;align-items:center;padding:0 14px;color:#8b97a6;font-size:10px}'
if needle in s and '.search input{' not in s:
    s = s.replace(needle, needle + '.search input{border:0;outline:0;background:transparent;width:100%;font:inherit;color:var(--ink);direction:rtl}.search input::placeholder{color:#8b97a6}.search span{font-size:16px;color:var(--navy);margin-right:5px}')

responsive = '''<style id="responsive-polish">
@media (max-width:800px){.headIn{height:auto!important;min-height:78px!important;grid-template-columns:1fr!important;gap:8px!important;padding:10px 0!important}.logo{width:180px!important;height:64px!important;justify-self:center}.search{width:100%!important;justify-self:stretch!important;box-sizing:border-box}nav{overflow-x:auto;white-space:nowrap;-webkit-overflow-scrolling:touch}.ticker{overflow:hidden}.hero{grid-template-columns:1fr!important}.hero img{min-height:220px}.three{grid-template-columns:1fr!important}.categoryGrid{grid-template-columns:1fr!important}.foot{grid-template-columns:1fr 1fr!important}}
@media (max-width:480px){.foot{grid-template-columns:1fr!important}.hero img{min-height:190px}}
</style>'''
if 'id="responsive-polish"' not in s: s = s.replace('</head>', responsive + '</head>', 1)

start = s.index('const DATA=')
end = s.index('</script>', start)
script = r'''const DATA='./news.json?v='+Date.now();
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const clean=u=>{try{return new URL(u,document.baseURI).href}catch{return ''}};
const placeholder='./assets/news/no-image-default.svg';
function imageFor(x){const u=clean(x&&x.image);if(u && !/6deaa228-fef4-472c-819d-400fa6c78630\.jpg(?:\?|$)/i.test(u) && !/logo\.svg(?:\?|$)/i.test(u))return u;return placeholder}
function img(x,cls=''){return `<img class="${cls}" src="${esc(imageFor(x))}" alt="صورة الخبر" loading="lazy" decoding="async" onerror="this.onerror=null;this.src='${placeholder}'">`}
function date(s){try{return new Date(s).toLocaleDateString('ar-IQ',{day:'2-digit',month:'2-digit',year:'numeric'})}catch{return ''}}
function tickerMarkup(items){const html=items.slice(0,12).map(x=>`<span>${esc(x.title)}</span>`).join('');return `<div class="tickerSet">${html}</div><div class="tickerSet" aria-hidden="true">${html}</div>`}
let ALL_ITEMS=[];
function render(items){
 if(!items.length){document.getElementById('heroTitle').textContent='لا توجد نتائج مطابقة';return}
 const hero=items[0];const hi=document.getElementById('heroImage');hi.src=imageFor(hero);hi.onerror=function(){this.onerror=null;this.src=placeholder};
 document.getElementById('heroCat').textContent=hero.category||'أخبار العراق';document.getElementById('heroTitle').textContent=hero.title;
 document.getElementById('sideNews').innerHTML=items.slice(1,7).map(x=>`<a class="latestItem" href="${esc(x.article_url||x.url||'#')}"><small>${esc(x.category)} • ${esc(date(x.published))}</small><strong>${esc(x.title)}</strong></a>`).join('');
 document.getElementById('ticker').innerHTML=tickerMarkup(items);
 document.getElementById('newsCards').innerHTML=items.slice(0,8).map(x=>`<article class="card"><a href="${esc(x.article_url||x.url||'#')}"><div class="thumb">${img(x)}</div><div class="body"><h3>${esc(x.title)}</h3><div class="meta">${esc(x.category)} • ${esc(date(x.published))}</div></div></a></article>`).join('');
 const kirkuk=items.filter(x=>x.category==='كركوك');const featured=(kirkuk.length?kirkuk:items.slice(0,3)).slice(0,3);
 document.getElementById('featured').innerHTML=featured.map(x=>`<a class="feature" href="${esc(x.article_url||x.url||'#')}">${img(x)}<div class="featureText"><span class="tag">${esc(x.category)}</span><h3>${esc(x.title)}</h3></div></a>`).join('');
 const groups=['سياسة','اقتصاد','رياضة','كركوك','أمن','تعلم'];
 document.getElementById('categoryGrid').innerHTML=groups.map(cat=>{const arr=items.filter(x=>x.category===cat).slice(0,3);const list=(arr.length?arr:[]).map(x=>`<a class="catItem" href="${esc(x.article_url||x.url||'#')}">${img(x)}<strong>${esc(x.title)}</strong></a>`).join('');return `<section id="${cat==='كركوك'?'kirkuk':cat==='سياسة'?'politics':cat==='اقتصاد'?'economy':cat==='رياضة'?'sports':cat==='أمن'?'security':'education'}" class="catBox"><div class="catTitle"><span>—</span>${cat}</div>${list||'<div class="emptyCat">لا توجد أخبار حالياً في هذا القسم</div>'}</section>`}).join('');
}
function doSearch(){const q=(document.getElementById('searchInput')?.value||'').trim().toLowerCase();render(q?ALL_ITEMS.filter(x=>`${x.title} ${x.category}`.toLowerCase().includes(q)):ALL_ITEMS)}
fetch(DATA).then(r=>{if(!r.ok)throw Error();return r.json()}).then(d=>{ALL_ITEMS=Array.isArray(d.items)?d.items:[];render(ALL_ITEMS);const input=document.getElementById('searchInput');if(input){input.addEventListener('keydown',e=>{if(e.key==='Enter')doSearch());input.addEventListener('input',()=>{if(!input.value)render(ALL_ITEMS)})}}).catch(()=>{document.getElementById('heroTitle').textContent='تعذر تحميل الأخبار مؤقتاً';document.getElementById('ticker').innerHTML='<div class="tickerSet"><span>تعذر تحميل الأخبار مؤقتاً</span></div>'});
'''
s = s[:start] + script + s[end:]

# Remove accidental duplicate search rules accumulated by earlier automated edits.
while s.count('.search input{') > 1:
    first=s.find('.search input{'); second=s.find('.search input{', first+1)
    # remove the second rule up to its matching closing brace
    depth=0; endpos=second
    while endpos < len(s):
        if s[endpos]=='{': depth+=1
        elif s[endpos]=='}':
            depth-=1
            if depth==0: endpos+=1; break
        endpos+=1
    s=s[:second]+s[endpos:]

p.write_text(s, encoding='utf-8')
print('تم إصلاح واجهة الأخبار ومنع الصور العامة الخاطئة وتنظيف البحث.')
