import requests
import os
import feedparser

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
