from pathlib import Path
import re

BASE = 'https://altaasahnews2026.github.io/altaasah-news/'
LOGO = BASE + 'assets/logo.jpg?v=20260913'
p = Path('index.html')
s = p.read_text(encoding='utf-8')

# Normalize only already-corrupted/remote image URLs. Keep normal relative paths intact.
# The previous fixer could repeatedly prepend BASE to assets/news/, breaking every image.
s = re.sub(r'(?:https://altaasahnews2026\.github\.io/altaasah-news/)+assets/news/', BASE + 'assets/news/', s)
s = re.sub(r'https://raw\.githubusercontent\.com/altaasahnews2026/altaasah-news/main/assets/news/', BASE + 'assets/news/', s)

# Fix the OpenGraph image if an earlier run produced a nested site URL.
s = re.sub(r'(?:https://altaasahnews2026\.github\.io/altaasah-news/)+https://altaasahnews2026\.github\.io/altaasah-news/assets/news/', BASE + 'assets/news/', s)

# Official logo: always use the real JPEG directly.
s = re.sub(r'(?:https://altaasahnews2026\.github\.io/altaasah-news/)?(?:\./)?assets/logo\.svg(?:\?[^\"\']*)?', LOGO, s)
s = re.sub(r'(?<![A-Za-z0-9_./:-])logo\.jpg(?:\?[^\"\']*)?', LOGO, s)
s = s.replace('src="./assets/logo.jpg"', 'src="' + LOGO + '"')
s = s.replace('src="./assets/logo.jpg?v=20260913"', 'src="' + LOGO + '"')

# Remove duplicated watermark images created by previous runs, then add exactly one
# watermark to each supported news-image container.
s = re.sub(r'<img\s+class="news-watermark"[^>]*>\s*', '', s, flags=re.I)
wm_css = '''<style id="news-logo-watermark">.news-watermark{position:absolute;z-index:6;left:10px;top:10px;width:88px;height:50px;object-fit:contain;pointer-events:none;filter:drop-shadow(0 1px 3px rgba(0,0,0,.45));background:rgba(255,255,255,.82);border-radius:4px;padding:3px}.thumb,.feature,.lead,.cat,.side{position:relative}@media(max-width:700px){.news-watermark{width:72px;height:41px;left:7px;top:7px}}</style>'''
s = re.sub(r'<style id="news-logo-watermark">.*?</style>\s*', '', s, flags=re.S)
s = s.replace('</head>', wm_css + '</head>', 1)
water = '<img class="news-watermark" src="' + LOGO + '" alt="التاسعة نيوز" aria-hidden="true">'
for marker in ['<div class="thumb">', '<div class="feature">', '<div class="lead">', '<div class="cat">', '<div class="side">']:
    s = s.replace(marker, marker + water)

# Ensure all normal news images are visible and not lazy-loaded.
s = s.replace('loading="lazy"', 'loading="eager"')
s = s.replace('decoding="async" referrerpolicy="no-referrer" referrerpolicy="no-referrer"', 'decoding="async" referrerpolicy="no-referrer"')

p.write_text(s, encoding='utf-8')
print('FINAL IMAGE FIX: normalized image URLs, restored official logo, and deduplicated watermarks')
