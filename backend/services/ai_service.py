# flake8: noqa: E501
import os
import json
import logging
import asyncio
import time
from dotenv import load_dotenv

# pyrefly: ignore [missing-import]
from openai import OpenAI

load_dotenv(override=True)

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
CRITICAL RULE: DO NOT just translate, copy, or slightly paraphrase the original sentences. 
You must write a completely fresh, engaging, and professional news report with a unique structure and flow. 
Keep the language same as the original article (Hindi or English).

Generate a JSON response containing exactly these keys:
1. "title": An SEO optimized title (max 60 chars) that is different from original.
2. "summary": A short bullet-point summary of the key facts (2-3 bullet points).
3. "meta_description": A compelling meta description (max 160 chars).
4. "keywords": Array of 5-8 relevant keyword strings.
5. "slug": A URL friendly slug in English based on the new title.
6. "category": The single most relevant news category.
7. "tags": Array of 3-5 relevant tags.
8. "rewritten_article": The completely NEW and UNIQUE article text based on the facts (at least 3-4 paragraphs). It MUST NOT be similar to the original article.

Article Title: {title}
Article Content: {content}
"""

def _fallback(article_title: str, article_content: str) -> dict:
    import re

    clean_title = re.sub(r"[^a-zA-Z0-9\u0900-\u097F]", "-", article_title.lower())
    return {
        "rewritten_article": (
            f"**[AI Generation Failed]** Content could not be generated cleanly. Falling back to original content:\n\n{article_content}"
            if article_content
            else "Content could not be generated at this time. API Error."
        ),
        "title": article_title[:60],
        "meta_description": (
            (article_content[:150] + "...") if article_content else article_title
        ),
        "keywords": ["news", "update", "latest"],
        "slug": clean_title[:50],
        "category": "General",
        "tags": ["news"],
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

class GeminiProvider:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={self.api_key}"

    def generate_sync(self, article_title: str, article_content: str) -> dict:
        if not self.api_key:
            return _fallback(article_title, article_content)

        prompt = PROMPT_TEMPLATE.format(title=article_title, content=article_content)
        
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 2048,
                "response_mime_type": "application/json",
            }
        }
        
        import requests
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.post(self.url, json=payload)
                if response.status_code == 200:
                    data = response.json()
                    text = data["candidates"][0]["content"]["parts"][0]["text"]
                    return _parse_response(text)
                else:
                    logger.error(f"Gemini API error (attempt {attempt + 1}): {response.text}")
                    if response.status_code in [429, 500, 503] and attempt < max_retries - 1:
                        time.sleep(2**attempt)
                        continue
                    return _fallback(article_title, article_content)
            except Exception as e:
                logger.error(f"Gemini API exception (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2**attempt)
                    continue
                return _fallback(article_title, article_content)
        return _fallback(article_title, article_content)

class AIService:
    def __init__(self):
        if os.getenv("GEMINI_API_KEY"):
            self.provider = GeminiProvider()
        else:
            self.provider = OpenRouterProvider()

    def generate_seo_content_sync(self, article_title: str, article_content: str) -> dict:
        if os.getenv("GEMINI_API_KEY"):
            result = self.provider.generate_sync(article_title, article_content)
            # If Gemini fails and returns fallback, try OpenRouter if available
            if "**[AI Generation Failed]**" in result.get("rewritten_article", "") and os.getenv("OPENROUTER_API_KEY"):
                fallback_provider = OpenRouterProvider()
                result = fallback_provider.generate_sync(article_title, article_content)
            return result
        else:
            return self.provider.generate_sync(article_title, article_content)

    async def generate_seo_content(self, article_title: str, article_content: str) -> dict:
        return await asyncio.to_thread(self.generate_seo_content_sync, article_title, article_content)

ai_service = AIService()

def generate_seo_content_sync(article_title: str, article_content: str) -> dict:
    return ai_service.generate_seo_content_sync(article_title, article_content)

async def generate_seo_content(article_title: str, article_content: str) -> dict:
    return await ai_service.generate_seo_content(article_title, article_content)
