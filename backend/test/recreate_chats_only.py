#!/usr/bin/env python3
"""
Script to recreate only chat sessions and messages
"""

import asyncio
import uuid
from prisma import Prisma

async def recreate_chats_only():
    """Recreate chat sessions and messages for the test@gmail.com user"""
    print("🔄 Recreating Chat Sessions...")
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
        
        # Create test chat sessions with messages
        print("\n💬 Creating chat sessions...")
        
        # Chat 1: General conversation
        chat1_hash = f"chat_{uuid.uuid4().hex[:16]}"
        chat1 = await prisma.chatsession.create(
            data={
                "userId": user.id,
                "title": "Getting Started with ChatConnect",
                "hash": chat1_hash
            }
        )
        print(f"✅ Created chat: {chat1.title} (Hash: {chat1.hash})")
        
        # Add messages to chat 1
        await prisma.message.create(
            data={
                "chatSessionId": chat1.id,
                "content": "Hello! I'm new to ChatConnect. How can I get started?",
                "role": "user"
            }
        )
        
        await prisma.message.create(
            data={
                "chatSessionId": chat1.id,
                "content": "Welcome to ChatConnect! 🎉\n\nHere's how to get started:\n\n1. **Add MCP Servers**: Go to Settings and add your MCP server URLs\n2. **Configure OAuth**: Set up OAuth for services like Gmail\n3. **Start Chatting**: Begin conversations and use your connected tools\n\nWould you like me to help you set up any specific integrations?",
                "role": "assistant"
            }
        )
        
        await prisma.message.create(
            data={
                "chatSessionId": chat1.id,
                "content": "That sounds great! Can you help me set up Gmail integration?",
                "role": "user"
            }
        )
        
        await prisma.message.create(
            data={
                "chatSessionId": chat1.id,
                "content": "Absolutely! Here's how to set up Gmail integration:\n\n1. **Create Pipedream Workflow**: Go to [Pipedream.com](https://pipedream.com) and create a Gmail MCP workflow\n2. **Get the URL**: Copy the MCP server URL (looks like `https://mcp.pipedream.net/your-workflow-id/gmail`)\n3. **Add to ChatConnect**: Go to Settings → MCP Servers and add the URL\n4. **OAuth Setup**: Click 'Authorize' to set up Gmail OAuth\n5. **Test**: Try sending an email through the chat!\n\nWould you like me to walk you through any of these steps?",
                "role": "assistant"
            }
        )
        
        # Chat 2: MCP Discussion
        chat2_hash = f"chat_{uuid.uuid4().hex[:16]}"
        chat2 = await prisma.chatsession.create(
            data={
                "userId": user.id,
                "title": "MCP Server Configuration",
                "hash": chat2_hash
            }
        )
        print(f"✅ Created chat: {chat2.title} (Hash: {chat2.hash})")
        
        # Add messages to chat 2
        await prisma.message.create(
            data={
                "chatSessionId": chat2.id,
                "content": "What are MCP servers and how do they work?",
                "role": "user"
            }
        )
        
        await prisma.message.create(
            data={
                "chatSessionId": chat2.id,
                "content": "MCP (Model Context Protocol) servers are external tools that AI models can interact with! 🤖\n\n**What they do:**\n- Connect AI to external services (Gmail, Google Drive, databases, etc.)\n- Provide tools and functions the AI can use\n- Handle authentication and data processing\n\n**How they work:**\n1. You add an MCP server URL to ChatConnect\n2. ChatConnect discovers available tools from that server\n3. When you chat, the AI can use those tools\n4. For example, with Gmail MCP, the AI can send emails for you\n\n**Popular MCP servers:**\n- Gmail (email operations)\n- Google Drive (file operations)\n- GitHub (code operations)\n- Custom APIs (your own services)\n\nWould you like me to show you how to add a specific MCP server?",
                "role": "assistant"
            }
        )
        
        # Chat 3: OAuth Discussion
        chat3_hash = f"chat_{uuid.uuid4().hex[:16]}"
        chat3 = await prisma.chatsession.create(
            data={
                "userId": user.id,
                "title": "OAuth Setup Guide",
                "hash": chat3_hash
            }
        )
        print(f"✅ Created chat: {chat3.title} (Hash: {chat3.hash})")
        
        # Add messages to chat 3
        await prisma.message.create(
            data={
                "chatSessionId": chat3.id,
                "content": "How does OAuth work with MCP servers?",
                "role": "user"
            }
        )
        
        await prisma.message.create(
            data={
                "chatSessionId": chat3.id,
                "content": "OAuth is how ChatConnect securely connects to your accounts! 🔐\n\n**OAuth Flow:**\n1. **Add MCP Server**: You add a server URL (like Gmail)\n2. **Authorize**: Click 'Authorize' button\n3. **Redirect**: You're taken to Google to log in\n4. **Permission**: You grant ChatConnect access to your Gmail\n5. **Token Storage**: ChatConnect stores the access token securely\n6. **Future Use**: AI can now use Gmail tools without re-authentication\n\n**Security Features:**\n- Tokens are encrypted and stored securely\n- You can revoke access anytime\n- Each MCP server has its own OAuth setup\n- No passwords are ever stored\n\n**Supported Services:**\n- Google (Gmail, Drive, Calendar)\n- GitHub\n- Custom OAuth providers\n\nReady to set up your first OAuth connection?",
                "role": "assistant"
            }
        )
        
        print(f"\n🎉 Successfully recreated chat data!")
        print(f"📊 Summary:")
        print(f"   - 3 chat sessions created")
        print(f"   - 8 messages created")
        
        print(f"\n🔗 Test URLs:")
        print(f"   - Chat 1: /chat/{chat1.hash}")
        print(f"   - Chat 2: /chat/{chat2.hash}")
        print(f"   - Chat 3: /chat/{chat3.hash}")
        
    except Exception as e:
        print(f"❌ Error recreating chat data: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await prisma.disconnect()

if __name__ == "__main__":
    asyncio.run(recreate_chats_only()) 