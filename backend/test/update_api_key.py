#!/usr/bin/env python3
"""
Script to help update the DeepSeek API key
"""

import os
from pathlib import Path

def update_api_key():
    """Update the API key in .env file"""
    
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found!")
        return False
    
    print("🔍 Current .env file content:")
    with open(env_file, 'r') as f:
        content = f.read()
        print(content)
    
    print("\n" + "="*50)
    print("📝 To update your API key:")
    print("1. Open the .env file in a text editor")
    print("2. Find the line: DEEPSEEK_API_KEY=sk-d51fbf9b0fe1429f97d84b2831fd347f")
    print("3. Replace it with: DEEPSEEK_API_KEY=\"sk-your-new-key-here\"")
    print("4. Save the file")
    print("5. Run this script again to verify")
    print("="*50)
    
    return True

if __name__ == "__main__":
    update_api_key() 