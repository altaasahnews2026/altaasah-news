#!/usr/bin/env python3
"""Publish fresh التاسعة نيوز stories to Instagram and TikTok.

Credentials are supplied only through GitHub Actions secrets/environment variables.
No AI branding, watermark, overlay, or AI-generated label is added to published media.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path
from urllib.parse import quote

import requests

ROOT = Path(__file__).resolve().parents[1]
NEWS_FILE = ROOT / "news.json"
STATE_FILE = ROOT / "social_state.json"
PAGES_BASE = os.getenv("SOCIAL_PUBLIC_BASE_URL", "https://altaasahnews2026.github.io/altaasah-news").rstrip("/")
MAX_POSTS_PER_RUN = int(os.getenv("SOCIAL_MAX_POSTS_PER_RUN", "3"))


def load_json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save_json(path: Path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def story_id(item: dict) -> str:
    raw = f"{item.get('url','')}|{item.get('title','')}|{item.get('published','')}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def public_image_url(item: dict) -> str:
    image = str(item.get("image") or "").lstrip("./")
    return f"{PAGES_BASE}/{quote(image, safe='/')}"


def caption(item: dict) -> str:
    title = " ".join(str(item.get("title") or "").split())
    source = str(item.get("source_name") or "التاسعة نيوز").strip()
    url = str(item.get("url") or "").strip()
    return f"{title}\n\nالمصدر: {source}\nالتفاصيل: {url}\n\n#التاسعة_نيوز #نعلم_لتعلم"


def post_instagram(item: dict, access_token: str, ig_user_id: str) -> str:
    image_url = public_image_url(item)
    cap = caption(item)
    base = f"https://graph.facebook.com/v24.0/{ig_user_id}/media"
    r = requests.post(base, data={"image_url": image_url, "caption": cap, "access_token": access_token}, timeout=45)
    r.raise_for_status()
    creation_id = r.json().get("id")
    if not creation_id:
        raise RuntimeError(f"Instagram media creation failed: {r.text[:500]}")
    time.sleep(2)
    r2 = requests.post(
        f"https://graph.facebook.com/v24.0/{ig_user_id}/media_publish",
        data={"creation_id": creation_id, "access_token": access_token},
        timeout=45,
    )
    r2.raise_for_status()
    published_id = r2.json().get("id")
    if not published_id:
        raise RuntimeError(f"Instagram publish failed: {r2.text[:500]}")
    return published_id


def tiktok_creator_info(access_token: str) -> dict:
    r = requests.post(
        "https://open.tiktokapis.com/v2/post/publish/creator_info/query/",
        headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json; charset=UTF-8"},
        timeout=45,
    )
    r.raise_for_status()
    data = r.json()
    if data.get("error", {}).get("code") not in (None, "ok"):
        raise RuntimeError(f"TikTok creator info failed: {data}")
    return data.get("data", {})


def post_tiktok_photo(item: dict, access_token: str) -> str:
    image_url = public_image_url(item)
    title = " ".join(str(item.get("title") or "").split())
    creator = tiktok_creator_info(access_token)
    privacy_options = creator.get("privacy_level_options") or []
    requested_privacy = os.getenv("TIKTOK_PRIVACY", "PUBLIC_TO_EVERYONE")
    privacy = requested_privacy if requested_privacy in privacy_options else (privacy_options[0] if privacy_options else requested_privacy)
    payload = {
        "post_info": {
            "title": title[:2200],
            "description": caption(item)[:2200],
            "privacy_level": privacy,
            "disable_comment": False,
            "auto_add_music": False,
        },
        "source_info": {
            "source": "PULL_FROM_URL",
            "photo_images": [image_url],
            "photo_cover_index": 0,
        },
        "post_mode": "DIRECT_POST",
        "media_type": "PHOTO",
    }
    r = requests.post(
        "https://open.tiktokapis.com/v2/post/publish/content/init/",
        headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json; charset=UTF-8"},
        json=payload,
        timeout=45,
    )
    r.raise_for_status()
    data = r.json()
    if data.get("error", {}).get("code") not in (None, "ok"):
        raise RuntimeError(f"TikTok publish failed: {data}")
    publish_id = data.get("data", {}).get("publish_id")
    if not publish_id:
        raise RuntimeError(f"TikTok publish failed: {data}")
    return publish_id


def main() -> int:
    news = load_json(NEWS_FILE, {"items": []})
    items = news.get("items", [])
    state = load_json(STATE_FILE, {"posted": {}})
    posted = state.setdefault("posted", {})

    ig_token = os.getenv("INSTAGRAM_ACCESS_TOKEN", "").strip()
    ig_user = os.getenv("INSTAGRAM_USER_ID", "").strip()
    tt_token = os.getenv("TIKTOK_ACCESS_TOKEN", "").strip()

    if not ig_token and not tt_token:
        print("SOCIAL: لا توجد مفاتيح نشر؛ تم تجاوز النشر بأمان.")
        save_json(STATE_FILE, state)
        return 0

    fresh = []
    for item in items:
        sid = story_id(item)
        if not item.get("image") or sid in posted:
            continue
        fresh.append((sid, item))
    fresh = fresh[:MAX_POSTS_PER_RUN]

    for sid, item in fresh:
        record = posted.setdefault(sid, {"title": item.get("title", ""), "url": item.get("url", "")})
        if ig_token and ig_user and not record.get("instagram"):
            try:
                record["instagram"] = post_instagram(item, ig_token, ig_user)
                print("Instagram OK:", item.get("title"))
            except Exception as exc:
                print("Instagram ERROR:", exc, file=sys.stderr)
        if tt_token and not record.get("tiktok"):
            try:
                record["tiktok"] = post_tiktok_photo(item, tt_token)
                print("TikTok OK:", item.get("title"))
            except Exception as exc:
                print("TikTok ERROR:", exc, file=sys.stderr)
        record["attempted_at"] = int(time.time())
        save_json(STATE_FILE, state)

    print("SOCIAL DONE:", len(fresh), "stories checked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
