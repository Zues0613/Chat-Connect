#!/usr/bin/env python3
"""
Test Tool Discovery

This script discovers available tools and their parameters from the MCP server.
"""

import asyncio
import json
import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

try:
    from prisma import Prisma
    from app.services.mcp_service import mcp_service
    print("✅ Imports successful")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

async def test_tool_discovery():
    """Test tool discovery from MCP server"""
    print("🔍 Testing Tool Discovery")
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
        
        # Parse config
        if isinstance(server.config, str):
            config = json.loads(server.config)
        else:
            config = server.config
        
        config['name'] = server.name
        server_id = f"test_discovery_{server.id}"
        
        await prisma.disconnect()
        
        # Connect to MCP server
        print(f"\n🔗 Connecting to MCP server...")
        success = await mcp_service.connect_to_server(server_id, config)
        
        if not success:
            print("❌ Failed to connect to MCP server")
            return
        
        print("✅ Connected to MCP server")
        
        # Get all available tools
        print(f"\n📋 Available Tools:")
        all_tools = mcp_service.get_all_tools()
        
        if not all_tools:
            print("❌ No tools discovered")
            return
        
        for i, tool in enumerate(all_tools, 1):
            print(f"\n{i}. Tool: {tool.get('name', 'Unknown')}")
            print(f"   Description: {tool.get('description', 'No description')}")
            
            # Show input schema
            input_schema = tool.get('inputSchema', {})
            if input_schema:
                print(f"   Parameters:")
                properties = input_schema.get('properties', {})
                required = input_schema.get('required', [])
                
                for param_name, param_info in properties.items():
                    param_type = param_info.get('type', 'unknown')
                    param_desc = param_info.get('description', 'No description')
                    is_required = param_name in required
                    print(f"     • {param_name} ({param_type}){' [REQUIRED]' if is_required else ''}: {param_desc}")
            else:
                print(f"   Parameters: None")
        
        # Test a Gmail tool with correct parameters
        print(f"\n🔍 Looking for Gmail tools...")
        gmail_tools = [tool for tool in all_tools if 'gmail' in tool.get('name', '').lower()]
        
        if gmail_tools:
            print(f"Found {len(gmail_tools)} Gmail tools:")
            for tool in gmail_tools:
                print(f"  • {tool.get('name')}")
                
            # Test the first Gmail tool
            test_tool = gmail_tools[0]
            tool_name = test_tool.get('name')
            
            print(f"\n🧪 Testing tool: {tool_name}")
            
            # Get the correct parameters
            input_schema = test_tool.get('inputSchema', {})
            required_params = input_schema.get('required', [])
            properties = input_schema.get('properties', {})
            
            # Build arguments based on schema
            test_args = {}
            for param in required_params:
                if param == 'instruction':
                    test_args[param] = f"Test {tool_name} functionality"
                elif param == 'to':
                    test_args[param] = "test@example.com"
                elif param == 'subject':
                    test_args[param] = "Test Subject"
                elif param == 'body':
                    test_args[param] = "Test body content"
                else:
                    # For unknown parameters, use a default value
                    param_info = properties.get(param, {})
                    param_type = param_info.get('type', 'string')
                    if param_type == 'string':
                        test_args[param] = f"test_{param}"
                    elif param_type == 'boolean':
                        test_args[param] = False
                    elif param_type == 'number':
                        test_args[param] = 0
                    else:
                        test_args[param] = None
            
            print(f"📝 Arguments: {json.dumps(test_args, indent=2)}")
            
            # Call the tool
            result = await mcp_service.call_tool(tool_name, test_args, server_id)
            
            print(f"\n📄 Tool call result:")
            print(f"   Type: {type(result)}")
            print(f"   Content: {json.dumps(result, indent=2)}")
            
            # Generate user-friendly message
            user_message = mcp_service.generate_user_friendly_error_message(tool_name, result)
            
            print(f"\n💬 User-friendly message:")
            print(f"{user_message}")
        else:
            print("❌ No Gmail tools found")
        
        # Clean up
        await mcp_service.disconnect_from_server(server_id)
        
        # Summary
        print(f"\n" + "=" * 50)
        print("📊 Tool Discovery Summary")
        print("=" * 50)
        print(f"✅ Discovered {len(all_tools)} tools")
        print(f"✅ MCP server is working correctly")
        print(f"✅ Tool discovery is functional")
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_tool_discovery()) 