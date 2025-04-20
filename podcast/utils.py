import requests
import os
import feedparser
import httpx
from datetime import datetime

def download_audio(url: str, dest_path: str) -> str:
    """Download up to the first 10MB of audio file from a URL to dest_path."""
    response = requests.get(url, stream=True)
    max_bytes = 10 * 1024 * 1024  # 10MB
    written = 0
    with open(dest_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                if written + len(chunk) > max_bytes:
                    chunk = chunk[:max_bytes - written]
                f.write(chunk)
                written += len(chunk)
                if written >= max_bytes:
                    break
    return dest_path

def delete_file(path: str):
    """Delete a file if it exists."""
    if os.path.exists(path):
        os.remove(path)

async def fetch_podcast_episodes(feed_url: str):
    if not feed_url:
        return []
    parsed = feedparser.parse(feed_url)
    return parsed.entries

async def get_latest_episode_date_async(feed_url):
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(feed_url)
            if resp.status_code != 200:
                return None
            content = resp.content
        parsed = feedparser.parse(content)
        entries = parsed.entries
        if not entries:
            return None
        latest = max(
            entries,
            key=lambda e: e.get("published_parsed") or e.get("updated_parsed") or 0
        )
        dt = latest.get("published_parsed") or latest.get("updated_parsed")
        if dt:
            return datetime(*dt[:6])
    except Exception:
        pass
    return None
