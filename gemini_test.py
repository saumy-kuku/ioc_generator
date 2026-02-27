import asyncio, os
from dotenv import load_dotenv
load_dotenv()
import google.generativeai as genai
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

async def test():
    model = genai.GenerativeModel('gemini-1.5-flash')
    r = await model.generate_content_async('Say hello in one sentence')
    print('Gemini OK:', r.text)

asyncio.run(test())