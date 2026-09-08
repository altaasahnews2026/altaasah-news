import json
from pathlib import Path
from urllib.request import urlopen, Request
from datetime import datetime, timezone

NEWS = Path('news.json')
IMAGE_DIR = Path('assets/editorial')
IMAGE_DIR.mkdir(parents=True, exist_ok=True)

KIRKUK_TITLE = 'مجلس محافظة كركوك يعقد جلسته الـ25 بحضور 15 عضواً لمناقشة عدد من الملفات بينها استضافة مديري شرطة المحافظة والبلدية'
KIRKUK_IMAGE = './assets/editorial/kirkuk-council-25-2026-09-08.jpg'
KIRKUK_URL = 'https://altaasahnews2026.github.io/altaasah-news/editorial/kirkuk-council-25-2026-09-08'
KIRKUK_PUBLISHED = '2026-09-08T13:11:00+03:00'
KIRKUK_IMAGE_URL = 'https://raw.githubusercontent.com/altaasahnews2026/altaasah-news/main/assets/editorial/kirkuk-council-25-2026-09-08.jpg'


def ensure_kirkuk_image():
    target = Path(KIRKUK_IMAGE)
    if target.exists() and target.stat().st_size > 1000:
        return
    req = Request(KIRKUK_IMAGE_URL, headers={'User-Agent': 'Mozilla/5.0'})
    with urlopen(req, timeout=30) as response:
        data = response.read()
    if not data.startswith(b'\xff\xd8'):
        raise RuntimeError('تعذر استعادة صورة خبر كركوك التحريري')
    target.write_bytes(data)


def main():
    ensure_kirkuk_image()
    data = json.loads(NEWS.read_text(encoding='utf-8')) if NEWS.exists() else {'updated_at': '', 'items': []}
    items = data.get('items') or []
    items = [item for item in items if item.get('title') != KIRKUK_TITLE]
    item = {
        'title': KIRKUK_TITLE,
        'url': KIRKUK_URL,
        'image': KIRKUK_IMAGE,
        'original_image': KIRKUK_IMAGE,
        'published': KIRKUK_PUBLISHED,
        'category': 'كركوك',
        'region': 'كركوك',
        'kirkuk': True,
        'breaking': False,
        'source_name': 'التاسعة نيوز',
        'summary': 'يعقد مجلس محافظة كركوك جلسته الـ25 بحضور 15 عضواً لمناقشة عدد من الملفات، بينها استضافة مديري شرطة المحافظة والبلدية لبحث الملفات المطروحة على جدول أعمال المجلس.'
    }
    items.insert(0, item)
    data['items'] = items
    data['updated_at'] = datetime.now(timezone.utc).isoformat()
    NEWS.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    print('تم نشر تحديث كركوك التحريري مع صورة المجلس، مع الإبقاء على الأخبار الحديثة التي جرى جلبها آلياً')


if __name__ == '__main__':
    main()
