#!/usr/bin/env python3
"""
Script to add simple MCP servers to the database for testing ChatConnect functionality.

This script creates three simple MCP servers:
1. Calculator - Basic arithmetic operations
2. Weather Simulator - Simulated weather data
3. File Operations - Simple file read/write operations

Usage:
    python add_test_mcp_servers.py [user_email]
"""

import asyncio
import sys
import os
from prisma import Prisma

# Simple MCP server configurations
TEST_MCP_SERVERS = [
    {
        "name": "Calculator",
        "description": "Simple calculator with basic arithmetic operations",
        "config": {
            "type": "custom",
            "uri": "http://localhost:8001/calculator",
            "transport": "http",
            "name": "Calculator"
        }
    },
    {
        "name": "Weather Simulator", 
        "description": "Simulate weather data for testing purposes",
        "config": {
            "type": "custom",
            "uri": "http://localhost:8001/weather",
            "transport": "http",
            "name": "Weather Simulator"
        }
    },
    {
        "name": "File Operations",
        "description": "Simple file operations for testing",
        "config": {
            "type": "custom",
            "uri": "http://localhost:8001/files",
            "transport": "http",
            "name": "File Operations"
        }
    },
    {
        "name": "Combined Test Server",
        "description": "All test tools combined in one server",
        "config": {
            "type": "custom",
            "uri": "http://localhost:8001/mcp",
            "transport": "http",
            "name": "Combined Test Server"
        }
    }
]

async def add_test_mcp_servers(user_email: str = None):
    """Add test MCP servers to the database"""
    
    prisma = Prisma()
    await prisma.connect()
    
    try:
        # If no email provided, use the first user in the database
        if not user_email:
            user = await prisma.user.find_first()
            if not user:
                print("❌ No users found in database. Please create a user first.")
                return
            user_email = user.email
            print(f"📧 Using first user: {user_email}")
        else:
            user = await prisma.user.find_unique(where={"email": user_email})
            if not user:
                print(f"❌ User with email {user_email} not found.")
                return
        
        print(f"👤 Adding MCP servers for user: {user_email}")
        
        # Check if servers already exist
        existing_servers = await prisma.mcpserver.find_many(where={"userId": user.id})
        existing_names = [server.name for server in existing_servers]
        
        added_count = 0
        skipped_count = 0
        
        for server_config in TEST_MCP_SERVERS:
            if server_config["name"] in existing_names:
                print(f"⏭️  Skipping {server_config['name']} - already exists")
                skipped_count += 1
                continue
            
            # Create the MCP server
            server = await prisma.mcpserver.create(
                data={
                    "userId": user.id,
                    "name": server_config["name"],
                    "description": server_config["description"],
                    "config": server_config["config"]
                }
            )
            
            print(f"✅ Added MCP server: {server_config['name']}")
            print(f"   URI: {server_config['config']['uri']}")
            print(f"   ID: {server.id}")
            added_count += 1
        
        print(f"\n📊 Summary:")
        print(f"   Added: {added_count} servers")
        print(f"   Skipped: {skipped_count} servers (already exist)")
        print(f"   Total: {len(existing_servers) + added_count} servers")
        
        if added_count > 0:
            print(f"\n🚀 Next steps:")
            print(f"   1. Start the simple MCP servers:")
            print(f"      python -m app.services.simple_mcp_servers")
            print(f"   2. Test the servers in ChatConnect")
            print(f"   3. Try asking the AI to use calculator or weather tools")
        
    except Exception as e:
        print(f"❌ Error adding MCP servers: {e}")
        raise
    finally:
        await prisma.disconnect()

async def list_mcp_servers(user_email: str = None):
    """List all MCP servers for a user"""
    
    prisma = Prisma()
    await prisma.connect()
    
    try:
        if not user_email:
            user = await prisma.user.find_first()
            if not user:
                print("❌ No users found in database.")
                return
            user_email = user.email
        else:
            user = await prisma.user.find_unique(where={"email": user_email})
            if not user:
                print(f"❌ User with email {user_email} not found.")
                return
        
        servers = await prisma.mcpserver.find_many(where={"userId": user.id})
        
        print(f"📋 MCP Servers for {user_email}:")
        print(f"{'ID':<5} {'Name':<25} {'Type':<15} {'URI':<50}")
        print("-" * 95)
        
        for server in servers:
            config = server.config
            server_type = config.get("type", "unknown")
            uri = config.get("uri", "N/A")
            print(f"{server.id:<5} {server.name:<25} {server_type:<15} {uri:<50}")
        
        print(f"\nTotal: {len(servers)} servers")
        
    except Exception as e:
        print(f"❌ Error listing MCP servers: {e}")
    finally:
        await prisma.disconnect()

async def delete_test_mcp_servers(user_email: str = None):
    """Delete test MCP servers from the database"""
    
    prisma = Prisma()
    await prisma.connect()
    
    try:
        if not user_email:
            user = await prisma.user.find_first()
            if not user:
                print("❌ No users found in database.")
                return
            user_email = user.email
        else:
            user = await prisma.user.find_unique(where={"email": user_email})
            if not user:
                print(f"❌ User with email {user_email} not found.")
                return
        
        # Find test servers
        test_server_names = [server["name"] for server in TEST_MCP_SERVERS]
        servers = await prisma.mcpserver.find_many(
            where={
                "userId": user.id,
                "name": {"in": test_server_names}
            }
        )
        
        if not servers:
            print(f"❌ No test MCP servers found for {user_email}")
            return
        
        print(f"🗑️  Deleting {len(servers)} test MCP servers for {user_email}:")
        
        for server in servers:
            await prisma.mcpserver.delete(where={"id": server.id})
            print(f"   ✅ Deleted: {server.name}")
        
        print(f"✅ Successfully deleted {len(servers)} test servers")
        
    except Exception as e:
        print(f"❌ Error deleting MCP servers: {e}")
    finally:
        await prisma.disconnect()

def print_usage():
    """Print usage information"""
    print("""
🔧 ChatConnect Test MCP Servers Management

Usage:
    python add_test_mcp_servers.py [command] [user_email]

Commands:
    add [email]     - Add test MCP servers (default command)
    list [email]    - List all MCP servers for a user
    delete [email]  - Delete test MCP servers
    help            - Show this help message

Examples:
    python add_test_mcp_servers.py add user@example.com
    python add_test_mcp_servers.py list
    python add_test_mcp_servers.py delete user@example.com

If no email is provided, the first user in the database will be used.
    """)

async def main():
    """Main function"""
    
    if len(sys.argv) < 2 or sys.argv[1] in ["help", "-h", "--help"]:
        print_usage()
        return
    
    command = sys.argv[1].lower()
    user_email = sys.argv[2] if len(sys.argv) > 2 else None
    
    if command == "add":
        await add_test_mcp_servers(user_email)
    elif command == "list":
        await list_mcp_servers(user_email)
    elif command == "delete":
        await delete_test_mcp_servers(user_email)
    else:
        print(f"❌ Unknown command: {command}")
        print_usage()

if __name__ == "__main__":
    asyncio.run(main()) 