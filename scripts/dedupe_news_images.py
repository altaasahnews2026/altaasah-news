import json
from pathlib import Path

NEWS = Path('news.json')

def main():
    data = json.loads(NEWS.read_text(encoding='utf-8'))
    items = data.get('items', [])
    seen_images = set()
    kept = []
    removed = []
    for item in items:
        image = str(item.get('image') or '').strip()
        original = str(item.get('original_image') or '').strip()
        rel = image.replace('./', '', 1)
        valid = image and original and image == original and Path(rel).is_file()
        if not valid:
            removed.append((item.get('title', ''), 'missing-or-mismatched-image'))
            continue
        if image in seen_images:
            removed.append((item.get('title', ''), 'duplicate-image'))
            continue
        seen_images.add(image)
        kept.append(item)
    if len(kept) < 20:
        raise SystemExit(f'صور الأخبار الفريدة غير كافية بعد التنقية: {len(kept)}')
    data['items'] = kept
    NEWS.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'تنقية الصور: أبقيت {len(kept)} خبراً، حذفت {len(removed)} خبراً مكرراً/مكسور الصورة')

if __name__ == '__main__':
    main()
