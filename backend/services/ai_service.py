# flake8: noqa: E501
import os
import json
import logging
import asyncio
import time
from dotenv import load_dotenv

from openai import OpenAI

load_dotenv()

logger = logging.getLogger(__name__)

NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")

if NVIDIA_API_KEY and NVIDIA_API_KEY != "your_nvidia_api_key_here":
    nvidia_client_available = True
else:
    nvidia_client_available = False
    logger.warning("NVIDIA_API_KEY not found. AI generation will use fallback.")

MODEL_NAME = "google/gemini-2.5-flash"

PROMPT_TEMPLATE = """
Act as an expert SEO Editor and News Analyst. Read the following news article title and content.
Your task is to EXTRACT facts from the original article and GENERATE COMPLETELY NEW AND UNIQUE CONTENT based on those facts. 
DO NOT just translate or copy the original sentences. DO NOT paraphrase the original content line-by-line. 
You must write a fresh, engaging, and professional news report with a unique structure and flow. Keep the language same as the original article (Hindi or English).

Generate a JSON response containing exactly these keys:
1. "content": The completely NEW and UNIQUE article text based on the facts (at least 3-4 paragraphs). It MUST NOT be similar to the original article in phrasing or structure.
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
    import re

    clean_title = re.sub(r"[^a-zA-Z0-9\u0900-\u097F]", "-", article_title.lower())
    return {
        "content": (
            f"**[AI Generation Failed]** Your NVIDIA API key might have exceeded its quota or is invalid. Falling back to original content:\n\n{article_content}"
            if article_content
            else "Content could not be generated at this time. API Error."
        ),
        "seo_title": article_title[:60],
        "meta_description": (
            (article_content[:150] + "...") if article_content else article_title
        ),
        "keywords": ["news", "update", "latest"],
        "slug": clean_title[:50],
        "category": "General",
        "summary": ["Generated via fallback."],
    }

def _parse_response(text: str) -> dict:
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return json.loads(text.strip())

class OpenRouterProvider:
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("NVIDIA_API_KEY")
        if self.api_key:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url="https://openrouter.ai/api/v1"
            )
        else:
            self.client = None

    def generate_sync(self, article_title: str, article_content: str) -> dict:
        if not self.client:
            return _fallback(article_title, article_content)

        prompt = PROMPT_TEMPLATE.format(title=article_title, content=article_content)

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    top_p=1,
                    max_tokens=2048,
                    stream=False
                )
                return _parse_response(response.choices[0].message.content)
            except Exception as e:
                logger.error(f"NVIDIA API error (attempt {attempt + 1}): {e}")
                err_str = str(e).lower()
                if "429" in err_str or "quota" in err_str or "rate limit" in err_str:
                    if attempt < max_retries - 1:
                        time.sleep(2**attempt)
                        continue
                return _fallback(article_title, article_content)
        
        return _fallback(article_title, article_content)

class AIService:
    def __init__(self):
        self.provider = OpenRouterProvider()

    def generate_seo_content_sync(self, article_title: str, article_content: str) -> dict:
        return self.provider.generate_sync(article_title, article_content)

    async def generate_seo_content(self, article_title: str, article_content: str) -> dict:
        return await asyncio.to_thread(self.generate_seo_content_sync, article_title, article_content)

ai_service = AIService()

def generate_seo_content_sync(article_title: str, article_content: str) -> dict:
    return ai_service.generate_seo_content_sync(article_title, article_content)

async def generate_seo_content(article_title: str, article_content: str) -> dict:
    return await ai_service.generate_seo_content(article_title, article_content)
