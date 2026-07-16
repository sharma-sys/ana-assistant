import os
from dotenv import load_dotenv
# pyrefly: ignore [missing-import]
from openai import OpenAI
load_dotenv('backend/.env')
client = OpenAI(api_key=os.getenv('OPENROUTER_API_KEY'), base_url='https://openrouter.ai/api/v1')
try:
    response = client.chat.completions.create(model='google/gemini-2.5-flash', messages=[{'role': 'user', 'content': 'test'}], max_tokens=10)
    print("SUCCESS:", response.choices[0].message.content)
except Exception as e:
    print("ERROR:", type(e), str(e))
