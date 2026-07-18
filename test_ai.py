import asyncio
import os
import sys

# Add backend to path so we can import services
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))

# pyrefly: ignore [missing-import]
from services.ai_service import ai_service

async def main():
    res = await ai_service.generate_seo_content("Wrestling Olympic News", "This is a short news about wrestling. The player won a medal today in Paris. He was very happy.")
    print("Result:")
    import pprint
    pprint.pprint(res)

asyncio.run(main())
