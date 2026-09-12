from pathlib import Path
import re

BASE = 'https://altaasahnews2026.github.io/altaasah-news/'
LOGO = BASE + 'assets/logo.jpg?v=20260913'
p = Path('index.html')
s = p.read_text(encoding='utf-8')

# Normalize all generated image URLs to the GitHub Pages origin.
# The browser must not be sent to raw.githubusercontent.com for site-owned images.
for folder in ('assets/news/', 'assets/editorial/'):
    escaped = re.escape(folder)
    s = re.sub(r'(?:https://altaasahnews2026\\.github\\.io/altaasah-news/)+(?=' + escaped + ')', BASE, s)
    s = re.sub(r'https://raw\\.githubusercontent\\.com/altaasahnews2026/altaasah-news/main/' + escaped, BASE + folder, s)
    s = re.sub(r'(?<![A-Za-z0-9_])\\./' + escaped, BASE + folder, s)
    s = re.sub(r'(?<![A-Za-z0-9_])' + escaped, BASE + folder, s)

# Repair any previously nested logo URL first.
s = re.sub(r'(?:https://altaasahnews2026\\.github\\.io/altaasah-news/)+https://altaasahnews2026\\.github\\.io/altaasah-news/assets/logo\\.jpg(?:\\?[^\\"\\']*)?', LOGO, s)
s = re.sub(r'https://altaasahnews2026\\.github\\.io/altaasah-news/assets/logo\\.jpg(?:\\?[^\\"\\']*)?', LOGO, s)
# Replace only standalone relative logo references. Do NOT use a broad logo.jpg regex,
# because that would match the filename inside an already absolute URL and create a nested URL.
s = re.sub(r'(?<=src=")\\./assets/logo\\.jpg(?:\\?[^\\"\\']*)?(?=")', LOGO, s)
s = re.sub(r'(?<=src=")assets/logo\\.jpg(?:\\?[^\\"\\']*)?(?=")', LOGO, s)
s = re.sub(r'(?<=src=")logo\\.jpg(?:\\?[^\\"\\']*)?(?=")', LOGO, s)
s = re.sub(r'(?:https://altaasahnews2026\\.github\\.io/altaasah-news/)?(?:\\./)?assets/logo\\.svg(?:\\?[^\\"\\']*)?', LOGO, s)

# Replace every duplicate rawizeImage definition produced by previous runs with one
# deterministic same-origin implementation. This is the key fix for the disappearing news images.
rawize = '''function rawizeImage(u){
  u=clean(u);
  if(!u) return '';
  const base='https://altaasahnews2026.github.io/altaasah-news/';
  if(u.startsWith(base+'assets/news/') || u.startsWith(base+'assets/editorial/')) return u;
  if(/^https:\\/\\/raw\\.githubusercontent\\.com\\/altaasahnews2026\\/altaasah-news\\/main\\/(assets\\/(?:news|editorial)\\/)/i.test(u)) return base+u.replace(/^https:\\/\\/raw\\.githubusercontent\\.com\\/altaasahnews2026\\/altaasah-news\\/main\\//i,'');
  if(/^\\.?\\/?assets\\/(?:news|editorial)\\//i.test(u)) return base+u.replace(/^\\.?\\//,'');
  return u;
}'''
s = re.sub(r'function rawizeImage\\(u\\)\\{.*?\\n\\}', rawize, s, flags=re.S)

# Remove duplicated watermark images and add exactly one to each supported image container.
s = re.sub(r'<img\\s+class="news-watermark"[^>]*>\\s*', '', s, flags=re.I)
wm_css = '''<style id="news-logo-watermark">.news-watermark{position:absolute;z-index:6;left:10px;top:10px;width:88px;height:50px;object-fit:contain;pointer-events:none;filter:drop-shadow(0 1px 3px rgba(0,0,0,.45));background:rgba(255,255,255,.82);border-radius:4px;padding:3px}.thumb,.feature,.lead,.cat,.side{position:relative}@media(max-width:700px){.news-watermark{width:72px;height:41px;left:7px;top:7px}}</style>'''
s = re.sub(r'<style id="news-logo-watermark">.*?</style>\\s*', '', s, flags=re.S)
s = s.replace('</head>', wm_css + '</head>', 1)
water = '<img class="news-watermark" src="' + LOGO + '" alt="التاسعة نيوز" aria-hidden="true">'
for marker in ['<div class="thumb">', '<div class="feature">', '<div class="lead">', '<div class="cat">', '<div class="side">']:
    s = s.replace(marker, marker + water)

# Keep normal news images visible.
s = s.replace('loading="lazy"', 'loading="eager"')
s = s.replace('decoding="async" referrerpolicy="no-referrer" referrerpolicy="no-referrer"', 'decoding="async" referrerpolicy="no-referrer"')

p.write_text(s, encoding='utf-8')
print('FINAL IMAGE FIX: forced same-origin news/editorial images, restored official logo, and removed duplicate rawizeImage functions')
