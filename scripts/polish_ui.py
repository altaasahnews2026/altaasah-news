from pathlib import Path
import re

p=Path('index.html')
s=p.read_text(encoding='utf-8')

css='''
<style id="professional-news-ui">
:root{--n:#061a31;--n2:#0b2947;--r:#d7192a;--bg:#f1f4f8;--ink:#10243a;--mut:#718096;--line:#dce3eb;--sh:0 10px 30px rgba(5,25,48,.09)}
body{background:linear-gradient(#f5f7fa 0,#eef2f6 100%);font-family:Tahoma,Arial,sans-serif}
.wrap{width:min(1380px,calc(100% - 30px))}
.header{box-shadow:0 2px 12px rgba(0,0,0,.04);position:relative;z-index:5}
.head{min-height:104px;display:grid!important;grid-template-columns:1fr auto 1fr!important;align-items:center!important;gap:18px!important}
.brand{grid-column:1!important;grid-row:1!important;justify-self:end!important;align-self:center!important;display:flex!important;flex-direction:column!important;align-items:flex-end!important;text-align:right!important;z-index:10!important}
.brand img{display:block!important;visibility:visible!important;opacity:1!important;width:245px!important;height:78px!important;max-width:245px!important;object-fit:contain!important;filter:drop-shadow(0 3px 7px rgba(0,0,0,.10))!important}
.brand small{display:block!important;margin-top:-5px!important;margin-right:4px!important}
.tools:first-child{grid-column:2!important;grid-row:1!important;justify-self:center!important}
.tools:last-child{grid-column:3!important;grid-row:1!important;justify-self:start!important}
.nav{box-shadow:0 3px 10px rgba(0,0,0,.08);position:sticky;top:0;z-index:20}.nav a{transition:.18s}.ticker{position:relative;z-index:19;box-shadow:0 2px 9px rgba(0,0,0,.05)}
main{padding-top:24px}.hero{gap:18px}.lead,.latest,.card,.feature,.mini,.cat{border-radius:14px;box-shadow:var(--sh);border-color:#dfe5ec}.lead{height:470px}.leadText{right:28px;left:28px;bottom:25px}.lead h1{font-size:31px;text-shadow:0 2px 8px rgba(0,0,0,.28)}.boxTitle{height:56px;background:#fff}.side{padding:12px}.side strong{font-size:11px}.side:hover,.mini a:hover,.cat a:hover{background:#f7f9fb}.section{margin-top:30px}.headSec{margin-bottom:14px}.headSec h2{font-size:21px;font-weight:900}.headSec i{width:30px;height:4px;border-radius:3px}.grid{gap:16px}.card{transition:transform .2s,box-shadow .2s}.card:hover{transform:translateY(-4px);box-shadow:0 14px 32px rgba(5,25,48,.13)}.thumb{height:190px}.body{padding:13px 14px 15px}.body h3{font-size:13px;line-height:1.8}.meta{font-size:9px}.split{gap:16px}.feature{height:275px}.featureText{right:18px;left:18px;bottom:17px}.featureText h3{font-size:16px}.cats{gap:16px}.cat h3{font-size:16px;padding:14px}.cat a{padding:11px}.cat strong{font-size:10px}.footer{margin-top:25px}.footer .wrap{padding-top:5px}.topBtn{box-shadow:0 6px 18px rgba(0,0,0,.18)}
@media(max-width:1050px){.lead{height:430px}.grid{gap:12px}.brand img{width:220px!important;height:72px!important;max-width:220px!important}}
@media(max-width:700px){.wrap{width:calc(100% - 12px)}.head{display:grid!important;grid-template-columns:1fr!important;grid-template-rows:auto auto!important;padding:8px 0;gap:5px}.brand{grid-column:1!important;grid-row:1!important;justify-self:center!important;align-items:center!important;text-align:center!important}.brand img{width:185px!important;height:58px!important;max-width:185px!important}.tools:first-child,.tools:last-child{grid-column:1!important;grid-row:2!important;justify-self:stretch!important}.tools:last-child{display:none}.nav{position:relative}.ticker{height:43px}.lead{height:335px;border-radius:11px}.lead h1{font-size:20px}.latest{border-radius:11px}.section{margin-top:22px}.headSec h2{font-size:17px}.grid{gap:8px}.thumb{height:135px}.body h3{font-size:10px}.card{border-radius:9px}.feature{height:205px}.cat{border-radius:9px}}
</style>
<style id="news-logo-watermark">
.news-watermark{position:absolute;z-index:6;left:10px;top:10px;width:88px;height:50px;object-fit:contain;pointer-events:none;filter:drop-shadow(0 1px 3px rgba(0,0,0,.45));background:rgba(255,255,255,.82);border-radius:4px;padding:3px}.thumb,.feature,.lead,.cat,.side{position:relative}.thumb .news-watermark,.feature .news-watermark,.lead .news-watermark,.cat .news-watermark,.side .news-watermark{display:block}@media(max-width:700px){.news-watermark{width:72px;height:41px;left:7px;top:7px}}
</style>
'''
css=css.replace('Tahom a','Tahoma')
s=re.sub(r'<style id="professional-news-ui">.*?</style>\s*','',s,flags=re.S)
s=re.sub(r'<style id="news-logo-watermark">.*?</style>\s*','',s,flags=re.S)
s=s.replace('</head>',css+'</head>',1)

logo='./assets/logo.jpg?v=20260913'
s=re.sub(r'(<a class="brand"[^>]*>\s*<img\s+[^>]*src=)["\'][^"\']*(?["\'])',lambda m:m.group(1)+'"'+logo+'"',s) if False else s
# Deterministically replace every header/footer logo reference and remove the deleted SVG reference.
s=re.sub(r'(class="brand"[^>]*>\s*<img\s+[^>]*src=)["\'][^"\']*(?:["\'])',lambda m:m.group(1)+'"'+logo+'"',s,count=1,flags=re.S)
s=s.replace('src="./assets/logo.jpg"','src="'+logo+'"')
s=s.replace('src="assets/logo.jpg"','src="'+logo+'"')
s=s.replace('src="assets/logo.svg"','src="'+logo+'"')
s=s.replace('src="./assets/logo.svg"','src="'+logo+'"')
water='<img class="news-watermark" src="'+logo+'" alt="التاسعة نيوز" aria-hidden="true">'
for marker in ['<div class="thumb">','<div class="feature">','<div class="lead">','<div class="cat">','<div class="side">']:
    s=s.replace(marker,marker+water)
s=s.replace('أحدث الأخبار','آخر الأخبار')
s=s.replace('آخر الأخبار العاجلة','آخر الأخبار')
p.write_text(s,encoding='utf-8')
print('UI POLISH: official logo forced in header, footer and news containers')
