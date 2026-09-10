from pathlib import Path
from datetime import datetime, timezone
import json

NEWS = Path('news.json')
ITEM = {
    'title': 'النائب محمد النعيمي: 7300 عقد ضاعت على كركوك وعقود صلاح الدين كذلك',
    'url': 'https://altaasahnews2026.github.io/altaasah-news/news/naimi-kirkuk-video.html',
    'category': 'محليات',
    'region': 'العراق',
    'published': datetime.now(timezone.utc).isoformat(),
    'image': './assets/editorial/naimi-kirkuk.svg',
    'original_image': './assets/editorial/naimi-kirkuk.svg',
    'source_url': '',
    'source_name': 'التاسعة نيوز',
    'breaking': False,
    'kirkuk': True,
    'report': True,
    'summary': 'قال النائب محمد النعيمي إن 7300 عقد مرتبطة بمحافظة كركوك ضاعت، مشيراً كذلك إلى عقود في صلاح الدين، وداعياً إلى توضيح مصير هذه العقود ومتابعة الملف.',
    'video_url': ''
}

data = json.loads(NEWS.read_text(encoding='utf-8'))
items = data.get('items', [])
items = [x for x in items if x.get('title') != ITEM['title']]
# إبقاء الخبر منشوراً ضمن الأخبار، لكن عدم وضعه في مقدمة الواجهة الرئيسية.
items.append(ITEM)
data['items'] = items
NEWS.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
print('تم إبقاء الخبر ضمن الأخبار وإزالته من مقدمة الواجهة الرئيسية')
