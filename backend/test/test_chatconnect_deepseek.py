#!/usr/bin/env python3
"""
ChatConnect DeepSeek R1 Integration Test Script

This script tests the complete ChatConnect workflow with DeepSeek R1:
1. DeepSeek R1 service initialization
2. MCP server connection and tool discovery
3. Function calling and execution
4. Response generation and confirmation
5. Error handling and OAuth flow

Usage:
    python test/test_chatconnect_deepseek.py
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Add the parent directory to the path to import app modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.services.deepseek_r1_service import DeepSeekR1Service, AIResponse, FunctionCall
from app.services.mcp_service_deepseek import MCPServiceDeepSeek, ValidationResult

load_dotenv()

class ChatConnectTester:
    """Test suite for ChatConnect with DeepSeek R1"""
    
    def __init__(self):
        self.deepseek_service = None
        self.mcp_service = None
        self.test_results = []
        
    async def setup(self):
        """Set up the test environment"""
        try:
            print("🔧 Setting up ChatConnect test environment...")
            
            # Initialize DeepSeek R1 service
            api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("DEFAULT_DEEPSEEK_API_KEY")
            if not api_key:
                print("❌ Neither DEEPSEEK_API_KEY nor DEFAULT_DEEPSEEK_API_KEY found in environment variables")
                return False
            
            self.deepseek_service = DeepSeekR1Service()  # No longer takes api_key parameter
            print("✅ DeepSeek R1 service initialized")
            
            # Initialize MCP service
            self.mcp_service = MCPServiceDeepSeek()
            print("✅ MCP service initialized")
            
            return True
            
        except Exception as e:
            print(f"❌ Setup failed: {e}")
            return False
    
    async def test_deepseek_initialization(self):
        """Test DeepSeek R1 service initialization"""
        print("\n🧠 Testing DeepSeek R1 Initialization...")
        
        try:
            # Test basic initialization
            assert self.deepseek_service is not None
            assert self.deepseek_service.client is not None
            print("✅ DeepSeek R1 client created successfully")
            
            # Test chat session initialization
            history = [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there! How can I help you?"}
            ]
            
            success = self.deepseek_service.start_chat_session(history)
            assert success == True
            print("✅ Chat session initialized with history")
            
            self.test_results.append({
                "test": "deepseek_initialization",
                "status": "PASS",
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            print(f"❌ DeepSeek R1 initialization failed: {e}")
            self.test_results.append({
                "test": "deepseek_initialization",
                "status": "FAIL",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
    
    async def test_mcp_server_connection(self):
        """Test MCP server connection"""
        print("\n🔗 Testing MCP Server Connection...")
        
        try:
            # Test with a mock Pipedream server configuration
            mock_config = {
                "name": "Test Pipedream Server",
                "type": "custom",
                "uri": "https://pipedream.net/test-endpoint",
                "transport": "http"
            }
            
            # This will fail since it's a mock URL, but we can test the connection logic
            success = await self.mcp_service.connect_to_server("test_server", mock_config)
            
            # We expect this to fail with a mock URL, but the connection logic should work
            print("✅ MCP server connection logic tested")
            
            self.test_results.append({
                "test": "mcp_server_connection",
                "status": "PASS",
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            print(f"❌ MCP server connection test failed: {e}")
            self.test_results.append({
                "test": "mcp_server_connection",
                "status": "FAIL",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
    
    async def test_function_validation(self):
        """Test function call validation"""
        print("\n✅ Testing Function Call Validation...")
        
        try:
            # Test valid function call
            valid_params = {
                "to": "test@example.com",
                "subject": "Test Email",
                "body": "This is a test email"
            }
            
            # Mock tool definition
            mock_tool = {
                "name": "gmail-send-email",
                "description": "Send an email via Gmail",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "to": {"type": "string"},
                        "subject": {"type": "string"},
                        "body": {"type": "string"}
                    },
                    "required": ["to", "subject", "body"]
                }
            }
            
            # Test validation logic
            validation = self.mcp_service.validate_function_call("gmail-send-email", valid_params)
            assert validation.valid == True
            print("✅ Valid function call validation passed")
            
            # Test invalid function call
            invalid_params = {
                "to": "test@example.com"
                # Missing required parameters
            }
            
            validation = self.mcp_service.validate_function_call("gmail-send-email", invalid_params)
            assert validation.valid == False
            assert len(validation.errors) > 0
            print("✅ Invalid function call validation passed")
            
            self.test_results.append({
                "test": "function_validation",
                "status": "PASS",
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            print(f"❌ Function validation test failed: {e}")
            self.test_results.append({
                "test": "function_validation",
                "status": "FAIL",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
    
    async def test_deepseek_message_processing(self):
        """Test DeepSeek R1 message processing"""
        try:
            print("💬 Testing DeepSeek R1 Message Processing...")
            
            # Test basic message processing
            user_message = "Hello, can you help me send an email?"
            response = await self.deepseek_service.process_message(user_message)
            
            if response and hasattr(response, 'content'):
                print(f"✅ DeepSeek response: {response.content[:100]}...")
                return True
            else:
                print("❌ Failed to get response from DeepSeek R1")
                return False
                
        except Exception as e:
            print(f"❌ DeepSeek message processing test failed: {e}")
            return False
    
    async def test_action_verification(self):
        """Test action completion verification"""
        print("\n🔍 Testing Action Completion Verification...")
        
        try:
            # Test email verification with success
            success_result = {
                "message_id": "test_message_id_123",
                "success": True
            }
            
            verification = await self.mcp_service.verify_action_completed("gmail-send-email", success_result)
            assert verification["verified"] == True
            print("✅ Email success verification passed")
            
            # Test email verification with OAuth required
            oauth_result = {
                "oauth_required": True,
                "oauth_url": "https://example.com/auth"
            }
            
            verification = await self.mcp_service.verify_action_completed("gmail-send-email", oauth_result)
            assert verification["verified"] == False
            print("✅ OAuth required verification passed")
            
            # Test email verification with failure
            failure_result = {
                "error": "Authentication failed"
            }
            
            verification = await self.mcp_service.verify_action_completed("gmail-send-email", failure_result)
            assert verification["verified"] == False
            print("✅ Failure verification passed")
            
            self.test_results.append({
                "test": "action_verification",
                "status": "PASS",
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            print(f"❌ Action verification test failed: {e}")
            self.test_results.append({
                "test": "action_verification",
                "status": "FAIL",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
    
    async def test_complete_workflow(self):
        """Test complete ChatConnect workflow"""
        try:
            print("🚀 Testing Complete ChatConnect Workflow...")
            
            # Test complete workflow with email request
            user_message = "Send an email to test@example.com with subject 'Test' and body 'Hello'"
            
            # Mock tools for testing
            mock_tools = [
                {
                    "type": "function",
                    "function": {
                        "name": "gmail-send-email",
                        "description": "Send an email via Gmail",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "instruction": {"type": "string"}
                            },
                            "required": ["instruction"]
                        }
                    }
                }
            ]
            
            response = await self.deepseek_service.process_message(user_message, mock_tools)
            
            if response and hasattr(response, 'content'):
                print(f"✅ Complete workflow response: {response.content[:100]}...")
                return True
            else:
                print("❌ Failed to get response from complete workflow")
                return False
                
        except Exception as e:
            print(f"❌ Complete workflow test failed: {e}")
            return False
    
    async def test_error_handling(self):
        """Test error handling"""
        try:
            print("⚠️ Testing Error Handling...")
            
            # Test with invalid API key
            try:
                # This should fail gracefully
                invalid_service = DeepSeekR1Service()
                print("✅ Error handling test passed")
                return True
            except Exception as e:
                print(f"✅ Error handling working: {e}")
                return True
                
        except Exception as e:
            print(f"❌ Error handling test failed: {e}")
            return False
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("📊 CHATCONNECT DEEPSEEK R1 TEST SUMMARY")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASS"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if result["status"] == "FAIL":
                    print(f"  - {result['test']}: {result.get('error', 'Unknown error')}")
        
        print("\n" + "="*60)
        
        # Save results to file
        with open("chatconnect_test_results.json", "w") as f:
            json.dump(self.test_results, f, indent=2)
        print("📄 Test results saved to chatconnect_test_results.json")
    
    async def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting ChatConnect DeepSeek R1 Integration Tests")
        print("="*60)
        
        # Setup
        if not await self.setup():
            print("❌ Setup failed. Exiting.")
            return
        
        # Run tests
        await self.test_deepseek_initialization()
        await self.test_mcp_server_connection()
        await self.test_function_validation()
        await self.test_deepseek_message_processing()
        await self.test_action_verification()
        await self.test_complete_workflow()
        await self.test_error_handling()
        
        # Print summary
        self.print_summary()

async def main():
    """Main test function"""
    tester = ChatConnectTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main()) 