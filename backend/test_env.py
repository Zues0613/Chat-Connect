#!/usr/bin/env python3
"""
Quick test to verify environment variables are loaded correctly
Run this from the backend directory: python test_env.py
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_env_vars():
    print("🔍 Environment Variables Test\n")
    
    # Check required variables
    required_vars = [
        "DATABASE_URL",
        "JWT_SECRET",
        "DEFAULT_DEEPSEEK_API_KEY"
    ]
    
    all_good = True
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if "SECRET" in var or "KEY" in var:
                masked = value[:6] + "..." + value[-4:] if len(value) > 10 else "***"
                print(f"✅ {var}: {masked}")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: NOT SET")
            all_good = False
    
    print("\n" + "="*50)
    if all_good:
        print("🎉 All required environment variables are set!")
        print("✅ Your backend should work correctly with the default DeepSeek API key.")
    else:
        print("⚠️  Some required environment variables are missing.")
        print("📝 Please check your .env file in the backend directory.")
    
    print("\n💡 Test with: python test_env.py")

if __name__ == "__main__":
    test_env_vars() 