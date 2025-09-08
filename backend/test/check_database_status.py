#!/usr/bin/env python3
"""
Script to check database status after reset
"""

import asyncio
from prisma import Prisma

async def check_database():
    """Check what data exists in the database"""
    print("🔍 Checking Database Status...")
    print("=" * 40)
    
    prisma = Prisma()
    await prisma.connect()
    
    try:
        # Check users
        users = await prisma.user.find_many()
        print(f"👥 Users: {len(users)}")
        for user in users:
            print(f"   - {user.email} (ID: {user.id})")
        
        # Check chat sessions
        chats = await prisma.chatsession.find_many()
        print(f"💬 Chat Sessions: {len(chats)}")
        for chat in chats:
            print(f"   - Chat {chat.id}: {chat.title} (Hash: {chat.hash})")
        
        # Check MCP servers
        servers = await prisma.mcpserver.find_many()
        print(f"🔧 MCP Servers: {len(servers)}")
        for server in servers:
            print(f"   - {server.name}: {server.description}")
        
        # Check messages
        messages = await prisma.message.find_many()
        print(f"💭 Messages: {len(messages)}")
        
        # Check API keys
        api_keys = await prisma.apikey.find_many()
        print(f"🔑 API Keys: {len(api_keys)}")
        
        # Check OAuth tokens
        oauth_tokens = await prisma.oauthtoken.find_many()
        print(f"🔐 OAuth Tokens: {len(oauth_tokens)}")
        
        print("\n" + "=" * 40)
        
        if len(users) == 0:
            print("❌ DATABASE IS EMPTY - All data was lost!")
            print("💡 You'll need to recreate your account and data")
        elif len(chats) == 0:
            print("⚠️  No chat sessions found - chats were lost")
        else:
            print("✅ Database has some data")
            
    except Exception as e:
        print(f"❌ Error checking database: {e}")
    finally:
        await prisma.disconnect()

if __name__ == "__main__":
    asyncio.run(check_database()) 