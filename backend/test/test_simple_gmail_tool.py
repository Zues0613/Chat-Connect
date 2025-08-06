#!/usr/bin/env python3
"""
Test Simple Gmail Tool

This script tests a simpler Gmail tool to see if the Pipedream workflow is working.
"""

import json
import sys
import os
import asyncio
import aiohttp

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

try:
    from prisma import Prisma
    from app.services.mcp_service import MCPService
    print("✅ Imports successful")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

async def test_simple_gmail_tool():
    """Test a simpler Gmail tool"""
    print("🔗 Testing Simple Gmail Tool")
    print("=" * 40)
    
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
        
        # Test a simpler Gmail tool first
        tool_name = "mcp_Gmail_gmail-list-labels"
        test_arguments = {
            "instruction": "List all Gmail labels"
        }
        
        print(f"\n⚡ Testing simple tool call: {tool_name}")
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
            elif "result" in result:
                print(f"\n✅ Tool call successful!")
                print(f"   Result: {json.dumps(result['result'], indent=2)}")
            else:
                print(f"\n⚠️ Unexpected response format")
                print(f"   Keys: {list(result.keys())}")
        else:
            print(f"\n⚠️ Unexpected result type: {type(result)}")
        
        # Summary
        print(f"\n" + "=" * 40)
        print("📊 Simple Tool Test Summary")
        print("=" * 40)
        
        if "error" in result:
            print(f"❌ The tool call failed with an error")
            print(f"   This might indicate:")
            print(f"   • Pipedream workflow is not properly configured")
            print(f"   • Authentication issues with Gmail")
            print(f"   • Network connectivity problems")
        elif "result" in result:
            print(f"✅ Tool call was successful!")
            print(f"   The Pipedream workflow is working correctly.")
            print(f"   You can now try more complex operations like sending emails.")
        else:
            print(f"⚠️ Unexpected response")
            print(f"   The workflow might be working but returning unexpected data.")
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_simple_gmail_tool()) 