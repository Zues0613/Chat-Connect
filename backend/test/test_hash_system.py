#!/usr/bin/env python3
"""
Test script to verify hash-based system
"""

import asyncio
from prisma import Prisma

async def test_hash_system():
    """Test the hash-based chat system"""
    print("🧪 Testing Hash-Based System...")
    print("=" * 40)
    
    prisma = Prisma()
    await prisma.connect()
    
    try:
        # Get the test user
        user = await prisma.user.find_unique(where={"email": "test@gmail.com"})
        if not user:
            print("❌ Test user not found!")
            return
        
        print(f"✅ Found test user: {user.email}")
        
        # Get all chats
        chats = await prisma.chatsession.find_many(
            where={"userId": user.id}
        )
        
        print(f"📋 Found {len(chats)} chats:")
        for chat in chats:
            print(f"   - Chat {chat.id}: {chat.title} (Hash: {chat.hash})")
            
            # Test finding by hash
            chat_by_hash = await prisma.chatsession.find_unique(
                where={"hash": chat.hash}
            )
            
            if chat_by_hash:
                print(f"     ✅ Found by hash: {chat_by_hash.id}")
                
                # Test getting messages by hash
                chat_with_messages = await prisma.chatsession.find_unique(
                    where={"hash": chat.hash},
                    include={"messages": True}
                )
                
                if chat_with_messages:
                    print(f"     ✅ Found {len(chat_with_messages.messages)} messages")
                else:
                    print(f"     ❌ Failed to get messages")
            else:
                print(f"     ❌ Failed to find by hash")
        
        print(f"\n🎉 Hash-based system test completed!")
        
    except Exception as e:
        print(f"❌ Error testing hash system: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await prisma.disconnect()

if __name__ == "__main__":
    asyncio.run(test_hash_system()) 