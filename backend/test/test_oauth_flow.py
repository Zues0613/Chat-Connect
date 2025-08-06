#!/usr/bin/env python3
"""
Test OAuth Flow for Gmail

This script tests the OAuth authentication flow for Gmail MCP integration.
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

async def test_oauth_flow():
    """Test the OAuth authentication flow"""
    print("🔐 Testing OAuth Authentication Flow")
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
        server_id = f"test_oauth_{server.id}"
        
        await prisma.disconnect()
        
        # Connect to MCP server
        print(f"\n🔗 Connecting to MCP server...")
        success = await mcp_service.connect_to_server(server_id, config)
        
        if not success:
            print("❌ Failed to connect to MCP server")
            return
        
        print("✅ Connected to MCP server")
        
        # Test Gmail send email (this should trigger OAuth flow)
        print(f"\n📧 Testing Gmail send email (should trigger OAuth)...")
        
        email_args = {
            "to": "test@example.com",
            "subject": "Test Email",
            "body": "This is a test email to trigger OAuth flow"
        }
        
        print(f"📝 Arguments: {json.dumps(email_args, indent=2)}")
        
        # Call the tool
        result = await mcp_service.call_tool("gmail-send-email", email_args, server_id)
        
        print(f"\n📄 Tool call result:")
        print(f"   Type: {type(result)}")
        print(f"   Content: {json.dumps(result, indent=2)}")
        
        # Generate user-friendly message
        user_message = mcp_service.generate_user_friendly_error_message("gmail-send-email", result)
        
        print(f"\n💬 User-friendly message:")
        print(f"{user_message}")
        
        # Check if OAuth is required
        if result.get("oauth_required"):
            print(f"\n🔐 OAuth Authentication Required!")
            print(f"   This is expected behavior for first-time Gmail usage")
            print(f"   The user should click the provided link to authenticate")
        elif result.get("success"):
            print(f"\n✅ Email sent successfully!")
        else:
            print(f"\n❌ Tool call failed")
            print(f"   Error: {result.get('error', 'Unknown error')}")
        
        # Clean up
        await mcp_service.disconnect_from_server(server_id)
        
        # Summary
        print(f"\n" + "=" * 50)
        print("📊 OAuth Flow Test Summary")
        print("=" * 50)
        
        if result.get("oauth_required"):
            print(f"✅ OAuth flow is working correctly!")
            print(f"   • MCP server is connected")
            print(f"   • Tool call is properly formatted")
            print(f"   • OAuth authentication is being requested")
            print(f"   • User-friendly message is generated")
        elif result.get("success"):
            print(f"✅ Gmail integration is working!")
            print(f"   • OAuth authentication is already complete")
            print(f"   • Email sending is functional")
        else:
            print(f"❌ There's still an issue:")
            print(f"   • Check Pipedream workflow configuration")
            print(f"   • Verify Gmail API credentials")
            print(f"   • Check workflow logs for errors")
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_oauth_flow()) 