"""Deprecated manual-news injector.

The news pipeline must publish only freshly fetched items with source images.
This script is intentionally a no-op so a stale editorial card/image cannot
re-enter news.json and break the image freshness/uniqueness guarantees.
"""
from pathlib import Path


def main():
    if not Path('news.json').exists():
        raise SystemExit('news.json غير موجود')
    print('تم تجاوز الإدراج التحريري اليدوي: الأخبار والصور تُجلب من المصادر الحديثة فقط')


if __name__ == '__main__':
    main()
