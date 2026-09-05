from pathlib import Path
import hashlib, html, json

BASE = 'https://altaasahnews2026.github.io/altaasah-news/'
NEWS_DIR = Path('news')
NEWS_DIR.mkdir(exist_ok=True)
EMERGENCY = BASE + '6deaa228-fef4-472c-819d-400fa6c78630.jpg'

def esc(v):
    return html.escape(str(v or ''), quote=True)

def slug(item, index):
    raw = f"{item.get('title','')}-{item.get('published','')}-{index}"
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()[:12]

def image_url(path):
    if not path or str(path).lower().endswith('.svg'):
        return EMERGENCY
    return BASE + str(path).lstrip('./')

def iso_date(v):
    return str(v or '')

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
    published = iso_date(item.get('published'))
    image = image_url(item.get('image'))
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
    doc = f'''<!doctype html><html lang="ar" dir="rtl"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="index,follow,max-image-preview:large">
<title>{esc(title)} | التاسعة نيوز</title><meta name="description" content="{esc(title)}">
<link rel="canonical" href="{esc(article_url)}"><meta property="og:type" content="article">
<meta property="og:site_name" content="التاسعة نيوز"><meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(title)}"><meta property="og:url" content="{esc(article_url)}">
<meta property="og:image" content="{esc(image)}"><meta property="og:locale" content="ar_IQ">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{esc(title)}"><meta name="twitter:image" content="{esc(image)}">
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False, separators=(',',':'))}</script>
<style>body{{margin:0;background:#f4f6f9;color:#14263b;font-family:Tahoma,Arial,sans-serif}}.wrap{{width:min(900px,calc(100% - 28px));margin:auto}}header{{background:#071b33;border-bottom:4px solid #e21d2b;padding:18px 0}}header a{{color:#fff;text-decoration:none;font-weight:900}}main{{padding:28px 0 50px}}article{{background:#fff;border:1px solid #dfe5ec;border-radius:14px;overflow:hidden}}.hero{{width:100%;height:min(500px,55vw);min-height:240px;object-fit:cover;display:block}}.content{{padding:25px}}.tag{{display:inline-block;background:#e21d2b;color:#fff;padding:7px 11px;border-radius:5px;font-size:12px;font-weight:900}}h1{{font-size:30px;line-height:1.6;margin:14px 0}}.meta{{color:#718096;font-size:12px;margin-bottom:22px}}p{{font-size:17px;line-height:2;color:#33485e}}.source{{display:inline-block;background:#071b33;color:#fff;text-decoration:none;padding:12px 18px;border-radius:7px;font-weight:900;margin-top:10px}}footer{{text-align:center;color:#718096;padding:20px;font-size:11px}}</style>
</head><body><header><div class="wrap"><a href="{BASE}">التاسعة نيوز — نعلم لتعلم</a></div></header><main><div class="wrap"><article><img class="hero" src="{esc(image)}" alt="{esc(title)}" loading="eager" decoding="async" onerror="this.onerror=null;this.src='{EMERGENCY}'"><div class="content"><span class="tag">{esc(cat)}</span><h1>{esc(title)}</h1><div class="meta">تاريخ النشر: {esc(published)}</div><p>تنشر <strong>التاسعة نيوز</strong> هذا الخبر ضمن تغطيتها المستمرة للأحداث في العراق وكركوك والعالم.</p><p>للاطلاع على التفاصيل الكاملة والمعلومات المنشورة من المصدر، يمكن متابعة الخبر عبر الرابط الأصلي أدناه.</p><a class="source" href="{esc(source_url)}" target="_blank" rel="nofollow noopener">قراءة الخبر من المصدر الأصلي ↗</a></div></article></div></main><footer>© التاسعة نيوز — نعلم لتعلم</footer></body></html>'''
    (NEWS_DIR / f'{sid}.html').write_text(doc, encoding='utf-8')
    urls.append((article_url, published, title, cat, image))

p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

sitemap = ['<?xml version="1.0" encoding="UTF-8"?>','<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
sitemap.append(f'<url><loc>{BASE}</loc><changefreq>hourly</changefreq><priority>1.0</priority></url>')
for u, pub, title, cat, image in urls:
    sitemap.append(f'<url><loc>{esc(u)}</loc><lastmod>{esc(pub)}</lastmod><changefreq>daily</changefreq><priority>0.8</priority></url>')
sitemap.append('</urlset>')
Path('sitemap.xml').write_text('\n'.join(sitemap) + '\n', encoding='utf-8')

rss = ['<?xml version="1.0" encoding="UTF-8"?>','<rss version="2.0"><channel>',f'<title>التاسعة نيوز</title><link>{BASE}</link><description>آخر أخبار العراق وكركوك من التاسعة نيوز</description><language>ar-IQ</language>']
for u, pub, title, cat, image in urls[:30]:
    rss.append(f'<item><title>{esc(title)}</title><link>{esc(u)}</link><guid isPermaLink="true">{esc(u)}</guid><description>{esc(title)}</description><category>{esc(cat)}</category><pubDate>{esc(pub)}</pubDate><enclosure url="{esc(image)}" type="image/jpeg" /></item>')
rss.append('</channel></rss>')
Path('feed.xml').write_text('\n'.join(rss) + '\n', encoding='utf-8')
print(f'تم إنشاء {len(urls)} صفحة خبر وتحديث sitemap.xml وfeed.xml')
