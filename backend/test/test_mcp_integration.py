#!/usr/bin/env python3
"""
Test MCP Integration with DeepSeek
Run this from the backend directory: python test_mcp_integration.py
"""

import os
import asyncio
import json
from dotenv import load_dotenv
from prisma import Prisma
from app.services.mcp_service import mcp_service
from app.services.deepseek_service import deepseek_service

load_dotenv()

async def test_mcp_integration():
    print("🔍 Testing MCP Integration with DeepSeek\n")
    
    # Get API key
    api_key = os.getenv("DEFAULT_DEEPSEEK_API_KEY")
    if not api_key:
        print("❌ DEFAULT_DEEPSEEK_API_KEY not found in .env")
        return
    
    print(f"✅ API Key found: {api_key[:10]}...{api_key[-4:]}")
    
    try:
        # Initialize DeepSeek
        print("🔄 Initializing DeepSeek service...")
        if not deepseek_service.initialize_with_api_key(api_key):
            print("❌ Failed to initialize DeepSeek")
            return
        print("✅ DeepSeek service initialized")
        
        # Connect to database
        print("🔄 Connecting to database...")
        prisma = Prisma()
        await prisma.connect()
        
        # Get test user (assuming test@gmail.com exists)
        user = await prisma.user.find_unique(where={"email": "test@gmail.com"})
        if not user:
            print("❌ Test user not found. Please create a user first.")
            await prisma.disconnect()
            return
        
        print(f"✅ Found test user: {user.email} (ID: {user.id})")
        
        # Get user's MCP servers
        servers = await prisma.mcpserver.find_many(where={"userId": user.id})
        print(f"📊 Found {len(servers)} MCP servers for user")
        
        if not servers:
            print("❌ No MCP servers found. Please add an MCP server first.")
            await prisma.disconnect()
            return
        
        # Display server information
        for i, server in enumerate(servers, 1):
            print(f"\n📡 Server {i}:")
            print(f"   Name: {server.name}")
            print(f"   Description: {server.description}")
            print(f"   Config: {json.dumps(server.config, indent=2)}")
        
        await prisma.disconnect()
        
        # Initialize MCP servers
        print(f"\n🔄 Initializing MCP servers for user {user.id}...")
        from app.chat.routes import initialize_mcp_servers
        await initialize_mcp_servers(user.id)
        
        # Check connected servers
        connected_servers = mcp_service.get_connected_servers()
        print(f"✅ Connected to {len(connected_servers)} MCP servers")
        
        for server_info in connected_servers:
            print(f"   - {server_info}")
        
        # Get available tools
        all_tools = mcp_service.get_all_tools()
        print(f"\n🔧 Available tools: {len(all_tools)}")
        
        for tool in all_tools:
            print(f"   - {tool.get('name', 'Unknown')}: {tool.get('description', 'No description')}")
        
        # Get tools in OpenAI format
        openai_tools = mcp_service.get_openai_tools()
        print(f"\n🤖 OpenAI format tools: {len(openai_tools)}")
        
        for tool in openai_tools:
            function = tool.get('function', {})
            print(f"   - {function.get('name', 'Unknown')}: {function.get('description', 'No description')}")
        
        # Test DeepSeek with tools
        if openai_tools:
            print(f"\n🧪 Testing DeepSeek with {len(openai_tools)} tools...")
            
            # Start chat session
            if not deepseek_service.start_chat_session():
                print("❌ Failed to start chat session")
                return
            
            # Send a test message that might trigger tool usage
            test_message = "Can you check my Gmail inbox and tell me how many unread emails I have?"
            print(f"📤 Sending test message: {test_message}")
            
            response = await deepseek_service.send_message(test_message, tools=openai_tools)
            
            print(f"📥 Response type: {response.get('type')}")
            
            if response.get('type') == 'tool_calls':
                print("🎉 DeepSeek requested tool calls!")
                tool_calls = response.get('tool_calls', [])
                print(f"   Tool calls requested: {len(tool_calls)}")
                
                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    print(f"   - {function_name}: {function_args}")
                    
                    # Test calling the tool
                    print(f"   🔄 Calling tool: {function_name}")
                    try:
                        tool_result = await mcp_service.call_tool(function_name, function_args)
                        print(f"   ✅ Tool result: {tool_result}")
                    except Exception as e:
                        print(f"   ❌ Tool call failed: {e}")
            else:
                print(f"📝 Text response: {response.get('content', 'No content')}")
        else:
            print("⚠️  No tools available for testing")
        
        print("\n🎉 MCP integration test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_mcp_integration()) 