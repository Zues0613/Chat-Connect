#!/usr/bin/env python3
"""
Test OpenRouter API connection for DeepSeek R1
Run this from the backend directory: python test_deepseek.py
"""

import os
import asyncio
from dotenv import load_dotenv
import openai

load_dotenv()

async def test_openrouter_api():
    print("🔍 Testing OpenRouter API Connection for DeepSeek R1\n")
    
    # Get API key
    api_key = os.getenv("DEFAULT_DEEPSEEK_API_KEY")
    if not api_key:
        print("❌ DEFAULT_DEEPSEEK_API_KEY not found in .env")
        return
    
    print(f"✅ API Key found: {api_key[:10]}...{api_key[-4:]}")
    
    try:
        # Initialize OpenAI client with OpenRouter base URL
        client = openai.AsyncOpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1"
        )
        
        print("✅ OpenAI client initialized with OpenRouter base URL")
        
        # Test a simple request
        print("🔄 Testing API connection...")
        
        response = await client.chat.completions.create(
            model="deepseek/deepseek-r1-0528",
            messages=[
                {"role": "user", "content": "Hello! Please respond with just 'Test successful' if you can see this message."}
            ],
            max_tokens=50,
            extra_headers={
                "HTTP-Referer": "http://localhost:3000",
                "X-Title": "VeeChat AI Assistant",
            }
        )
        
        content = response.choices[0].message.content
        print(f"✅ API Response: {content}")
        print("\n🎉 OpenRouter API connection successful!")
        
    except Exception as e:
        print(f"❌ API Error: {e}")
        print(f"\nError type: {type(e).__name__}")
        
        # Check if it's an authentication error
        if "401" in str(e) or "authentication" in str(e).lower():
            print("\n🔍 This appears to be an authentication issue.")
            print("Possible causes:")
            print("1. OpenRouter API key is invalid or expired")
            print("2. API key format is incorrect")
            print("3. Account has no credits or is suspended")
            print("\n💡 Try:")
            print("- Check your OpenRouter account status")
            print("- Generate a new API key from openrouter.ai")
            print("- Verify the API key format")
            print("- Make sure you have credits in your OpenRouter account")

if __name__ == "__main__":
    asyncio.run(test_openrouter_api()) 