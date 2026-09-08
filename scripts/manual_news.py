import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

NEWS = Path('news.json')
TITLE = 'مجلس محافظة كركوك يعقد جلسته الـ25 بحضور 15 عضواً لمناقشة عدد من الملفات بينها استضافة مديري شرطة المحافظة والبلدية'
IMAGE = './assets/editorial/kirkuk-council-25-2026-09-08.jpg'
URL = 'https://altaasahnews2026.github.io/altaasah-news/editorial/kirkuk-council-25-2026-09-08'
PUBLISHED = '2026-09-08T13:11:00+03:00'


def main():
    data = json.loads(NEWS.read_text(encoding='utf-8'))
    items = data.get('items', [])
    items = [x for x in items if x.get('title') != TITLE]
    item = {
        'title': TITLE,
        'url': URL,
        'image': IMAGE,
        'original_image': IMAGE,
        'published': PUBLISHED,
        'category': 'كركوك',
        'region': 'كركوك',
        'kirkuk': True,
        'breaking': False,
        'source_name': 'التاسعة نيوز',
        'summary': 'يعقد مجلس محافظة كركوك جلسته الـ25 بحضور 15 عضواً لمناقشة عدد من الملفات، بينها استضافة مديري شرطة المحافظة والبلدية لبحث الملفات المطروحة على جدول أعمال المجلس.'
    }
    data['items'] = [item] + items
    data['updated_at'] = datetime.now(timezone.utc).isoformat()
    NEWS.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    print('تم تثبيت الخبر التحريري: مجلس محافظة كركوك — الجلسة 25')


if __name__ == '__main__':
    main()
