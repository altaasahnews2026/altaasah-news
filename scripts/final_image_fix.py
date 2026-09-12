from pathlib import Path
import re

BASE = 'https://altaasahnews2026.github.io/altaasah-news/'
LOGO = BASE + 'assets/logo.jpg'
p = Path('index.html')
s = p.read_text(encoding='utf-8')

# Root-cause fix: use absolute same-origin GitHub Pages URLs everywhere.
s = re.sub(r'(?<!https:)(?<!http:)(?:\\./)?assets/news/', BASE + 'assets/news/', s)
s = re.sub(r'https://raw\\.githubusercontent\\.com/altaasahnews2026/altaasah-news/main/assets/news/', BASE + 'assets/news/', s)

# Make the official logo load directly as a JPEG. This avoids a nested SVG -> JPEG
# dependency which was causing the header logo to disappear on the published page.
s = re.sub(r'(?:https://altaasahnews2026\\.github\\.io/altaasah-news/)?(?:\\./)?assets/logo\\.svg(?:\\?[^\"\']*)?', LOGO, s)
s = re.sub(r'(?:\\./)?assets/logo\\.svg(?:\\?[^\"\']*)?', LOGO, s)
s = s.replace('src="logo.jpg"', 'src="' + LOGO + '"')

# Keep images visible and make the browser revalidate fresh assets after each feed refresh.
s = s.replace('loading="lazy"', 'loading="eager"')
s = s.replace('decoding="async"', 'decoding="async" referrerpolicy="no-referrer"')

# Official Al-Taasah News logo watermark on every news-image container.
wm_css = '''<style id="news-logo-watermark">.news-watermark{position:absolute;z-index:6;left:10px;top:10px;width:88px;height:50px;object-fit:contain;pointer-events:none;filter:drop-shadow(0 1px 3px rgba(0,0,0,.45));background:rgba(255,255,255,.82);border-radius:4px;padding:3px}.thumb,.feature,.lead,.cat,.side{position:relative}@media(max-width:700px){.news-watermark{width:72px;height:41px;left:7px;top:7px}}</style>'''
s = re.sub(r'<style id="news-logo-watermark">.*?</style>\\s*', '', s, flags=re.S)
s = s.replace('</head>', wm_css + '</head>', 1)
water = '<img class="news-watermark" src="' + LOGO + '" alt="التاسعة نيوز" aria-hidden="true">'
for marker in ['<div class="thumb">','<div class="feature">','<div class="lead">','<div class="cat">','<div class="side">']:
    s = s.replace(marker, marker + water)

p.write_text(s, encoding='utf-8')
print('FINAL IMAGE FIX: official Al-Taasah News logo is loaded directly from assets/logo.jpg and watermark enforced')
