"""
Utility to extract og:image / twitter:image from article URLs.
Used by all collectors to populate image_url field.
"""
import logging
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


def fetch_og_image(url: str, timeout: int = 5) -> str | None:
    """
    Fetches the og:image or twitter:image meta tag from an article URL.
    Returns the image URL string, or None if not found / on error.
    Fast: only downloads the <head> section using streaming.
    """
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout, stream=True)
        if resp.status_code != 200:
            return None

        # Read only first 50KB — enough to get <head>
        content = b""
        for chunk in resp.iter_content(chunk_size=4096):
            content += chunk
            if len(content) >= 50_000:
                break

        soup = BeautifulSoup(content, "html.parser")

        # Priority: og:image > twitter:image > first <img> in article
        for prop in ["og:image", "twitter:image", "og:image:secure_url"]:
            tag = soup.find("meta", property=prop) or soup.find("meta", attrs={"name": prop})
            if tag:
                img = tag.get("content", "").strip()
                if img and img.startswith("http"):
                    return img

        return None
    except Exception as e:
        logger.debug(f"Image fetch failed for {url}: {e}")
        return None


def extract_image_from_feed_entry(entry) -> str | None:
    """
    Tries to extract image from RSS feed entry metadata before scraping the page.
    Falls back to None so caller can try fetch_og_image.
    """
    # 1. media:content
    if hasattr(entry, "media_content") and entry.media_content:
        url = entry.media_content[0].get("url", "")
        if url and url.startswith("http"):
            return url

    # 2. media:thumbnail
    if hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
        url = entry.media_thumbnail[0].get("url", "")
        if url and url.startswith("http"):
            return url

    # 3. enclosures (podcasts/images)
    if hasattr(entry, "enclosures") and entry.enclosures:
        for enc in entry.enclosures:
            if "image" in enc.get("type", ""):
                url = enc.get("href", "") or enc.get("url", "")
                if url and url.startswith("http"):
                    return url

    # 4. img tag in summary/description
    for field in ["summary", "description", "content"]:
        text = ""
        if hasattr(entry, field):
            val = getattr(entry, field)
            if isinstance(val, list) and val:
                text = val[0].get("value", "")
            elif isinstance(val, str):
                text = val
        if text:
            soup = BeautifulSoup(text, "html.parser")
            img = soup.find("img")
            if img and img.get("src", "").startswith("http"):
                return img["src"]

    return None
