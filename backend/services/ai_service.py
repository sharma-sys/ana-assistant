import os
import json
import logging
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv
from openai import OpenAI, AsyncOpenAI

load_dotenv()

logger = logging.getLogger(__name__)

api_key = os.getenv("NVIDIA_API_KEY")
client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=api_key) if api_key else None
async_client = AsyncOpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=api_key) if api_key else None

MODEL = "meta/llama-3.1-70b-instruct"

PROMPT_TEMPLATE = """
Act as an expert SEO Editor and News Analyst. Read the following news article title and content.
Your task is to REWRITE the article completely in your own words. DO NOT copy the original content. Make it unique, engaging, and professional. Keep the language same as the original article (Hindi or English).

Generate a JSON response containing exactly these keys:
1. "content": The completely REWRITTEN and unique article text (at least 3-4 paragraphs).
2. "seo_title": An SEO optimized title (max 60 chars) that is different from original.
3. "meta_description": A compelling meta description (max 160 chars).
4. "keywords": Array of 5-8 relevant keyword strings.
5. "slug": A URL friendly slug in English based on the new title.
6. "category": The single most relevant news category (e.g., Politics, Sports, Business, Technology, Crime).
7. "summary": A short bullet-point summary of the key facts (2-3 bullet points).

Article Title: {title}
Article Content: {content}

Return ONLY valid JSON. Do not include markdown formatting or backticks.
"""


def _fallback(article_title: str, article_content: str) -> dict:
    """Return basic metadata when AI is unavailable (non-quota errors)."""
    import re
    clean_title = re.sub(r'[^a-zA-Z0-9\u0900-\u097F]', '-', article_title.lower())
    return {
        "content": article_content if article_content else "Content could not be generated at this time.",
        "seo_title": article_title[:60],
        "meta_description": (article_content[:150] + "...") if article_content else article_title,
        "keywords": ["news", "update", "latest"],
        "slug": clean_title[:50],
        "category": "General",
        "summary": (article_content[:300] + "...") if article_content else article_title,
    }


def _is_quota_error(e: Exception) -> bool:
    err_str = str(e).lower()
    return "429" in err_str or "quota" in err_str or "resourceexhausted" in type(e).__name__.lower()


def _parse_response(text: str) -> dict:
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return json.loads(text.strip())


def generate_seo_content_sync(article_title: str, article_content: str) -> dict:
    """
    Calls Gemini API synchronously to generate SEO metadata and a summary.
    Implements exponential backoff for quota errors.
    """
    import time
    if not client:
        return _fallback(article_title, article_content)

    prompt = PROMPT_TEMPLATE.format(title=article_title, content=article_content)

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}]
            )
            return _parse_response(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"Error generating AI content (sync, attempt {attempt + 1}): {e}")
            if _is_quota_error(e):
                if attempt < max_retries - 1:
                    time.sleep(3 ** attempt)  # 1s, 3s, 9s...
                    continue
                logger.warning(f"Rate limit exhausted after {max_retries} attempts, using fallback.")
                return _fallback(article_title, article_content)
            return _fallback(article_title, article_content)


async def generate_seo_content(article_title: str, article_content: str) -> dict:
    """
    Calls Gemini API asynchronously to generate SEO metadata and a summary.
    Implements exponential backoff for quota errors.
    """
    import asyncio
    if not client:
        return _fallback(article_title, article_content)

    prompt = PROMPT_TEMPLATE.format(title=article_title, content=article_content)

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = await async_client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}]
            )
            return _parse_response(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"Error generating AI content (async, attempt {attempt + 1}): {e}")
            if _is_quota_error(e):
                if attempt < max_retries - 1:
                    await asyncio.sleep(3 ** attempt)
                    continue
                logger.warning(f"Rate limit exhausted after {max_retries} attempts, using fallback.")
                return _fallback(article_title, article_content)
            return _fallback(article_title, article_content)
