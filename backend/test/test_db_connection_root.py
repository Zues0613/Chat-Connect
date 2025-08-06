#!/usr/bin/env python3
"""
Simple database connection test
"""

import asyncio
import os
from prisma import Prisma

async def test_db_connection():
    """Test database connection and basic operations"""
    print("🔍 Testing Database Connection...")
    
    try:
        # Test 1: Basic connection
        print("1. Testing basic connection...")
        prisma = Prisma()
        await prisma.connect()
        print("✅ Database connection successful")
        
        # Test 2: Simple query
        print("2. Testing simple query...")
        users = await prisma.user.find_many(take=1)
        print(f"✅ Found {len(users)} users")
        
        # Test 3: Chat query
        print("3. Testing chat query...")
        chats = await prisma.chatsession.find_many(take=5)
        print(f"✅ Found {len(chats)} chats")
        
        # Test 4: Message query with include
        print("4. Testing message query with include...")
        if chats:
            chat_with_messages = await prisma.chatsession.find_unique(
                where={"id": chats[0].id},
                include={"messages": True}
            )
            if chat_with_messages:
                print(f"✅ Found chat with {len(chat_with_messages.messages)} messages")
            else:
                print("⚠️  No messages found for first chat")
        else:
            print("⚠️  No chats found to test messages")
        
        await prisma.disconnect()
        print("✅ Database disconnected successfully")
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False
    
    return True

async def test_specific_chat(chat_id: int):
    """Test getting messages for a specific chat"""
    print(f"\n🔍 Testing specific chat {chat_id}...")
    
    try:
        prisma = Prisma()
        await prisma.connect()
        
        # Get chat with messages
        chat = await prisma.chatsession.find_unique(
            where={"id": chat_id},
            include={"messages": True}
        )
        
        if chat:
            print(f"✅ Found chat: {chat.title}")
            print(f"✅ Messages count: {len(chat.messages)}")
            
            # Sort messages
            sorted_messages = sorted(chat.messages, key=lambda x: x.createdAt)
            print(f"✅ Sorted {len(sorted_messages)} messages")
            
            # Show first few messages
            for i, msg in enumerate(sorted_messages[:3]):
                print(f"   Message {i+1}: {msg.role} - {msg.content[:50]}...")
        else:
            print(f"❌ Chat {chat_id} not found")
        
        await prisma.disconnect()
        
    except Exception as e:
        print(f"❌ Chat test failed: {e}")

async def main():
    """Main test function"""
    print("Database Connection Test")
    print("=" * 30)
    
    # Test basic connection
    success = await test_db_connection()
    
    if success:
        # Test specific chat if provided
        chat_id_input = input("\nEnter a chat ID to test (or press Enter to skip): ").strip()
        if chat_id_input:
            try:
                chat_id = int(chat_id_input)
                await test_specific_chat(chat_id)
            except ValueError:
                print("❌ Invalid chat ID")
    
    print("\n🎉 Database test completed!")

if __name__ == "__main__":
    asyncio.run(main()) 