import json
from pathlib import Path
from PIL import Image

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
        path = Path(rel)
        valid = bool(image and original and image == original and path.is_file())
        if valid:
            try:
                with Image.open(path) as im:
                    valid = im.width >= 360 and im.height >= 220
            except Exception:
                valid = False
        if not valid:
            removed.append((item.get('title', ''), 'missing-or-invalid-image'))
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
    print(f'تنقية الصور: أبقيت {len(kept)} خبراً، حذفت {len(removed)} خبراً بصورة مفقودة/غير صالحة أو مكررة')


if __name__ == '__main__':
    main()
