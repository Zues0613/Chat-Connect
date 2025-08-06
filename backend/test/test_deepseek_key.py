#!/usr/bin/env python3
"""
Simple DeepSeek API key test (supports both DeepSeek and OpenRouter)
"""

import os
import asyncio
import sys
from dotenv import load_dotenv
import openai

# Add the parent directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

load_dotenv()

async def test_deepseek_key():
    """Test DeepSeek API key (supports both DeepSeek and OpenRouter)"""
    try:
        # Get API key
        api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("DEFAULT_DEEPSEEK_API_KEY")
        if not api_key:
            print("❌ No API key found")
            return False

        print(f"🔑 Testing API key: {api_key[:10]}...{api_key[-4:]}")

        # Determine if using OpenRouter or direct DeepSeek API
        if api_key.startswith("sk-or-v1-"):
            # OpenRouter API
            base_url = "https://openrouter.ai/api/v1"
            model = "openai/gpt-3.5-turbo"  # Basic model that should work
            print("🌐 Using OpenRouter API")
        else:
            # Direct DeepSeek API
            base_url = "https://api.deepseek.com"
            model = "deepseek-reasoner"
            print("🌐 Using direct DeepSeek API")

        # Initialize client
        client = openai.AsyncOpenAI(
            api_key=api_key,
            base_url=base_url
        )

        # Test with a simple request
        print("🧠 Testing API connection...")

        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": "Hello, this is a test message."}
            ],
            max_tokens=50
        )

        print("✅ API key is working!")
        print(f"Response: {response.choices[0].message.content}")
        return True

    except Exception as e:
        print(f"❌ API key test failed: {e}")

        # Provide specific guidance based on error
        if "401" in str(e) or "authentication" in str(e).lower():
            print("\n🔧 This looks like an authentication issue:")
            if api_key.startswith("sk-or-v1-"):
                print("   - Your OpenRouter API key might be expired")
                print("   - You might need to get a new key from https://openrouter.ai/")
            else:
                print("   - Your DeepSeek API key might be expired")
                print("   - You might need to get a new key from https://platform.deepseek.com/")
            print("   - Check if your account is verified")
        elif "quota" in str(e).lower() or "limit" in str(e).lower():
            print("\n🔧 This looks like a quota/limit issue:")
            if api_key.startswith("sk-or-v1-"):
                print("   - You might have hit your OpenRouter usage limits")
                print("   - Check your account usage at https://openrouter.ai/")
            else:
                print("   - You might have hit your DeepSeek usage limits")
                print("   - Check your account usage at https://platform.deepseek.com/")
        elif "404" in str(e):
            print("\n🔧 This looks like an endpoint issue:")
            print("   - The API endpoint might have changed")
            print("   - Check the latest documentation")
        elif "402" in str(e) or "balance" in str(e).lower():
            print("\n🔧 This looks like a balance/credit issue:")
            if api_key.startswith("sk-or-v1-"):
                print("   - You need to add credits to your OpenRouter account")
                print("   - Visit https://openrouter.ai/ to add funds")
            else:
                print("   - You need to add credits to your DeepSeek account")
                print("   - Visit https://platform.deepseek.com/ to add funds")

        return False

if __name__ == "__main__":
    success = asyncio.run(test_deepseek_key())
    if success:
        print("\n🎉 Your API key is working! ChatConnect is ready to go!")
    else:
        print("\n⚠️ Please fix the API key issue before using ChatConnect") 