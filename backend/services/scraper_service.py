# pyrefly: ignore [missing-import]
import trafilatura
import logging
import time
import random
import threading
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Global rate limiting state
domain_locks = {}
global_lock = threading.Lock()

def _get_domain_lock(domain: str):
    with global_lock:
        if domain not in domain_locks:
            domain_locks[domain] = {"lock": threading.Lock(), "last_request": 0.0}
        return domain_locks[domain]

def _enforce_rate_limit(url: str):
    try:
        domain = urlparse(url).netloc
        if not domain:
            return
            
        domain_state = _get_domain_lock(domain)
        
        with domain_state["lock"]:
            now = time.time()
            time_since_last = now - domain_state["last_request"]
            # Enforce minimum 2 seconds + random jitter up to 1.5s
            min_delay = 2.0 + random.uniform(0.1, 1.5)
            
            if time_since_last < min_delay:
                sleep_time = min_delay - time_since_last
                time.sleep(sleep_time)
                
            domain_state["last_request"] = time.time()
    except Exception as e:
        logger.error(f"Rate limiting error for {url}: {e}")

def extract_article_content(url: str) -> str:
    """
    Downloads and extracts the main text content from a given news article URL.
    Returns the extracted text or a fallback string on failure.
    """
    _enforce_rate_limit(url)
    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            # Extract main text, omitting comments and navigation
            text = trafilatura.extract(downloaded, include_comments=False, include_tables=False)
            if text:
                if len(text) < 150:
                    logger.warning(f"Extracted content too short, likely paywall or blocking for {url}")
                    return "Error: Article content is too short to summarize. It may be behind a paywall or cookie banner."
                return text
        
        logger.warning(f"Failed to extract content from {url}")
        return "Could not extract article content. The content might be behind a paywall or the site blocks scrapers."
    except Exception as e:
        logger.error(f"Error scraping {url}: {e}")
        return f"Error scraping article content: {str(e)}"
