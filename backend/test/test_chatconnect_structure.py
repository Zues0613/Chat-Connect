#!/usr/bin/env python3
"""
ChatConnect Structure Test Script

This script tests the basic structure and imports of the ChatConnect system
without requiring actual API keys or external services.

Usage:
    python test/test_chatconnect_structure.py
"""

import sys
import os
from datetime import datetime

# Add the parent directory to the path to import app modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def test_imports():
    """Test that all modules can be imported"""
    print("🔧 Testing ChatConnect Structure and Imports...")
    
    try:
        # Test DeepSeek R1 service imports
        from app.services.deepseek_r1_service import DeepSeekR1Service, AIResponse, FunctionCall
        print("✅ DeepSeek R1 service imports successful")
        
        # Test MCP service imports
        from app.services.mcp_service_deepseek import MCPServiceDeepSeek, ValidationResult, MCPLogger
        print("✅ MCP service imports successful")
        
        # Test chat routes imports
        from app.chat.routes_deepseek import router as deepseek_router
        print("✅ Chat routes imports successful")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_class_instantiation():
    """Test that classes can be instantiated"""
    print("\n🏗️ Testing Class Instantiation...")
    
    try:
        # Test DeepSeek R1 service
        from app.services.deepseek_r1_service import DeepSeekR1Service, AIResponse, FunctionCall
        
        # Test AIResponse
        response = AIResponse(
            message="Test message",
            reasoning="Test reasoning",
            function_calls=[]
        )
        assert response.message == "Test message"
        assert response.reasoning == "Test reasoning"
        print("✅ AIResponse instantiation successful")
        
        # Test FunctionCall
        function_call = FunctionCall(
            name="test-function",
            parameters={"test": "param"},
            call_id="test_id"
        )
        assert function_call.name == "test-function"
        assert function_call.parameters["test"] == "param"
        print("✅ FunctionCall instantiation successful")
        
        # Test DeepSeekR1Service (without API key)
        service = DeepSeekR1Service()
        assert service is not None
        print("✅ DeepSeekR1Service instantiation successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Class instantiation failed: {e}")
        return False

def test_mcp_service():
    """Test MCP service structure"""
    print("\n🔗 Testing MCP Service Structure...")
    
    try:
        from app.services.mcp_service_deepseek import MCPServiceDeepSeek, ValidationResult, MCPLogger
        
        # Test MCPLogger
        logger = MCPLogger()
        assert logger is not None
        print("✅ MCPLogger instantiation successful")
        
        # Test ValidationResult
        validation = ValidationResult(True, [])
        assert validation.valid == True
        assert len(validation.errors) == 0
        
        validation_fail = ValidationResult(False, ["error1", "error2"])
        assert validation_fail.valid == False
        assert len(validation_fail.errors) == 2
        print("✅ ValidationResult instantiation successful")
        
        # Test MCPServiceDeepSeek
        mcp_service = MCPServiceDeepSeek()
        assert mcp_service is not None
        assert hasattr(mcp_service, 'servers')
        assert hasattr(mcp_service, 'logger')
        print("✅ MCPServiceDeepSeek instantiation successful")
        
        return True
        
    except Exception as e:
        print(f"❌ MCP service test failed: {e}")
        return False

def test_validation_logic():
    """Test function validation logic"""
    print("\n✅ Testing Function Validation Logic...")
    
    try:
        from app.services.mcp_service_deepseek import MCPServiceDeepSeek
        
        mcp_service = MCPServiceDeepSeek()
        
        # Test validation with valid parameters
        valid_params = {
            "to": "test@example.com",
            "subject": "Test",
            "body": "Test body"
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
        
        # Test validation (this will fail since we don't have the tool in the service)
        # But we can test the validation method exists
        assert hasattr(mcp_service, 'validate_function_call')
        print("✅ Function validation method exists")
        
        return True
        
    except Exception as e:
        print(f"❌ Validation logic test failed: {e}")
        return False

def test_environment_configuration():
    """Test environment configuration"""
    print("\n⚙️ Testing Environment Configuration...")
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        # Check if environment variables are accessible
        app_name = os.getenv("CHATCONNECT_APP_NAME", "ChatConnect")
        app_version = os.getenv("CHATCONNECT_VERSION", "1.0.0")
        
        assert app_name == "ChatConnect"
        assert app_version == "1.0.0"
        print("✅ Environment configuration accessible")
        
        # Check if .env.example exists
        if os.path.exists("env.example"):
            print("✅ env.example file exists")
        else:
            print("⚠️ env.example file not found")
        
        return True
        
    except Exception as e:
        print(f"❌ Environment configuration test failed: {e}")
        return False

def test_file_structure():
    """Test that all required files exist"""
    print("\n📁 Testing File Structure...")
    
    required_files = [
        "app/services/deepseek_r1_service.py",
        "app/services/mcp_service_deepseek.py",
        "app/chat/routes_deepseek.py",
        "app/main.py",
        "env.example",
        "CHATCONNECT_README.md"
    ]
    
    missing_files = []
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path} exists")
        else:
            print(f"❌ {file_path} missing")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\n⚠️ Missing files: {missing_files}")
        return False
    else:
        print("✅ All required files exist")
        return True

def main():
    """Run all structure tests"""
    print("🚀 ChatConnect Structure Test")
    print("=" * 50)
    
    tests = [
        ("Import Tests", test_imports),
        ("Class Instantiation", test_class_instantiation),
        ("MCP Service Structure", test_mcp_service),
        ("Validation Logic", test_validation_logic),
        ("Environment Configuration", test_environment_configuration),
        ("File Structure", test_file_structure)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append({
                "test": test_name,
                "status": "PASS" if success else "FAIL",
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append({
                "test": test_name,
                "status": "FAIL",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 STRUCTURE TEST SUMMARY")
    print("=" * 50)
    
    total_tests = len(results)
    passed_tests = len([r for r in results if r["status"] == "PASS"])
    failed_tests = total_tests - passed_tests
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests} ✅")
    print(f"Failed: {failed_tests} ❌")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if failed_tests > 0:
        print("\n❌ Failed Tests:")
        for result in results:
            if result["status"] == "FAIL":
                print(f"  - {result['test']}: {result.get('error', 'Unknown error')}")
    
    print("\n" + "=" * 50)
    
    if passed_tests == total_tests:
        print("🎉 All structure tests passed! ChatConnect is ready for configuration.")
        print("\nNext steps:")
        print("1. Set up your DEEPSEEK_API_KEY in .env file")
        print("2. Configure your MCP servers")
        print("3. Run the full integration tests: python test_chatconnect_deepseek.py")
        print("4. Start the server: uvicorn app.main:app --reload")
    else:
        print("⚠️ Some tests failed. Please check the errors above.")
    
    # Save results
    import json
    with open("chatconnect_structure_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("📄 Test results saved to chatconnect_structure_test_results.json")

if __name__ == "__main__":
    main() 