import re
import html
# pyrefly: ignore [missing-import]
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

class DataCleaner:
    @staticmethod
    def strip_html_tags(text: str) -> str:
        """
        Removes HTML tags from a string using BeautifulSoup.
        """
        if not text:
            return ""
        try:
            # Parse HTML and extract text
            soup = BeautifulSoup(text, "html.parser")
            clean_text = soup.get_text(separator=" ")
            return clean_text
        except Exception as e:
            logger.warning(f"Error stripping HTML: {e}")
            # Fallback to simple regex
            clean_text = re.sub(r'<[^>]+>', ' ', text)
            return clean_text

    @staticmethod
    def normalize_whitespace(text: str) -> str:
        """
        Removes excessive whitespaces, tabs, and newlines.
        """
        if not text:
            return ""
        # Replace multiple spaces/newlines with a single space
        return re.sub(r'\s+', ' ', text).strip()

    @staticmethod
    def sanitize_text(text: str) -> str:
        """
        Full sanitization pipeline: 
        Unescapes HTML entities -> Strips tags -> Normalizes whitespace.
        """
        if not text:
            return ""
        text = html.unescape(text)
        text = DataCleaner.strip_html_tags(text)
        text = DataCleaner.normalize_whitespace(text)
        return text
