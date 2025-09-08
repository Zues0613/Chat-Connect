#!/usr/bin/env python3
"""
MCP Server Diagnostic Script

This script helps diagnose MCP server connection issues by:
1. Checking what MCP servers are configured in the database
2. Testing connections to those servers
3. Identifying configuration issues
"""

import asyncio
import json
import sys
import os
from typing import Dict, Any, List

# Add the backend directory to the path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

try:
    from prisma import Prisma
    from app.services.mcp_service import MCPService
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running this from the backend directory and all dependencies are installed.")
    sys.exit(1)

async def diagnose_mcp_servers():
    """Diagnose MCP server configurations and connections"""
    print("🔍 MCP Server Diagnostic Tool")
    print("=" * 50)
    
    # Initialize Prisma
    try:
        prisma = Prisma()
        await prisma.connect()
        print("✅ Database connection successful")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return
    
    # Get all MCP servers from database
    try:
        servers = await prisma.mcpserver.find_many()
        print(f"\n📊 Found {len(servers)} MCP server(s) in database")
        
        if not servers:
            print("❌ No MCP servers found in database")
            print("   You need to add MCP servers through the settings page first")
            await prisma.disconnect()
            return
        
        # Display server configurations
        print("\n🔧 MCP Server Configurations:")
        print("-" * 35)
        
        for i, server in enumerate(servers, 1):
            print(f"\n{i}. Server ID: {server.id}")
            print(f"   Name: {server.name}")
            print(f"   Description: {server.description or 'None'}")
            print(f"   User ID: {server.userId}")
            print(f"   Created: {server.createdAt}")
            
            # Parse and display config
            try:
                if isinstance(server.config, str):
                    config = json.loads(server.config)
                else:
                    config = server.config
                
                print(f"   Config:")
                print(f"     Type: {config.get('type', 'Unknown')}")
                print(f"     URI: {config.get('uri', 'None')}")
                print(f"     Transport: {config.get('transport', 'Unknown')}")
                
            except Exception as e:
                print(f"   ❌ Config parsing error: {e}")
                print(f"   Raw config: {server.config}")
        
        await prisma.disconnect()
        
    except Exception as e:
        print(f"❌ Error fetching MCP servers: {e}")
        await prisma.disconnect()
        return
    
    # Test MCP service connections
    print("\n🔗 Testing MCP Service Connections:")
    print("-" * 40)
    
    mcp_service = MCPService()
    
    for i, server in enumerate(servers, 1):
        print(f"\n{i}. Testing connection to '{server.name}':")
        
        # Parse config
        try:
            if isinstance(server.config, str):
                config = json.loads(server.config)
            else:
                config = server.config
            
            # Add server name to config for better error messages
            config['name'] = server.name
            
            print(f"   Config: {json.dumps(config, indent=2)}")
            
            # Test connection
            server_id = f"test_server_{server.id}"
            success = await mcp_service.connect_to_server(server_id, config)
            
            if success:
                print(f"   ✅ Connection successful!")
                
                # Get tools from this server
                client = mcp_service.clients.get(server_id)
                if client:
                    print(f"   📋 Available tools: {len(client.available_tools)}")
                    for tool in client.available_tools:
                        print(f"      • {tool.get('name', 'Unknown')}")
                else:
                    print(f"   ⚠️ No client found after successful connection")
            else:
                print(f"   ❌ Connection failed")
                
                # Get error details
                client = mcp_service.clients.get(server_id)
                if client and client.last_error:
                    print(f"   Error: {client.last_error}")
                
        except Exception as e:
            print(f"   ❌ Error testing connection: {e}")
    
    # Test tool availability
    print("\n🔧 Testing Tool Availability:")
    print("-" * 30)
    
    all_tools = mcp_service.get_all_tools()
    connected_servers = mcp_service.get_connected_servers()
    
    print(f"Total connected servers: {len(connected_servers)}")
    print(f"Total available tools: {len(all_tools)}")
    
    if all_tools:
        print("\nAvailable tools:")
        for tool in all_tools:
            print(f"  • {tool.get('name')} (from {tool.get('server_name', 'Unknown')})")
    else:
        print("\n❌ No tools available")
    
    # Test specific tool calls
    print("\n⚡ Testing Specific Tool Calls:")
    print("-" * 35)
    
    test_tools = [
        "mcp_Gmail_gmail-send-email",
        "mcp_LinkedIn_linkedin-get-current-member-profile",
        "mcp_ElevenLabs_text_to_speech"
    ]
    
    for tool_name in test_tools:
        print(f"\nTesting: {tool_name}")
        
        # Check if tool is available
        is_available = mcp_service.is_tool_available(tool_name)
        server_info = mcp_service.get_tool_server_info(tool_name)
        
        if is_available and server_info:
            print(f"  ✅ Available from {server_info['server_name']}")
            
            # Try to call the tool
            try:
                result = await mcp_service.call_tool(tool_name, {"instruction": "Test call"})
                if "error" in result:
                    print(f"  ❌ Tool call failed: {result['error']}")
                else:
                    print(f"  ✅ Tool call successful")
            except Exception as e:
                print(f"  ❌ Tool call error: {e}")
        else:
            print(f"  ❌ Not available")
            if server_info:
                print(f"     Server info: {server_info}")
    
    # Summary and recommendations
    print("\n" + "=" * 50)
    print("📊 Diagnostic Summary")
    print("=" * 50)
    
    print(f"• MCP servers in database: {len(servers)}")
    print(f"• Successfully connected: {len(connected_servers)}")
    print(f"• Available tools: {len(all_tools)}")
    
    if len(connected_servers) == 0:
        print("\n❌ No MCP servers are currently connected!")
        print("\n💡 Possible issues:")
        print("   • MCP server URLs are incorrect")
        print("   • MCP servers are not running")
        print("   • Network connectivity issues")
        print("   • Authentication problems")
        print("   • Invalid server configurations")
        
        print("\n🔧 Troubleshooting steps:")
        print("   1. Verify MCP server URLs are correct")
        print("   2. Ensure MCP servers are running and accessible")
        print("   3. Check network connectivity")
        print("   4. Review server configurations")
        print("   5. Check server logs for errors")
    
    elif len(all_tools) == 0:
        print("\n⚠️ Servers connected but no tools available!")
        print("\n💡 Possible issues:")
        print("   • MCP servers don't provide the expected tools")
        print("   • Tool discovery failed")
        print("   • Server configuration issues")
    
    else:
        print("\n✅ MCP functionality is working!")
        print(f"   You have {len(all_tools)} tools available from {len(connected_servers)} servers")
    
    print("\n✅ Diagnostic completed!")

if __name__ == "__main__":
    asyncio.run(diagnose_mcp_servers()) 