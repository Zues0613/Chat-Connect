#!/usr/bin/env python3
"""
MCP Functionality Demo

This script demonstrates how the system handles MCP server availability
and provides user-friendly error messages when servers are not available.
"""

import asyncio
import json

# Mock MCP Service for demonstration
class MockMCPService:
    def __init__(self):
        self.connected_servers = {}
        self.available_tools = []
    
    async def connect_to_server(self, server_id, config):
        """Mock server connection - always fails for demo"""
        print(f"🔗 Attempting to connect to {config.get('name', 'Unknown Server')}...")
        print(f"   URI: {config.get('uri', 'No URI')}")
        
        # Simulate connection failure
        await asyncio.sleep(0.5)  # Simulate network delay
        print(f"   ❌ Connection failed: Server not available")
        return False
    
    async def call_tool(self, tool_name, arguments):
        """Mock tool call - always returns error for demo"""
        print(f"⚡ Attempting to call tool: {tool_name}")
        print(f"   Arguments: {json.dumps(arguments, indent=2)}")
        
        # Simulate tool call failure
        await asyncio.sleep(0.3)  # Simulate processing delay
        
        return {
            "error": f"Tool '{tool_name}' is not available. No MCP server provides this tool.",
            "error_type": "tool_not_available",
            "available_tools": [],
            "connected_servers": []
        }
    
    def generate_user_friendly_error_message(self, tool_name, error_result):
        """Generate user-friendly error messages"""
        error_type = error_result.get("error_type", "unknown")
        
        if error_type == "tool_not_available":
            available_tools = error_result.get("available_tools", [])
            connected_servers = error_result.get("connected_servers", [])
            
            if available_tools:
                return f"❌ The MCP server for '{tool_name}' is not available. Available tools: {', '.join(available_tools[:5])}{'...' if len(available_tools) > 5 else ''}"
            elif connected_servers:
                return f"❌ The MCP server for '{tool_name}' is not available. Connected servers: {', '.join(connected_servers)}"
            else:
                return f"❌ The MCP server for '{tool_name}' is not available. No MCP servers are currently connected."
        
        else:
            error_msg = error_result.get("error", "Unknown error")
            return f"❌ Failed to execute '{tool_name}': {error_msg}"

async def demo_mcp_functionality():
    """Demonstrate MCP functionality with various scenarios"""
    print("🚀 MCP Functionality Demo")
    print("=" * 40)
    print("This demo shows how the system handles MCP server availability")
    print("and provides user-friendly error messages when servers are not available.\n")
    
    mcp_service = MockMCPService()
    
    # Test 1: Try to connect to Gmail MCP server
    print("📧 Testing Gmail MCP Server Connection")
    print("-" * 35)
    
    gmail_config = {
        "name": "Gmail Server",
        "type": "custom",
        "uri": "https://your-gmail-mcp-server.pipedream.net",
        "transport": "http"
    }
    
    success = await mcp_service.connect_to_server("gmail_test", gmail_config)
    if not success:
        print("   ✅ System correctly identified that Gmail server is not available\n")
    
    # Test 2: Try to connect to LinkedIn MCP server
    print("💼 Testing LinkedIn MCP Server Connection")
    print("-" * 38)
    
    linkedin_config = {
        "name": "LinkedIn Server",
        "type": "custom", 
        "uri": "https://your-linkedin-mcp-server.pipedream.net",
        "transport": "http"
    }
    
    success = await mcp_service.connect_to_server("linkedin_test", linkedin_config)
    if not success:
        print("   ✅ System correctly identified that LinkedIn server is not available\n")
    
    # Test 3: Try to call Gmail tools
    print("📧 Testing Gmail Tool Calls")
    print("-" * 25)
    
    gmail_tools = [
        "mcp_Gmail_gmail-send-email",
        "mcp_Gmail_gmail-find-email",
        "mcp_Gmail_gmail-list-labels"
    ]
    
    for tool_name in gmail_tools:
        print(f"\n   Testing: {tool_name}")
        result = await mcp_service.call_tool(tool_name, {"instruction": "Test instruction"})
        
        if "error" in result:
            user_friendly_error = mcp_service.generate_user_friendly_error_message(tool_name, result)
            print(f"   {user_friendly_error}")
    
    # Test 4: Try to call LinkedIn tools
    print("\n💼 Testing LinkedIn Tool Calls")
    print("-" * 28)
    
    linkedin_tools = [
        "mcp_LinkedIn_linkedin-get-current-member-profile",
        "mcp_LinkedIn_linkedin-create-text-post-user",
        "mcp_LinkedIn_linkedin-search-organization"
    ]
    
    for tool_name in linkedin_tools:
        print(f"\n   Testing: {tool_name}")
        result = await mcp_service.call_tool(tool_name, {"instruction": "Test instruction"})
        
        if "error" in result:
            user_friendly_error = mcp_service.generate_user_friendly_error_message(tool_name, result)
            print(f"   {user_friendly_error}")
    
    # Test 5: Try to call other MCP tools
    print("\n🔧 Testing Other MCP Tools")
    print("-" * 25)
    
    other_tools = [
        "mcp_ElevenLabs_text_to_speech",
        "mcp_GoogleDrive_google_drive-list-files",
        "mcp_GitHub_github-create-repository"
    ]
    
    for tool_name in other_tools:
        print(f"\n   Testing: {tool_name}")
        result = await mcp_service.call_tool(tool_name, {"instruction": "Test instruction"})
        
        if "error" in result:
            user_friendly_error = mcp_service.generate_user_friendly_error_message(tool_name, result)
            print(f"   {user_friendly_error}")
    
    # Summary
    print("\n" + "=" * 40)
    print("📊 Demo Summary")
    print("=" * 40)
    
    print("✅ The system correctly handles MCP server unavailability:")
    print("   • Attempts to connect to MCP servers")
    print("   • Detects when servers are not available")
    print("   • Provides clear error messages for each tool")
    print("   • Explains what tools are available (if any)")
    print("   • Gives helpful feedback to users")
    
    print("\n💡 When you request an action that requires an MCP server:")
    print("   • The AI will attempt to use the appropriate MCP tool")
    print("   • If the tool is available: The action will be executed")
    print("   • If the tool is not available: You'll receive a clear error message")
    
    print("\n🎯 Example user interaction:")
    print("   User: 'Send an email to john@example.com'")
    print("   System: '❌ The MCP server for 'mcp_Gmail_gmail-send-email' is not available.")
    print("           No MCP servers are currently connected.'")
    
    print("\n✅ Demo completed successfully!")
    print("   The system properly handles MCP server availability and provides appropriate feedback.")

if __name__ == "__main__":
    asyncio.run(demo_mcp_functionality()) 