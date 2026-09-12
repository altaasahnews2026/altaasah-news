from pathlib import Path
import re

BASE = 'https://altaasahnews2026.github.io/altaasah-news/'
LOGO = BASE + 'assets/logo.jpg?v=20260913'
p = Path('index.html')
s = p.read_text(encoding='utf-8')

# Normalize only corrupted/remote NEWS image URLs. Never prepend BASE twice.
s = re.sub(r'(?:https://altaasahnews2026\.github\.io/altaasah-news/)+assets/news/', BASE + 'assets/news/', s)
s = re.sub(r'https://raw\.githubusercontent\.com/altaasahnews2026/altaasah-news/main/assets/news/', BASE + 'assets/news/', s)
s = re.sub(r'(?:https://altaasahnews2026\.github\.io/altaasah-news/)+https://altaasahnews2026\.github\.io/altaasah-news/assets/news/', BASE + 'assets/news/', s)

# Repair any previously nested logo URL first.
s = re.sub(r'(?:https://altaasahnews2026\.github\.io/altaasah-news/)+https://altaasahnews2026\.github\.io/altaasah-news/assets/logo\.jpg(?:\?[^\"\']*)?', LOGO, s)
s = re.sub(r'https://altaasahnews2026\.github\.io/altaasah-news/assets/logo\.jpg(?:\?[^\"\']*)?', LOGO, s)
# Replace only standalone relative logo references. Do NOT use a broad logo.jpg regex,
# because that would match the filename inside an already absolute URL and create a nested URL.
s = re.sub(r'(?<=src=")\./assets/logo\.jpg(?:\?[^\"\']*)?(?=")', LOGO, s)
s = re.sub(r'(?<=src=")assets/logo\.jpg(?:\?[^\"\']*)?(?=")', LOGO, s)
s = re.sub(r'(?<=src=")logo\.jpg(?:\?[^\"\']*)?(?=")', LOGO, s)
s = re.sub(r'(?:https://altaasahnews2026\.github\.io/altaasah-news/)?(?:\./)?assets/logo\.svg(?:\?[^\"\']*)?', LOGO, s)

# Remove duplicated watermark images and add exactly one to each supported image container.
s = re.sub(r'<img\s+class="news-watermark"[^>]*>\s*', '', s, flags=re.I)
wm_css = '''<style id="news-logo-watermark">.news-watermark{position:absolute;z-index:6;left:10px;top:10px;width:88px;height:50px;object-fit:contain;pointer-events:none;filter:drop-shadow(0 1px 3px rgba(0,0,0,.45));background:rgba(255,255,255,.82);border-radius:4px;padding:3px}.thumb,.feature,.lead,.cat,.side{position:relative}@media(max-width:700px){.news-watermark{width:72px;height:41px;left:7px;top:7px}}</style>'''
s = re.sub(r'<style id="news-logo-watermark">.*?</style>\s*', '', s, flags=re.S)
s = s.replace('</head>', wm_css + '</head>', 1)
water = '<img class="news-watermark" src="' + LOGO + '" alt="التاسعة نيوز" aria-hidden="true">'
for marker in ['<div class="thumb">', '<div class="feature">', '<div class="lead">', '<div class="cat">', '<div class="side">']:
    s = s.replace(marker, marker + water)

# Keep normal news images visible.
s = s.replace('loading="lazy"', 'loading="eager"')
s = s.replace('decoding="async" referrerpolicy="no-referrer" referrerpolicy="no-referrer"', 'decoding="async" referrerpolicy="no-referrer"')

p.write_text(s, encoding='utf-8')
print('FINAL IMAGE FIX: repaired nested URLs, restored official logo, and preserved news image paths')
