#!/usr/bin/env python3
"""
Test script for chat endpoints to verify they're working correctly
Works with OTP-based authentication system
"""

import requests
import json
import time
from typing import Optional

class ChatEndpointTester:
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url
        self.token = None
        
    def login_with_otp(self, email: str, otp: str = None) -> bool:
        """Login using OTP system"""
        try:
            # For test@gmail.com, we can use a special bypass
            if email == "test@gmail.com":
                print(f"🔧 Using test email bypass for {email}")
                
                # Send OTP (this will be skipped for test email)
                send_response = requests.post(f"{self.base_url}/auth/send-otp", json={
                    "email": email
                })
                
                if send_response.status_code == 200:
                    print("✅ OTP request successful (test mode)")
                    
                    # For test email, use the special test OTP
                    test_otp = "000000"  # Test OTP from OTPManager
                    
                    verify_response = requests.post(f"{self.base_url}/auth/verify-otp", json={
                        "email": email,
                        "otp": test_otp
                    })
                    
                    if verify_response.status_code == 200:
                        data = verify_response.json()
                        self.token = data.get("access_token")
                        print(f"✅ Test login successful for {email}")
                        return True
                    else:
                        print(f"❌ Test OTP verification failed: {verify_response.status_code} - {verify_response.text}")
                        return False
                else:
                    print(f"❌ OTP send failed: {send_response.status_code} - {send_response.text}")
                    return False
            else:
                # For normal users, require OTP
                if not otp:
                    print(f"❌ OTP required for {email}")
                    return False
                
                print(f"🔐 Using OTP authentication for {email}")
                
                # Send OTP first
                send_response = requests.post(f"{self.base_url}/auth/send-otp", json={
                    "email": email
                })
                
                if send_response.status_code != 200:
                    print(f"❌ OTP send failed: {send_response.status_code} - {send_response.text}")
                    return False
                
                print("✅ OTP sent successfully")
                print("⚠️  Please check your email and enter the OTP")
                
                # Verify OTP
                verify_response = requests.post(f"{self.base_url}/auth/verify-otp", json={
                    "email": email,
                    "otp": otp
                })
                
                if verify_response.status_code == 200:
                    data = verify_response.json()
                    self.token = data.get("access_token")
                    print(f"✅ Login successful for {email}")
                    return True
                else:
                    print(f"❌ OTP verification failed: {verify_response.status_code} - {verify_response.text}")
                    return False
                
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False
    
    def get_headers(self) -> dict:
        """Get headers with auth token"""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def test_get_chats(self) -> bool:
        """Test getting chat list"""
        try:
            print("🔍 Testing GET /chat/chats...")
            start_time = time.time()
            
            response = requests.get(
                f"{self.base_url}/chat/chats",
                headers=self.get_headers(),
                timeout=10
            )
            
            duration = time.time() - start_time
            print(f"⏱️  Response time: {duration:.2f}s")
            
            if response.status_code == 200:
                chats = response.json()
                print(f"✅ Got {len(chats)} chats")
                return True
            else:
                print(f"❌ Failed: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            print("❌ Timeout - request took too long")
            return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def test_get_messages(self, chat_id: int) -> bool:
        """Test getting messages for a specific chat"""
        try:
            print(f"🔍 Testing GET /chat/chats/{chat_id}/messages...")
            start_time = time.time()
            
            response = requests.get(
                f"{self.base_url}/chat/chats/{chat_id}/messages",
                headers=self.get_headers(),
                timeout=10
            )
            
            duration = time.time() - start_time
            print(f"⏱️  Response time: {duration:.2f}s")
            
            if response.status_code == 200:
                messages = response.json()
                print(f"✅ Got {len(messages)} messages for chat {chat_id}")
                return True
            elif response.status_code == 404:
                print(f"⚠️  Chat {chat_id} not found")
                return True  # This is expected for non-existent chats
            else:
                print(f"❌ Failed: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            print("❌ Timeout - request took too long")
            return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def test_create_chat(self) -> Optional[int]:
        """Test creating a new chat"""
        try:
            print("🔍 Testing POST /chat/chats...")
            start_time = time.time()
            
            response = requests.post(
                f"{self.base_url}/chat/chats",
                headers=self.get_headers(),
                json={"title": f"Test Chat {int(time.time())}"},
                timeout=10
            )
            
            duration = time.time() - start_time
            print(f"⏱️  Response time: {duration:.2f}s")
            
            if response.status_code == 200:
                chat = response.json()
                chat_id = chat.get("id")
                print(f"✅ Created chat {chat_id}: {chat.get('title')}")
                return chat_id
            else:
                print(f"❌ Failed: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            print("❌ Timeout - request took too long")
            return None
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
    def run_all_tests(self, email: str, otp: str = None):
        """Run all tests"""
        print("🧪 Starting Chat Endpoint Tests...\n")
        
        # Test 1: Login with OTP
        if not self.login_with_otp(email, otp):
            print("❌ Cannot proceed without login")
            return
        
        print()
        
        # Test 2: Get chats
        if not self.test_get_chats():
            print("❌ Chat list test failed")
            return
        
        print()
        
        # Test 3: Create a test chat
        test_chat_id = self.test_create_chat()
        if test_chat_id is None:
            print("❌ Chat creation test failed")
            return
        
        print()
        
        # Test 4: Get messages for the test chat
        if not self.test_get_messages(test_chat_id):
            print("❌ Messages test failed")
            return
        
        print()
        
        # Test 5: Test with non-existent chat
        if not self.test_get_messages(99999):
            print("❌ Non-existent chat test failed")
            return
        
        print("\n🎉 All tests completed!")

def main():
    """Main function"""
    print("ChatConnect Chat Endpoint Tester (OTP Authentication)")
    print("=" * 55)
    
    # Get credentials
    email = input("Enter your email: ").strip()
    
    if not email:
        print("❌ Email is required")
        return
    
    # For test email, no OTP needed
    if email == "test@gmail.com":
        print("🔧 Using test email mode (no OTP required)")
        otp = None
    else:
        otp = input("Enter your OTP: ").strip()
        if not otp:
            print("❌ OTP is required for non-test emails")
            return
    
    # Run tests
    tester = ChatEndpointTester()
    tester.run_all_tests(email, otp)

if __name__ == "__main__":
    main() 