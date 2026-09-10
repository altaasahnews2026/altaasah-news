import hashlib
import json
from pathlib import Path
from PIL import Image

NEWS = Path('news.json')
NEWS_ROOT = Path('assets/news')
MIN_W, MIN_H = 360, 220


def image_fingerprint(path: Path):
    try:
        raw = path.read_bytes()
        with Image.open(path) as im:
            im.verify()
        return hashlib.sha256(raw).hexdigest()
    except Exception:
        return None


def main():
    data = json.loads(NEWS.read_text(encoding='utf-8'))
    items = data.get('items', [])
    seen_paths = set()
    seen_hashes = set()
    kept = []
    removed = []

    for item in items:
        image = str(item.get('image') or '').strip()
        original = str(item.get('original_image') or '').strip()
        rel = image[2:] if image.startswith('./') else image
        path = Path(rel)

        # Root cause guard: only same-origin raw publisher images from assets/news
        # are allowed in the news feed. Editorial/template images must never enter.
        valid = (
            image.startswith('./assets/news/')
            and original == image
            and path.is_file()
            and path.parent == NEWS_ROOT
        )
        if valid:
            try:
                with Image.open(path) as im:
                    valid = im.width >= MIN_W and im.height >= MIN_H and im.format not in ('SVG',)
            except Exception:
                valid = False

        if not valid:
            removed.append((item.get('title', ''), 'missing-invalid-or-non-news-image'))
            continue

        fingerprint = image_fingerprint(path)
        if not fingerprint:
            removed.append((item.get('title', ''), 'unreadable-image'))
            continue

        if image in seen_paths or fingerprint in seen_hashes:
            removed.append((item.get('title', ''), 'duplicate-image-content'))
            continue

        seen_paths.add(image)
        seen_hashes.add(fingerprint)
        kept.append(item)

    if len(kept) < 20:
        raise SystemExit(f'صور الأخبار الفريدة غير كافية بعد التنقية: {len(kept)}')

    data['items'] = kept
    NEWS.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'تنقية الصور: أبقيت {len(kept)} خبراً، حذفت {len(removed)} خبراً بصورة مفقودة/غير صالحة/تحريرية أو مكررة')


if __name__ == '__main__':
    main()
