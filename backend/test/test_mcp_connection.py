#!/usr/bin/env python3
"""
Test MCP Connection

This script tests the actual MCP server connection using your configured server.
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

async def test_mcp_connection():
    """Test MCP server connection"""
    print("🔗 Testing MCP Server Connection")
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
        
        server = servers[0]  # Use the first server
        print(f"📧 Testing connection to: {server.name}")
        
        # Parse config
        if isinstance(server.config, str):
            config = json.loads(server.config)
        else:
            config = server.config
        
        config['name'] = server.name
        print(f"🔧 Config: {json.dumps(config, indent=2)}")
        
        await prisma.disconnect()
        
        # Test connection with MCP service
        mcp_service = MCPService()
        server_id = f"test_{server.id}"
        
        print(f"\n🔗 Attempting to connect...")
        success = await mcp_service.connect_to_server(server_id, config)
        
        if success:
            print(f"✅ Connection successful!")
            
            # Check available tools
            client = mcp_service.clients.get(server_id)
            if client:
                print(f"📋 Available tools: {len(client.available_tools)}")
                for tool in client.available_tools:
                    print(f"   • {tool.get('name', 'Unknown')}")
                
                # Test a Gmail tool
                if client.available_tools:
                    test_tool = client.available_tools[0]
                    tool_name = test_tool.get('name')
                    
                    print(f"\n⚡ Testing tool call: {tool_name}")
                    result = await mcp_service.call_tool(tool_name, {
                        "instruction": "This is a test call to verify the MCP server is working"
                    })
                    
                    if "error" in result:
                        print(f"❌ Tool call failed: {result['error']}")
                    else:
                        print(f"✅ Tool call successful!")
                        print(f"📄 Result: {json.dumps(result, indent=2)}")
            else:
                print(f"⚠️ No client found after successful connection")
        else:
            print(f"❌ Connection failed")
            
            # Get error details
            client = mcp_service.clients.get(server_id)
            if client and client.last_error:
                print(f"🔍 Error details: {client.last_error}")
        
        # Summary
        print(f"\n" + "=" * 40)
        print("📊 Connection Test Summary")
        print("=" * 40)
        
        connected_servers = mcp_service.get_connected_servers()
        all_tools = mcp_service.get_all_tools()
        
        print(f"• Connected servers: {len(connected_servers)}")
        print(f"• Available tools: {len(all_tools)}")
        
        if len(connected_servers) > 0:
            print(f"✅ MCP server connection is working!")
            print(f"   You should now be able to use MCP tools in your chat.")
        else:
            print(f"❌ MCP server connection failed")
            print(f"   Check the error details above for troubleshooting.")
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_mcp_connection()) 