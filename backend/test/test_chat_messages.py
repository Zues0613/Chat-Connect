import asyncio
import sys
import os

# Add the parent directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from prisma import Prisma

async def test_chat_messages():
    prisma = Prisma()
    await prisma.connect()
    
    try:
        # Get all chat sessions
        chat_sessions = await prisma.chatsession.find_many()
        print(f"Total chat sessions in database: {len(chat_sessions)}")
        
        if chat_sessions:
            print("\nChat Sessions found:")
            for chat in chat_sessions:
                print(f"- Chat ID: {chat.id}, Title: {chat.title}, User ID: {chat.userId}")
                
                # Get messages for this chat
                messages = await prisma.message.find_many(where={"chatSessionId": chat.id})
                print(f"  Messages: {len(messages)}")
                for msg in messages:
                    print(f"    - {msg.role}: {msg.content[:50]}...")
                print()
        else:
            print("No chat sessions found in database")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await prisma.disconnect()

if __name__ == "__main__":
    asyncio.run(test_chat_messages()) 