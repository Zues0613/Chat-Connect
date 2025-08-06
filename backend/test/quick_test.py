#!/usr/bin/env python3
"""
Quick test script for test@gmail.com (no user input required)
"""

import requests
import time
from typing import Optional

def quick_test():
    """Quick test using test@gmail.com"""
    base_url = "http://127.0.0.1:8000"
    email = "test@gmail.com"
    test_otp = "000000"
    
    print("🚀 Quick Test for test@gmail.com")
    print("=" * 40)
    
    try:
        # Step 1: Send OTP
        print("1. Sending OTP...")
        send_response = requests.post(f"{base_url}/auth/send-otp", json={
            "email": email
        })
        
        if send_response.status_code != 200:
            print(f"❌ OTP send failed: {send_response.status_code}")
            return False
        
        print("✅ OTP sent successfully")
        
        # Step 2: Verify OTP
        print("2. Verifying OTP...")
        verify_response = requests.post(f"{base_url}/auth/verify-otp", json={
            "email": email,
            "otp": test_otp
        })
        
        if verify_response.status_code != 200:
            print(f"❌ OTP verification failed: {verify_response.status_code}")
            return False
        
        token = verify_response.json().get("access_token")
        if not token:
            print("❌ No token received")
            return False
        
        print("✅ Login successful")
        
        # Step 3: Test chat endpoints
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        print("3. Testing chat list...")
        chats_response = requests.get(f"{base_url}/chat/chats", headers=headers, timeout=10)
        
        if chats_response.status_code == 200:
            chats = chats_response.json()
            print(f"✅ Got {len(chats)} chats")
            
            # Test messages for first chat if exists
            if chats:
                first_chat_id = chats[0]["id"]
                print(f"4. Testing messages for chat {first_chat_id}...")
                
                messages_response = requests.get(
                    f"{base_url}/chat/chats/{first_chat_id}/messages", 
                    headers=headers, 
                    timeout=10
                )
                
                if messages_response.status_code == 200:
                    messages = messages_response.json()
                    print(f"✅ Got {len(messages)} messages")
                else:
                    print(f"⚠️  Messages test failed: {messages_response.status_code}")
            else:
                print("4. No chats to test messages")
        else:
            print(f"❌ Chat list failed: {chats_response.status_code}")
            return False
        
        print("\n🎉 Quick test completed successfully!")
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend. Is the server running?")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = quick_test()
    exit(0 if success else 1) 