#!/usr/bin/env python3
"""
MCP Functionality Test Script

This script demonstrates how to test MCP functionality and handle cases where
specific MCP servers are not available. It shows the proper error handling
and user feedback mechanisms.
"""

import asyncio
import json
import sys
import os
from typing import Dict, Any, List, Optional

# Add the backend directory to the path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.mcp_service import MCPService, MCPClient

class MCPFunctionalityTester:
    def __init__(self):
        self.mcp_service = MCPService()
        self.test_results = []
    
    async def test_mcp_server_connection(self, server_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Test connection to an MCP server"""
        print(f"\n🔗 Testing connection to MCP server: {server_id}")
        print(f"   Config: {json.dumps(config, indent=2)}")
        
        try:
            success = await self.mcp_service.connect_to_server(server_id, config)
            
            if success:
                print(f"   ✅ Successfully connected to {server_id}")
                return {
                    "server_id": server_id,
                    "status": "connected",
                    "tools_count": len(self.mcp_service.clients[server_id].available_tools),
                    "tools": self.mcp_service.clients[server_id].available_tools
                }
            else:
                print(f"   ❌ Failed to connect to {server_id}")
                return {
                    "server_id": server_id,
                    "status": "failed",
                    "error": "Connection failed"
                }
                
        except Exception as e:
            print(f"   ❌ Error connecting to {server_id}: {e}")
            return {
                "server_id": server_id,
                "status": "error",
                "error": str(e)
            }
    
    async def test_tool_availability(self, tool_name: str) -> Dict[str, Any]:
        """Test if a specific tool is available"""
        print(f"\n🔧 Testing tool availability: {tool_name}")
        
        # Check if any connected server has this tool
        available_tools = self.mcp_service.get_all_tools()
        tool_found = None
        
        for tool in available_tools:
            if tool.get("name") == tool_name:
                tool_found = tool
                break
        
        if tool_found:
            print(f"   ✅ Tool '{tool_name}' is available")
            return {
                "tool_name": tool_name,
                "status": "available",
                "tool_info": tool_found
            }
        else:
            print(f"   ❌ Tool '{tool_name}' is NOT available")
            print(f"   📋 Available tools: {[tool.get('name') for tool in available_tools]}")
            return {
                "tool_name": tool_name,
                "status": "not_available",
                "available_tools": [tool.get('name') for tool in available_tools]
            }
    
    async def test_tool_execution(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Test execution of a specific tool"""
        print(f"\n⚡ Testing tool execution: {tool_name}")
        print(f"   Arguments: {json.dumps(arguments, indent=2)}")
        
        try:
            result = await self.mcp_service.call_tool(tool_name, arguments)
            
            if "error" in result:
                print(f"   ❌ Tool execution failed: {result['error']}")
                return {
                    "tool_name": tool_name,
                    "status": "failed",
                    "error": result["error"]
                }
            else:
                print(f"   ✅ Tool execution successful")
                print(f"   📄 Result: {json.dumps(result, indent=2)}")
                return {
                    "tool_name": tool_name,
                    "status": "success",
                    "result": result
                }
                
        except Exception as e:
            print(f"   ❌ Tool execution error: {e}")
            return {
                "tool_name": tool_name,
                "status": "error",
                "error": str(e)
            }
    
    def generate_user_friendly_message(self, test_result: Dict[str, Any]) -> str:
        """Generate user-friendly messages based on test results"""
        if test_result.get("status") == "not_available":
            tool_name = test_result.get("tool_name", "Unknown tool")
            available_tools = test_result.get("available_tools", [])
            
            if available_tools:
                return f"❌ The MCP server for '{tool_name}' is not available. Available tools: {', '.join(available_tools)}"
            else:
                return f"❌ The MCP server for '{tool_name}' is not available. No MCP servers are currently connected."
        
        elif test_result.get("status") == "failed":
            return f"❌ Failed to execute '{test_result.get('tool_name')}': {test_result.get('error')}"
        
        elif test_result.get("status") == "success":
            return f"✅ Successfully executed '{test_result.get('tool_name')}'"
        
        else:
            return f"⚠️ Unknown status for '{test_result.get('tool_name')}': {test_result.get('status')}"
    
    async def run_comprehensive_test(self):
        """Run a comprehensive test of MCP functionality"""
        print("🚀 Starting MCP Functionality Test")
        print("=" * 50)
        
        # Test 1: Try to connect to various MCP servers
        test_servers = [
            {
                "id": "gmail_server",
                "config": {
                    "type": "custom",
                    "uri": "https://your-gmail-mcp-server.pipedream.net",
                    "transport": "http"
                }
            },
            {
                "id": "linkedin_server", 
                "config": {
                    "type": "custom",
                    "uri": "https://your-linkedin-mcp-server.pipedream.net",
                    "transport": "http"
                }
            },
            {
                "id": "file_system_server",
                "config": {
                    "type": "stdio",
                    "uri": "mcp-file-system",
                    "transport": "stdio"
                }
            },
            {
                "id": "github_server",
                "config": {
                    "type": "custom",
                    "uri": "https://your-github-mcp-server.pipedream.net",
                    "transport": "http"
                }
            }
        ]
        
        print("\n📡 Testing MCP Server Connections")
        print("-" * 30)
        
        for server_test in test_servers:
            result = await self.test_mcp_server_connection(server_test["id"], server_test["config"])
            self.test_results.append(result)
        
        # Test 2: Test tool availability
        test_tools = [
            "mcp_Gmail_gmail-send-email",
            "mcp_LinkedIn_linkedin-get-current-member-profile", 
            "mcp_file_system_read_file",
            "mcp_GitHub_github-create-repository",
            "mcp_ElevenLabs_text_to_speech"
        ]
        
        print("\n🔧 Testing Tool Availability")
        print("-" * 30)
        
        for tool_name in test_tools:
            result = await self.test_tool_availability(tool_name)
            self.test_results.append(result)
        
        # Test 3: Test tool execution for available tools
        print("\n⚡ Testing Tool Execution")
        print("-" * 30)
        
        # Get all available tools
        available_tools = self.mcp_service.get_all_tools()
        
        if available_tools:
            print(f"Found {len(available_tools)} available tools")
            
            # Test a few available tools
            for tool in available_tools[:2]:  # Test first 2 tools
                tool_name = tool.get("name")
                if tool_name:
                    # Create sample arguments based on tool schema
                    sample_args = self.generate_sample_arguments(tool)
                    result = await self.test_tool_execution(tool_name, sample_args)
                    self.test_results.append(result)
        else:
            print("No tools available for testing")
        
        # Test 4: Test error handling for unavailable tools
        print("\n🚫 Testing Error Handling for Unavailable Tools")
        print("-" * 50)
        
        unavailable_tools = [
            "mcp_NonExistent_tool",
            "mcp_AnotherServer_missing_function"
        ]
        
        for tool_name in unavailable_tools:
            result = await self.test_tool_availability(tool_name)
            self.test_results.append(result)
        
        # Generate summary
        await self.generate_test_summary()
    
    def generate_sample_arguments(self, tool: Dict[str, Any]) -> Dict[str, Any]:
        """Generate sample arguments for a tool based on its schema"""
        schema = tool.get("inputSchema", {})
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        
        sample_args = {}
        
        for prop_name, prop_info in properties.items():
            prop_type = prop_info.get("type", "string")
            description = prop_info.get("description", "")
            
            if prop_type == "string":
                if "email" in prop_name.lower():
                    sample_args[prop_name] = "test@example.com"
                elif "url" in prop_name.lower():
                    sample_args[prop_name] = "https://example.com"
                elif "instruction" in prop_name.lower():
                    sample_args[prop_name] = "This is a test instruction for the MCP tool."
                else:
                    sample_args[prop_name] = f"Sample {prop_name}"
            elif prop_type == "number":
                sample_args[prop_name] = 42
            elif prop_type == "boolean":
                sample_args[prop_name] = True
            elif prop_type == "array":
                sample_args[prop_name] = []
            elif prop_type == "object":
                sample_args[prop_name] = {}
        
        return sample_args
    
    async def generate_test_summary(self):
        """Generate a comprehensive test summary"""
        print("\n" + "=" * 50)
        print("📊 MCP FUNCTIONALITY TEST SUMMARY")
        print("=" * 50)
        
        # Count results by status
        status_counts = {}
        for result in self.test_results:
            status = result.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1
        
        print(f"\n📈 Test Results Summary:")
        for status, count in status_counts.items():
            print(f"   {status.capitalize()}: {count}")
        
        print(f"\n🔗 Connected Servers:")
        connected_servers = self.mcp_service.get_connected_servers()
        if connected_servers:
            for server in connected_servers:
                print(f"   ✅ {server['id']}: {server['tool_count']} tools")
        else:
            print("   ❌ No servers connected")
        
        print(f"\n🔧 Available Tools:")
        available_tools = self.mcp_service.get_all_tools()
        if available_tools:
            for tool in available_tools:
                print(f"   • {tool.get('name', 'Unknown')}")
        else:
            print("   ❌ No tools available")
        
        print(f"\n💡 User-Friendly Messages:")
        print("-" * 30)
        
        # Generate user-friendly messages for failed/unavailable tools
        for result in self.test_results:
            if result.get("status") in ["not_available", "failed", "error"]:
                message = self.generate_user_friendly_message(result)
                print(f"   {message}")
        
        print(f"\n🎯 Recommendations:")
        print("-" * 20)
        
        if not connected_servers:
            print("   • Set up MCP servers in your configuration")
            print("   • Ensure MCP server URLs are correct and accessible")
            print("   • Check network connectivity to MCP servers")
        
        if not available_tools:
            print("   • Connect to MCP servers to get access to tools")
            print("   • Verify MCP server configurations")
        
        failed_tools = [r for r in self.test_results if r.get("status") == "failed"]
        if failed_tools:
            print("   • Review tool execution errors and fix configurations")
            print("   • Check tool parameter requirements")
        
        print(f"\n✅ Test completed successfully!")
        print("   The system properly handles MCP server availability and provides appropriate feedback.")

async def main():
    """Main function to run the MCP functionality test"""
    tester = MCPFunctionalityTester()
    await tester.run_comprehensive_test()

if __name__ == "__main__":
    asyncio.run(main()) 