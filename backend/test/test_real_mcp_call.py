#!/usr/bin/env python3
"""
Test Real MCP Call

This script tests that the MCP service makes real calls to Pipedream
instead of returning mock responses.
"""

import json
import sys
import os
import asyncio

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

try:
    from prisma import Prisma
    from app.services.mcp_service import MCPService
    print("✅ Imports successful")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

async def test_real_mcp_call():
    """Test that MCP service makes real calls to Pipedream"""
    print("🔗 Testing Real MCP Call to Pipedream")
    print("=" * 50)
    
    try:
        # Get MCP server from database
        prisma = Prisma()
        await prisma.connect()
        
        servers = await prisma.mcpserver.find_many()
        if not servers:
            print("❌ No MCP servers found in database")
            await prisma.disconnect()
            return
        
        server = servers[0]
        print(f"📧 Testing with server: {server.name}")
        print(f"🔗 URI: {server.config.get('uri') if isinstance(server.config, dict) else 'JSON string'}")
        
        # Parse config
        if isinstance(server.config, str):
            config = json.loads(server.config)
        else:
            config = server.config
        
        config['name'] = server.name
        await prisma.disconnect()
        
        # Test connection and tool call
        mcp_service = MCPService()
        server_id = f"test_{server.id}"
        
        print(f"\n🔗 Connecting to MCP server...")
        success = await mcp_service.connect_to_server(server_id, config)
        
        if not success:
            print(f"❌ Failed to connect to MCP server")
            return
        
        print(f"✅ Connected successfully!")
        
        # Test Gmail send email tool
        tool_name = "mcp_Gmail_gmail-send-email"
        test_arguments = {
            "instruction": "Send a test email to test@example.com with subject 'MCP Test' and body 'This is a test email from the MCP integration.'"
        }
        
        print(f"\n⚡ Testing real tool call: {tool_name}")
        print(f"📝 Arguments: {json.dumps(test_arguments, indent=2)}")
        
        # Make the tool call
        result = await mcp_service.call_tool(tool_name, test_arguments)
        
        print(f"\n📄 Tool call result:")
        print(f"   Type: {type(result)}")
        print(f"   Content: {json.dumps(result, indent=2)}")
        
        # Analyze the result
        if isinstance(result, dict):
            if "error" in result:
                print(f"\n❌ Tool call failed:")
                print(f"   Error: {result['error']}")
                if "details" in result:
                    print(f"   Details: {result['details']}")
            elif "success" in result and result["success"]:
                print(f"\n✅ Tool call reported success!")
                print(f"   Message: {result.get('message', 'No message')}")
                
                # Check if this looks like a real response or mock
                if "data" in result and "status" in result.get("data", {}):
                    if result["data"]["status"] == "executed":
                        print(f"   ⚠️ This looks like a mock response (status: executed)")
                    else:
                        print(f"   ✅ This looks like a real response (status: {result['data']['status']})")
                else:
                    print(f"   ✅ This appears to be a real response from Pipedream")
            else:
                print(f"\n⚠️ Unexpected response format")
                print(f"   Keys: {list(result.keys())}")
        else:
            print(f"\n⚠️ Unexpected result type: {type(result)}")
        
        # Summary
        print(f"\n" + "=" * 50)
        print("📊 Real MCP Call Test Summary")
        print("=" * 50)
        
        if "error" in result:
            print(f"❌ The tool call failed with an error")
            print(f"   This might indicate:")
            print(f"   • Pipedream workflow is not properly configured")
            print(f"   • Authentication issues with Gmail")
            print(f"   • Network connectivity problems")
            print(f"   • Invalid workflow URL")
        elif "success" in result and result["success"]:
            if "data" in result and result.get("data", {}).get("status") == "executed":
                print(f"⚠️ Still getting mock response")
                print(f"   The MCP service might still be using mock responses")
            else:
                print(f"✅ Real call to Pipedream was made!")
                print(f"   Check your Gmail sent folder for the test email")
                print(f"   Also check Pipedream logs for execution details")
        
        print(f"\n💡 Next steps:")
        print(f"   1. Check your Gmail sent folder")
        print(f"   2. Check Pipedream workflow execution logs")
        print(f"   3. Verify Gmail API credentials in Pipedream")
        print(f"   4. Test the Pipedream URL directly in a browser")
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_real_mcp_call()) 