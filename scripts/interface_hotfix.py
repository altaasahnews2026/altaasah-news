from pathlib import Path
import json
import re
import html

p = Path('index.html')
s = p.read_text(encoding='utf-8')

# Stable visual layer: keep the watermark small and never let generic image rules stretch it.
style = r'''<style id="interface-hotfix">
/* واجهة الصفحة الرئيسية - طبقة ثابتة بعد جميع القوالب */
.header{position:relative;z-index:30;background:#fff}
.head{min-height:96px!important}
.brand{position:relative!important;z-index:31!important}
.brand img{width:225px!important;height:72px!important;object-fit:contain!important}
.news-watermark{position:absolute!important;right:14px!important;left:auto!important;top:auto!important;bottom:14px!important;width:82px!important;height:auto!important;max-width:82px!important;max-height:50px!important;object-fit:contain!important;display:block!important;visibility:visible!important;opacity:.96!important;z-index:25!important;pointer-events:none!important;background:rgba(255,255,255,.90)!important;border-radius:5px!important;padding:3px!important}
.lead>.news-watermark{right:18px!important;bottom:18px!important;width:108px!important;max-width:108px!important;max-height:64px!important}
.thumb>img:not(.news-watermark){width:100%!important;height:100%!important;object-fit:cover!important;display:block!important}
.lead>img:not(.news-watermark){width:100%!important;height:100%!important;object-fit:cover!important;display:block!important}
.side>img:not(.news-watermark){width:88px!important;height:67px!important;object-fit:cover!important;display:block!important}
@media(max-width:700px){.brand img{width:185px!important;height:58px!important}.news-watermark{right:8px!important;bottom:8px!important;width:68px!important;max-width:68px!important;max-height:42px!important}.lead>.news-watermark{right:10px!important;bottom:10px!important;width:88px!important;max-width:88px!important}}
</style>'''
s = re.sub(r'<style id="interface-hotfix">.*?</style>', '', s, flags=re.S)
s = s.replace('</head>', style + '</head>', 1)

# The current generated page has CSS for nav/ticker but some generations lose the actual markup.
# Restore it if missing, without replacing the existing article content.
if 'class="site-nav-hotfix"' not in s:
    nav = '''<nav class="nav site-nav-hotfix" aria-label="التنقل الرئيسي"><div class="wrap navin">
<a class="active" href="./">الرئيسية</a><a href="./?cat=كركوك">كركوك</a><a href="./?cat=العراق">العراق</a><a href="./?cat=سياسة">سياسة</a><a href="./?cat=أمن">أمن</a><a href="./?cat=اقتصاد">اقتصاد</a><a href="./?cat=رياضة">رياضة</a><a href="./?cat=منوعات">منوعات</a><a href="./?cat=عربي">عربي</a><a href="./?cat=دولي">دولي</a></div></nav>'''
    s = s.replace('</header>', nav + '</header>', 1)

if 'id="homepageTickerHotfix"' not in s:
    td = {}
    try:
        td = json.loads(Path('ticker.json').read_text(encoding='utf-8'))
    except Exception:
        pass
    latest = [x for x in td.get('latest', []) if isinstance(x, dict) and x.get('title')][:30]
    def item(x):
        title = html.escape(str(x.get('title','')), quote=True)
        url = html.escape(str(x.get('url','#')), quote=True)
        return f'<a href="{url}" target="_blank" rel="noopener">{title}</a>'
    block = ''.join(item(x) for x in latest)
    if not block:
        block = '<span>التاسعة نيوز — آخر الأخبار</span>'
    ticker = f'''<div class="ticker" id="homepageTickerHotfix"><b>آخر الأخبار</b><div class="tickerWindow"><div class="tickerTrack"><div class="tickerSet">{block}</div><div class="tickerSet">{block}</div></div></div></div>'''
    s = s.replace('<main>', ticker + '<main>', 1)

# Make sure the external app.js fix is actually loaded, with cache busting.
script = '<script id="homepage-app-js" src="./assets/app.js?v=20260913-4" defer></script>'
s = re.sub(r'<script id="homepage-app-js"[^>]*></script>', '', s)
if 'id="homepage-app-js"' not in s:
    s = s.replace('</body>', script + '</body>', 1)

p.write_text(s, encoding='utf-8')
print('INTERFACE HOTFIX OK: navigation, ticker, watermark and current app.js enforced')
