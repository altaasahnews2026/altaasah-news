from pathlib import Path
import hashlib, html, json, re
from urllib.parse import quote

BASE = 'https://altaasahnews2026.github.io/altaasah-news/'
NEWS_DIR = Path('news')
NEWS_DIR.mkdir(exist_ok=True)

def esc(v):
    return html.escape(str(v or ''), quote=True)

def slug(item, index):
    raw = f"{item.get('title','')}-{item.get('published','')}-{index}"
    h = hashlib.sha256(raw.encode('utf-8')).hexdigest()[:12]
    return h

def image_url(path):
    if not path:
        return BASE + '6deaa228-fef4-472c-819d-400fa6c78630.jpg'
    return BASE + path.lstrip('./')

p = Path('news.json')
data = json.loads(p.read_text(encoding='utf-8'))
items = data.get('items', [])
urls = []
for i, item in enumerate(items):
    sid = slug(item, i)
    article_url = f'{BASE}news/{sid}.html'
    item['article_url'] = article_url
    source_url = item.get('url', '')
    title = item.get('title', 'خبر من التاسعة نيوز')
    cat = item.get('category', 'أخبار العراق')
    published = item.get('published', '')
    image = image_url(item.get('image'))
    # The feed contains headlines and source links; do not invent article body text.
    body = f'''<p>تنشر <strong>التاسعة نيوز</strong> هذا الخبر ضمن تغطيتها المستمرة للأحداث في العراق وكركوك والعالم.</p>\n<p>للاطلاع على التفاصيل الكاملة والمعلومات المنشورة من المصدر، يمكن متابعة الخبر عبر الرابط الأصلي أدناه.</p>'''
    ld = {
        '@context':'https://schema.org', '@type':'NewsArticle',
        'headline': title, 'datePublished': published, 'dateModified': published,
        'mainEntityOfPage': {'@type':'WebPage','@id':article_url},
        'image':[image], 'articleSection':cat,
        'author':{'@type':'Organization','name':'التاسعة نيوز'},
        'publisher':{'@type':'Organization','name':'التاسعة نيوز','logo':{'@type':'ImageObject','url':BASE+'assets/logo.svg'}},
        'description': title,
        'isPartOf':{'@type':'NewsMediaOrganization','name':'التاسعة نيوز','url':BASE}
    }
    doc = f'''<!doctype html>\n<html lang="ar" dir="rtl">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1">\n<meta name="robots" content="index,follow,max-image-preview:large">\n<title>{esc(title)} | التاسعة نيوز</title>\n<meta name="description" content="{esc(title)}">\n<link rel="canonical" href="{esc(article_url)}">\n<meta property="og:type" content="article">\n<meta property="og:site_name" content="التاسعة نيوز">\n<meta property="og:title" content="{esc(title)}">\n<meta property="og:description" content="{esc(title)}">\n<meta property="og:url" content="{esc(article_url)}">\n<meta property="og:image" content="{esc(image)}">\n<meta property="og:locale" content="ar_IQ">\n<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False, separators=(',',':'))}</script>\n<style>body{{margin:0;background:#f4f6f9;color:#14263b;font-family:Tahoma,Arial,sans-serif}}.wrap{{width:min(900px,calc(100% - 28px));margin:auto}}header{{background:#071b33;border-bottom:4px solid #e21d2b;padding:18px 0}}header a{{color:#fff;text-decoration:none;font-weight:900}}main{{padding:28px 0 50px}}article{{background:#fff;border:1px solid #dfe5ec;border-radius:14px;overflow:hidden}}.hero{{width:100%;height:min(500px,55vw);min-height:240px;object-fit:cover;display:block}}.content{{padding:25px}}.tag{{display:inline-block;background:#e21d2b;color:#fff;padding:7px 11px;border-radius:5px;font-size:12px;font-weight:900}}h1{{font-size:30px;line-height:1.6;margin:14px 0}}.meta{{color:#718096;font-size:12px;margin-bottom:22px}}p{{font-size:17px;line-height:2;color:#33485e}}.source{{display:inline-block;background:#071b33;color:#fff;text-decoration:none;padding:12px 18px;border-radius:7px;font-weight:900;margin-top:10px}}footer{{text-align:center;color:#718096;padding:20px;font-size:11px}}</style>\n</head>\n<body><header><div class="wrap"><a href="{BASE}">التاسعة نيوز — نعلم لتعلم</a></div></header><main><div class="wrap"><article><img class="hero" src="{esc(image)}" alt="{esc(title)}" onerror="this.src='{BASE}6deaa228-fef4-472c-819d-400fa6c78630.jpg'"><div class="content"><span class="tag">{esc(cat)}</span><h1>{esc(title)}</h1><div class="meta">تاريخ النشر: {esc(published)}</div>{body}<a class="source" href="{esc(source_url)}" target="_blank" rel="nofollow noopener">قراءة الخبر من المصدر الأصلي ↗</a></div></article></div></main><footer>© التاسعة نيوز — نعلم لتعلم</footer></body></html>'''
    (NEWS_DIR / f'{sid}.html').write_text(doc, encoding='utf-8')
    urls.append((article_url, published))

p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

sitemap = ['<?xml version="1.0" encoding="UTF-8"?>','<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">']
sitemap.append(f'<url><loc>{BASE}</loc><changefreq>hourly</changefreq><priority>1.0</priority></url>')
for u, pub in urls:
    sitemap.append(f'<url><loc>{esc(u)}</loc><changefreq>daily</changefreq><priority>0.8</priority></url>')
sitemap.append('</urlset>')
Path('sitemap.xml').write_text('\n'.join(sitemap) + '\n', encoding='utf-8')
print(f'تم إنشاء {len(urls)} صفحة خبر مستقلة وتحديث sitemap.xml')
