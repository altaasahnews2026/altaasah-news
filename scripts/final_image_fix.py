from pathlib import Path
import re

BASE = 'https://altaasahnews2026.github.io/altaasah-news/'
p = Path('index.html')
s = p.read_text(encoding='utf-8')

# Root-cause fix: use absolute same-origin GitHub Pages URLs everywhere.
# Relative paths can resolve incorrectly when the same markup is reused from /news/*.html.
s = re.sub(
    r'(?<!https:)(?<!http:)(?:\.\/)?assets/news/',
    BASE + 'assets/news/',
    s,
)
s = re.sub(
    r'https://raw\.githubusercontent\.com/altaasahnews2026/altaasah-news/main/assets/news/',
    BASE + 'assets/news/',
    s,
)

# Keep images visible and make the browser revalidate fresh assets after each feed refresh.
s = s.replace('loading="lazy"', 'loading="eager"')
s = s.replace('decoding="async"', 'decoding="async" referrerpolicy="no-referrer"')

p.write_text(s, encoding='utf-8')
print('FINAL IMAGE FIX: absolute same-origin image URLs enforced')
