from pathlib import Path
import re

p = Path('index.html')
s = p.read_text(encoding='utf-8')

# Prefer same-origin GitHub Pages assets. This avoids image failures caused by
# cross-origin/raw-host URLs while keeping the repository's generated files intact.
s = re.sub(
    r'https://raw\.githubusercontent\.com/altaasahnews2026/altaasah-news/main/assets/news/',
    './assets/news/',
    s,
)
s = re.sub(
    r'https://altaasahnews2026\.github\.io/altaasah-news/assets/news/',
    './assets/news/',
    s,
)

# Make generated news images resilient without relying on third-party hosts.
s = s.replace('decoding="async"', 'decoding="async" referrerpolicy="no-referrer"')

p.write_text(s, encoding='utf-8')
print('FINAL IMAGE FIX: same-origin assets enabled')
