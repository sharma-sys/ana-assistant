import os
import json
import logging
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv
# pyrefly: ignore [missing-import]
import google.generativeai as genai

load_dotenv()

logger = logging.getLogger(__name__)

api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

def generate_seo_content_sync(article_title: str, article_content: str):
    """
    Calls Gemini API to generate SEO metadata and a summary synchronously.
    """
    if not api_key or api_key == "your_gemini_api_key_here":
        import re
        clean_title = re.sub(r'[^a-zA-Z0-9\u0900-\u097F]', '-', article_title.lower())
        return {
            "content": article_content,
            "seo_title": article_title[:60],
            "meta_description": article_content[:150] + "..." if article_content else article_title,
            "keywords": ["news", "latest update"],
            "slug": clean_title[:50],
            "category": "General",
            "summary": article_content[:300] + "..." if article_content else article_title
        }
        
    prompt = f"""
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
    
    Article Title: {article_title}
    Article Content: {article_content}
    
    Return ONLY valid JSON. Do not include markdown formatting or backticks.
    """
    
    try:
        model = genai.GenerativeModel('gemini-2.5-flash', generation_config={"response_mime_type": "application/json"})
        response = model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
            
        result = json.loads(text.strip())
        return result
    except Exception as e:
        logger.error(f"Error generating AI content: {e}")
        import re
        clean_title = re.sub(r'[^a-zA-Z0-9\u0900-\u097F]', '-', article_title.lower())
        return {
            "content": article_content if article_content else "Content could not be generated at this time.",
            "seo_title": article_title[:60],
            "meta_description": (article_content[:150] + "...") if article_content else article_title,
            "keywords": ["news", "update", "latest"],
            "slug": clean_title[:50],
            "category": "General",
            "summary": (article_content[:300] + "...") if article_content else article_title
        }

async def generate_seo_content(article_title: str, article_content: str):
    """
    Calls Gemini API to generate SEO metadata and a summary.
    """
    if not api_key or api_key == "your_gemini_api_key_here":
        import re
        clean_title = re.sub(r'[^a-zA-Z0-9\u0900-\u097F]', '-', article_title.lower())
        return {
            "content": article_content,
            "seo_title": article_title[:60],
            "meta_description": article_content[:150] + "..." if article_content else article_title,
            "keywords": ["news", "latest update"],
            "slug": clean_title[:50],
            "category": "General",
            "summary": article_content[:300] + "..." if article_content else article_title
        }
        
    prompt = f"""
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
    
    Article Title: {article_title}
    Article Content: {article_content}
    
    Return ONLY valid JSON. Do not include markdown formatting or backticks.
    """
    
    try:
        model = genai.GenerativeModel('gemini-2.5-flash', generation_config={"response_mime_type": "application/json"})
        response = await model.generate_content_async(prompt)
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
            
        result = json.loads(text.strip())
        return result
    except Exception as e:
        logger.error(f"Error generating AI content: {e}")
        import re
        clean_title = re.sub(r'[^a-zA-Z0-9\u0900-\u097F]', '-', article_title.lower())
        return {
            "content": article_content if article_content else "Content could not be generated at this time.",
            "seo_title": article_title[:60],
            "meta_description": (article_content[:150] + "...") if article_content else article_title,
            "keywords": ["news", "update", "latest"],
            "slug": clean_title[:50],
            "category": "General",
            "summary": (article_content[:300] + "...") if article_content else article_title
        }
