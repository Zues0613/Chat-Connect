#!/usr/bin/env python3
"""
Script to populate existing chat sessions with hash values
"""

import asyncio
import uuid
from prisma import Prisma

async def populate_chat_hashes():
    """Populate hash values for existing chat sessions"""
    print("🔧 Populating chat hashes...")
    
    prisma = Prisma()
    await prisma.connect()
    
    try:
        # Get all chats without hash
        chats_without_hash = await prisma.chatsession.find_many(
            where={"hash": None}
        )
        
        print(f"Found {len(chats_without_hash)} chats without hash")
        
        if not chats_without_hash:
            print("✅ All chats already have hash values")
            return
        
        # Update each chat with a unique hash
        for chat in chats_without_hash:
            # Generate a unique hash based on chat ID and timestamp
            unique_hash = f"chat_{chat.id}_{int(chat.createdAt.timestamp())}"
            
            # Update the chat with the hash
            await prisma.chatsession.update(
                where={"id": chat.id},
                data={"hash": unique_hash}
            )
            
            print(f"✅ Updated chat {chat.id} with hash: {unique_hash}")
        
        print(f"🎉 Successfully updated {len(chats_without_hash)} chats")
        
        # Verify all chats now have hashes
        remaining_chats = await prisma.chatsession.find_many(
            where={"hash": None}
        )
        
        if not remaining_chats:
            print("✅ All chats now have hash values")
        else:
            print(f"⚠️  {len(remaining_chats)} chats still missing hash")
            
    except Exception as e:
        print(f"❌ Error populating hashes: {e}")
    finally:
        await prisma.disconnect()

async def test_hash_lookup():
    """Test hash-based chat lookup"""
    print("\n🧪 Testing hash-based lookup...")
    
    prisma = Prisma()
    await prisma.connect()
    
    try:
        # Get a chat with hash
        chat_with_hash = await prisma.chatsession.find_first(
            where={"hash": {"not": None}}
        )
        
        if chat_with_hash:
            print(f"✅ Found chat by hash: {chat_with_hash.hash}")
            print(f"   Chat ID: {chat_with_hash.id}")
            print(f"   Title: {chat_with_hash.title}")
            
            # Test finding by hash
            found_chat = await prisma.chatsession.find_unique(
                where={"hash": chat_with_hash.hash}
            )
            
            if found_chat:
                print(f"✅ Successfully found chat by hash: {found_chat.id}")
            else:
                print("❌ Failed to find chat by hash")
        else:
            print("⚠️  No chats with hash found")
            
    except Exception as e:
        print(f"❌ Error testing hash lookup: {e}")
    finally:
        await prisma.disconnect()

async def main():
    """Main function"""
    print("Chat Hash Population Script")
    print("=" * 30)
    
    # Populate hashes
    await populate_chat_hashes()
    
    # Test hash lookup
    await test_hash_lookup()
    
    print("\n🎉 Script completed!")

if __name__ == "__main__":
    asyncio.run(main()) 