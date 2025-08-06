#!/usr/bin/env python3
"""
Test Gmail with Instructions

This script tests Gmail functionality using the instruction-based format.
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

async def test_gmail_instruction():
    """Test Gmail with instruction-based format"""
    print("📧 Testing Gmail with Instructions")
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
        server_id = f"test_gmail_{server.id}"
        
        await prisma.disconnect()
        
        # Connect to MCP server
        print(f"\n🔗 Connecting to MCP server...")
        success = await mcp_service.connect_to_server(server_id, config)
        
        if not success:
            print("❌ Failed to connect to MCP server")
            return
        
        print("✅ Connected to MCP server")
        
        # Test 1: Send email with instruction
        print(f"\n📧 Test 1: Send email with instruction...")
        
        email_instruction = "Send an email to vishad.cse2023@citchennai.net with subject 'iPhone Charger Request' asking him to give me the iPhone charger when he gets a chance"
        
        email_args = {
            "instruction": email_instruction
        }
        
        print(f"📝 Instruction: {email_instruction}")
        
        # Call the tool
        result = await mcp_service.call_tool("mcp_Gmail_gmail-send-email", email_args, server_id)
        
        print(f"\n📄 Tool call result:")
        print(f"   Type: {type(result)}")
        print(f"   Content: {json.dumps(result, indent=2)}")
        
        # Generate user-friendly message
        user_message = mcp_service.generate_user_friendly_error_message("mcp_Gmail_gmail-send-email", result)
        
        print(f"\n💬 User-friendly message:")
        print(f"{user_message}")
        
        # Test 2: List Gmail labels
        print(f"\n📧 Test 2: List Gmail labels...")
        
        labels_instruction = "List all Gmail labels in my account"
        
        labels_args = {
            "instruction": labels_instruction
        }
        
        print(f"📝 Instruction: {labels_instruction}")
        
        # Call the tool
        labels_result = await mcp_service.call_tool("mcp_Gmail_gmail-list-labels", labels_args, server_id)
        
        print(f"\n📄 Labels result:")
        print(f"   Type: {type(labels_result)}")
        print(f"   Content: {json.dumps(labels_result, indent=2)}")
        
        # Generate user-friendly message
        labels_message = mcp_service.generate_user_friendly_error_message("mcp_Gmail_gmail-list-labels", labels_result)
        
        print(f"\n💬 Labels message:")
        print(f"{labels_message}")
        
        # Clean up
        await mcp_service.disconnect_from_server(server_id)
        
        # Summary
        print(f"\n" + "=" * 50)
        print("📊 Gmail Instruction Test Summary")
        print("=" * 50)
        
        if result.get("oauth_required"):
            print(f"🔐 OAuth authentication is required!")
            print(f"   This is expected for first-time Gmail usage")
        elif result.get("success"):
            print(f"✅ Email sending is working!")
        else:
            print(f"❌ Email sending failed:")
            print(f"   Error: {result.get('error', 'Unknown error')}")
        
        if labels_result.get("success"):
            print(f"✅ Gmail labels listing is working!")
        else:
            print(f"❌ Gmail labels listing failed:")
            print(f"   Error: {labels_result.get('error', 'Unknown error')}")
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_gmail_instruction()) 