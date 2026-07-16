import logging
import json
import re
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import cloudscraper
from bs4 import BeautifulSoup
import time

logger = logging.getLogger(__name__)

# Basic keywords for images we want to skip
IGNORE_KEYWORDS = ['googleusercontent.com', 'gstatic.com', 'logo', 'icon', 'avatar', 'placeholder', 'blank', 'transparent', 'pixel', 'tracker', 'spinner']

class ImageExtractor:
    def __init__(self, timeout=10, max_workers=5):
        self.timeout = timeout
        self.max_workers = max_workers
        self.scraper = cloudscraper.create_scraper()

    def _normalize_url(self, base_url, img_url):
        if not img_url:
            return None
        # Handle protocol-relative
        if img_url.startswith('//'):
            img_url = 'https:' + img_url
        
        # Make absolute
        url = urljoin(base_url, img_url)
        
        # Ensure it's http/https
        parsed = urlparse(url)
        if parsed.scheme not in ('http', 'https'):
            return None
            
        return url

    def _is_valid_image(self, url):
        url_lower = url.lower()
        
        # Skip obvious bad words in URL
        for kw in IGNORE_KEYWORDS:
            if kw in url_lower:
                return False
                
        # Validate reachability and size
        try:
            # We use stream=True or just fetch headers. Some servers don't like HEAD.
            # Using GET with stream to get headers.
            resp = self.scraper.get(url, stream=True, timeout=self.timeout)
            if resp.status_code != 200:
                return False
                
            content_type = resp.headers.get('Content-Type', '')
            if not content_type.startswith('image/'):
                return False
                
            # If Content-Length is provided, we can skip tiny images (e.g. < 5KB)
            content_length = resp.headers.get('Content-Length')
            if content_length and int(content_length) < 5000:
                return False
                
            return True
        except Exception as e:
            logger.debug(f"Image validation failed for {url}: {e}")
            return False

    def _extract_from_json_ld(self, soup):
        for script in soup.find_all('script', type='application/ld+json'):
            if not script.string:
                continue
            try:
                data = json.loads(script.string)
                if isinstance(data, dict):
                    # Check for image property
                    img = data.get('image')
                    if isinstance(img, str):
                        return img
                    elif isinstance(img, list) and len(img) > 0 and isinstance(img[0], str):
                        return img[0]
                    elif isinstance(img, dict) and 'url' in img:
                        return img['url']
                    elif isinstance(img, list) and len(img) > 0 and isinstance(img[0], dict) and 'url' in img[0]:
                        return img[0]['url']
            except json.JSONDecodeError:
                pass
        return None

    def _extract_from_article_body(self, soup):
        # Look for the first reasonable image inside typical article containers
        article_containers = soup.find_all(['article', 'main', 'div'], class_=re.compile(r'content|article|post|body|story', re.I))
        
        candidates = []
        # If no specific containers, search whole body
        search_area = article_containers if article_containers else [soup]
        
        for container in search_area:
            for img in container.find_all('img'):
                # Check data-src, data-lazy-src, src
                src = img.get('data-src') or img.get('data-lazy-src') or img.get('data-original') or img.get('src')
                if not src:
                    continue
                    
                # Basic inline check for width/height attributes to prefer larger images
                width = img.get('width')
                height = img.get('height')
                
                # If width/height provided as strings, try to parse
                try:
                    w = int(re.sub(r'[^0-9]', '', str(width))) if width else 0
                    h = int(re.sub(r'[^0-9]', '', str(height))) if height else 0
                    
                    if w > 0 and h > 0 and (w < 300 or h < 300):
                        continue # Skip explicitly small images
                except Exception:
                    pass
                    
                candidates.append(src)
                
        return candidates

    def extract_image(self, article_url, html_content=None, feed_image_url=None):
        candidates = []
        
        if feed_image_url:
            candidates.append(self._normalize_url(article_url, feed_image_url))
            
        soup = None
        if not html_content:
            try:
                resp = self.scraper.get(article_url, timeout=self.timeout)
                if resp.status_code == 200:
                    html_content = resp.content
            except Exception as e:
                logger.warning(f"Failed to fetch {article_url} for image extraction: {e}")
        
        if html_content:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 1. Open Graph Image
            og_img = soup.find('meta', property='og:image')
            if og_img and og_img.get('content'):
                candidates.append(self._normalize_url(article_url, og_img['content']))
                
            # 2. Twitter Card Image
            tw_img = soup.find('meta', attrs={'name': 'twitter:image'})
            if tw_img and tw_img.get('content'):
                candidates.append(self._normalize_url(article_url, tw_img['content']))
                
            # 3. JSON-LD Schema
            ld_img = self._extract_from_json_ld(soup)
            if ld_img:
                candidates.append(self._normalize_url(article_url, ld_img))
                
            # 4-10. Body images
            body_images = self._extract_from_article_body(soup)
            for img in body_images:
                candidates.append(self._normalize_url(article_url, img))
                
        # Deduplicate while preserving order
        seen = set()
        unique_candidates = []
        for c in candidates:
            if c and c not in seen:
                seen.add(c)
                unique_candidates.append(c)
                
        # Validate candidates in parallel
        # Return the first valid one according to priority order
        valid_image = None
        
        if not unique_candidates:
            return None
            
        # Optimization: Try the top 3 high-priority candidates first before trying the rest
        # Often OG or Twitter image is valid.
        top_candidates = unique_candidates[:3]
        rest_candidates = unique_candidates[3:]
        
        for c in top_candidates:
            if self._is_valid_image(c):
                return c
                
        # If top 3 fail, use ThreadPool for the rest (can be many)
        if rest_candidates:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # We need to maintain priority order. 
                # Submit all, but process results according to original order.
                future_to_url = {executor.submit(self._is_valid_image, url): url for url in rest_candidates}
                
                # Wait for all to finish so we can check in original priority order
                # This ensures we prefer earlier candidates over later ones
                results = {}
                for future in as_completed(future_to_url):
                    url = future_to_url[future]
                    try:
                        results[url] = future.result()
                    except Exception:
                        results[url] = False
                        
                # Now check in order
                for c in rest_candidates:
                    if results.get(c):
                        return c
                        
        return None
