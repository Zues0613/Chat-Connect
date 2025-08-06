#!/usr/bin/env python3
"""
Test OAuth Configuration
This script tests if the OAuth configuration is properly set up.
"""

import os
from dotenv import load_dotenv

def test_oauth_config():
    """Test OAuth configuration"""
    print("🔧 Testing OAuth Configuration...")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Check required OAuth variables
    required_vars = [
        "GOOGLE_CLIENT_ID",
        "GOOGLE_CLIENT_SECRET", 
        "OAUTH_REDIRECT_URI",
        "FRONTEND_URL"
    ]
    
    missing_vars = []
    config_status = {}
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if "SECRET" in var or "KEY" in var:
                masked_value = value[:8] + "..." + value[-4:] if len(value) > 12 else "***"
                config_status[var] = masked_value
            else:
                config_status[var] = value
        else:
            missing_vars.append(var)
            config_status[var] = "❌ MISSING"
    
    # Display configuration status
    print("📋 OAuth Configuration Status:")
    for var, value in config_status.items():
        print(f"   {var}: {value}")
    
    print("\n" + "=" * 50)
    
    if missing_vars:
        print("❌ OAuth Configuration Issues:")
        for var in missing_vars:
            print(f"   - {var} is not set")
        print("\n🔧 To fix:")
        print("   1. Create a .env file in the backend directory")
        print("   2. Add the missing environment variables")
        print("   3. Get your Google Client Secret from Google Cloud Console")
        return False
    else:
        print("✅ OAuth Configuration is complete!")
        print("\n🎯 Next Steps:")
        print("   1. Start your backend server")
        print("   2. Start your frontend application")
        print("   3. Add a Gmail MCP server")
        print("   4. Test the OAuth flow")
        return True

def test_oauth_url_generation():
    """Test OAuth URL generation"""
    print("\n🔗 Testing OAuth URL Generation...")
    print("=" * 50)
    
    try:
        from app.services.oauth_service import oauth_service
        
        # Test OAuth URL generation
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        if client_id:
            print(f"✅ Google Client ID found: {client_id[:20]}...")
            
            # Test URL generation (without actual state)
            test_state = "test_state_123"
            oauth_url = oauth_service.generate_oauth_url("gmail", test_state)
            
            if oauth_url:
                print("✅ OAuth URL generation successful!")
                print(f"   Sample URL: {oauth_url[:100]}...")
            else:
                print("❌ OAuth URL generation failed")
                return False
        else:
            print("❌ Google Client ID not found")
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure you're running this from the backend directory")
        return False
    except Exception as e:
        print(f"❌ Error testing OAuth URL generation: {e}")
        return False
    
    return True

def main():
    """Main test function"""
    print("🚀 ChatConnect OAuth Configuration Test")
    print("=" * 50)
    
    # Test basic configuration
    config_ok = test_oauth_config()
    
    if config_ok:
        # Test OAuth URL generation
        url_ok = test_oauth_url_generation()
        
        if url_ok:
            print("\n🎉 All OAuth tests passed!")
            print("   Your OAuth configuration is ready to use.")
        else:
            print("\n⚠️ OAuth URL generation failed.")
            print("   Check your OAuth service configuration.")
    else:
        print("\n❌ OAuth configuration is incomplete.")
        print("   Please fix the missing environment variables.")

if __name__ == "__main__":
    main() 