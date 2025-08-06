#!/usr/bin/env python3
"""
Check MCP Configuration

This script checks your MCP server configuration to help diagnose issues.
"""

import json
import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

try:
    from prisma import Prisma
    print("✅ Prisma import successful")
except ImportError as e:
    print(f"❌ Prisma import failed: {e}")
    print("Make sure you have installed the requirements: pip install -r requirements.txt")
    sys.exit(1)

async def check_mcp_config():
    """Check MCP server configuration"""
    print("🔍 Checking MCP Server Configuration")
    print("=" * 45)
    
    try:
        # Initialize Prisma
        prisma = Prisma()
        await prisma.connect()
        print("✅ Database connection successful")
        
        # Get all MCP servers
        servers = await prisma.mcpserver.find_many()
        print(f"\n📊 Found {len(servers)} MCP server(s) in database")
        
        if not servers:
            print("❌ No MCP servers found!")
            print("   You need to add MCP servers through the settings page first.")
            print("   Go to: http://localhost:3000/settings?tab=mcp-servers")
            await prisma.disconnect()
            return
        
        # Display each server's configuration
        for i, server in enumerate(servers, 1):
            print(f"\n{i}. Server: {server.name}")
            print(f"   ID: {server.id}")
            print(f"   User ID: {server.userId}")
            print(f"   Description: {server.description or 'None'}")
            print(f"   Created: {server.createdAt}")
            
            # Parse and display config
            try:
                if isinstance(server.config, str):
                    config = json.loads(server.config)
                    print(f"   Config (parsed from JSON):")
                else:
                    config = server.config
                    print(f"   Config (direct):")
                
                print(f"     Type: {config.get('type', 'Unknown')}")
                print(f"     URI: {config.get('uri', 'None')}")
                print(f"     Transport: {config.get('transport', 'Unknown')}")
                
                # Validate config
                if not config.get('uri'):
                    print(f"     ❌ Missing URI!")
                if not config.get('type'):
                    print(f"     ❌ Missing type!")
                    
            except json.JSONDecodeError as e:
                print(f"   ❌ Config parsing error: {e}")
                print(f"   Raw config: {server.config}")
            except Exception as e:
                print(f"   ❌ Config error: {e}")
        
        await prisma.disconnect()
        
        # Summary
        print(f"\n" + "=" * 45)
        print("📊 Configuration Summary")
        print("=" * 45)
        
        print(f"• Total MCP servers: {len(servers)}")
        
        # Check for common issues
        issues = []
        for server in servers:
            try:
                if isinstance(server.config, str):
                    config = json.loads(server.config)
                else:
                    config = server.config
                
                if not config.get('uri'):
                    issues.append(f"Server '{server.name}' has no URI")
                if not config.get('type'):
                    issues.append(f"Server '{server.name}' has no type")
                    
            except:
                issues.append(f"Server '{server.name}' has invalid config")
        
        if issues:
            print(f"\n❌ Issues found:")
            for issue in issues:
                print(f"   • {issue}")
        else:
            print(f"\n✅ All servers have valid configurations")
        
        print(f"\n💡 Next steps:")
        print(f"   1. If you have MCP servers configured, try sending a message in chat")
        print(f"   2. Check the server logs for connection attempts")
        print(f"   3. Verify your MCP server URLs are correct and accessible")
        print(f"   4. Ensure your MCP servers are running")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure your database is running and properly configured.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(check_mcp_config()) 