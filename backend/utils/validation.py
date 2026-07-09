import re
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)

class DataValidator:
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """
        Checks if a string is a valid HTTP/HTTPS URL.
        """
        if not url:
            return False
        try:
            result = urlparse(url)
            return all([result.scheme in ['http', 'https'], result.netloc])
        except Exception:
            return False

    @staticmethod
    def is_valid_title(title: str, min_length: int = 5) -> bool:
        """
        Validates that a title is not empty, meets minimum length, and is not obvious spam.
        """
        if not title:
            return False
            
        title = title.strip()
        
        if len(title) < min_length:
            return False
            
        # Basic spam check (can be expanded)
        spam_keywords = ["viagra", "casino", "porn", "xxx"]
        title_lower = title.lower()
        if any(keyword in title_lower for keyword in spam_keywords):
            logger.warning(f"Spam keyword detected in title: {title}")
            return False
            
        return True

    @staticmethod
    def is_valid_content(content: str, min_length: int = 20) -> bool:
        """
        Validates that extracted content is substantial enough.
        """
        if not content:
            return False
            
        content = content.strip()
        
        # Check minimum length
        if len(content) < min_length:
            return False
            
        # Check for common paywall/blocking messages
        blocking_messages = [
            "error: article content is too short",
            "could not extract article content",
            "javascript is disabled",
            "please enable javascript",
            "you are using an adblocker"
        ]
        
        content_lower = content.lower()
        if any(msg in content_lower for msg in blocking_messages):
            return False
            
        return True
