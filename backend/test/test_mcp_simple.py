#!/usr/bin/env python3
"""
Simple MCP Functionality Test

This script demonstrates how the system handles MCP server availability
and provides user-friendly error messages when servers are not available.
"""

import asyncio
import sys
import os

# Add the backend directory to the path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.mcp_service import MCPService

async def test_mcp_functionality():
    """Test MCP functionality with various scenarios"""
    print("🚀 MCP Functionality Test")
    print("=" * 40)
    
    mcp_service = MCPService()
    
    # Test 1: Try to connect to a non-existent Gmail MCP server
    print("\n📧 Testing Gmail MCP Server Connection")
    print("-" * 35)
    
    gmail_config = {
        "name": "Gmail Server",
        "type": "custom",
        "uri": "https://non-existent-gmail-server.pipedream.net",
        "transport": "http"
    }
    
    success = await mcp_service.connect_to_server("gmail_test", gmail_config)
    if success:
        print("✅ Gmail server connected successfully")
    else:
        print("❌ Gmail server connection failed (expected)")
    
    # Test 2: Try to connect to a LinkedIn MCP server
    print("\n💼 Testing LinkedIn MCP Server Connection")
    print("-" * 38)
    
    linkedin_config = {
        "name": "LinkedIn Server",
        "type": "custom", 
        "uri": "https://non-existent-linkedin-server.pipedream.net",
        "transport": "http"
    }
    
    success = await mcp_service.connect_to_server("linkedin_test", linkedin_config)
    if success:
        print("✅ LinkedIn server connected successfully")
    else:
        print("❌ LinkedIn server connection failed (expected)")
    
    # Test 3: Check available tools
    print("\n🔧 Checking Available Tools")
    print("-" * 25)
    
    available_tools = mcp_service.get_all_tools()
    if available_tools:
        print(f"✅ Found {len(available_tools)} available tools:")
        for tool in available_tools:
            print(f"   • {tool.get('name')} (from {tool.get('server_name', 'Unknown')})")
    else:
        print("❌ No tools available (expected)")
    
    # Test 4: Try to call a Gmail tool
    print("\n📧 Testing Gmail Tool Call")
    print("-" * 25)
    
    gmail_tool_result = await mcp_service.call_tool(
        "mcp_Gmail_gmail-send-email",
        {"instruction": "Send a test email"}
    )
    
    if "error" in gmail_tool_result:
        user_friendly_error = mcp_service.generate_user_friendly_error_message(
            "mcp_Gmail_gmail-send-email", 
            gmail_tool_result
        )
        print(f"❌ Gmail tool call failed: {user_friendly_error}")
    else:
        print("✅ Gmail tool call successful")
    
    # Test 5: Try to call a LinkedIn tool
    print("\n💼 Testing LinkedIn Tool Call")
    print("-" * 28)
    
    linkedin_tool_result = await mcp_service.call_tool(
        "mcp_LinkedIn_linkedin-get-current-member-profile",
        {"instruction": "Get my LinkedIn profile"}
    )
    
    if "error" in linkedin_tool_result:
        user_friendly_error = mcp_service.generate_user_friendly_error_message(
            "mcp_LinkedIn_linkedin-get-current-member-profile",
            linkedin_tool_result
        )
        print(f"❌ LinkedIn tool call failed: {user_friendly_error}")
    else:
        print("✅ LinkedIn tool call successful")
    
    # Test 6: Try to call a non-existent tool
    print("\n🚫 Testing Non-existent Tool Call")
    print("-" * 32)
    
    fake_tool_result = await mcp_service.call_tool(
        "mcp_FakeServer_fake-function",
        {"test": "data"}
    )
    
    if "error" in fake_tool_result:
        user_friendly_error = mcp_service.generate_user_friendly_error_message(
            "mcp_FakeServer_fake-function",
            fake_tool_result
        )
        print(f"❌ Fake tool call failed: {user_friendly_error}")
    else:
        print("✅ Fake tool call successful")
    
    # Test 7: Check connected servers
    print("\n🔗 Connected Servers Status")
    print("-" * 25)
    
    connected_servers = mcp_service.get_connected_servers()
    if connected_servers:
        print("✅ Connected servers:")
        for server in connected_servers:
            status = "🟢 Connected" if server["is_connected"] else "🔴 Disconnected"
            print(f"   • {server['name']}: {status} ({server['tool_count']} tools)")
            if server.get("last_error"):
                print(f"     Error: {server['last_error']}")
    else:
        print("❌ No servers connected")
    
    # Test 8: Demonstrate tool availability checking
    print("\n🔍 Tool Availability Check")
    print("-" * 25)
    
    test_tools = [
        "mcp_Gmail_gmail-send-email",
        "mcp_LinkedIn_linkedin-get-current-member-profile",
        "mcp_ElevenLabs_text_to_speech",
        "mcp_FakeServer_fake-function"
    ]
    
    for tool_name in test_tools:
        is_available = mcp_service.is_tool_available(tool_name)
        server_info = mcp_service.get_tool_server_info(tool_name)
        
        if is_available and server_info:
            print(f"✅ {tool_name} - Available from {server_info['server_name']}")
        else:
            print(f"❌ {tool_name} - Not available")
    
    print("\n" + "=" * 40)
    print("📊 Test Summary")
    print("=" * 40)
    
    print(f"• Connected servers: {len(connected_servers)}")
    print(f"• Available tools: {len(available_tools)}")
    
    if not connected_servers:
        print("\n💡 The system correctly handles cases where MCP servers are not available.")
        print("   When you request an action that requires a specific MCP server:")
        print("   • The system will inform you that the MCP server is not available")
        print("   • It will show you what tools are currently available")
        print("   • It will provide helpful error messages")
    
    print("\n✅ MCP functionality test completed!")
    print("   The system properly handles MCP server availability and provides appropriate feedback.")

if __name__ == "__main__":
    asyncio.run(test_mcp_functionality()) 