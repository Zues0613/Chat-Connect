from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from prisma import Prisma
from typing import List, Dict, Any, Optional
import json
import asyncio

from app.auth.jwt_handler import decode_access_token
from app.services.deepseek_service import deepseek_service
from app.services.mcp_service import mcp_service

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class ChatCreateRequest(BaseModel):
    title: Optional[str] = "New Chat"

class MessageSendRequest(BaseModel):
    content: str
    chatId: int

class ChatTitleUpdateRequest(BaseModel):
    title: str

class ChatResponse(BaseModel):
    id: int
    title: str
    createdAt: str
    updatedAt: str

class MessageResponse(BaseModel):
    id: int
    content: str
    role: str
    createdAt: str

@router.post("/chats", response_model=ChatResponse)
async def create_chat(
    request: ChatCreateRequest,
    token: str = Depends(oauth2_scheme)
):
    """Create a new chat session"""
    try:
        payload = decode_access_token(token)
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token.")
        
        prisma = Prisma()
        await prisma.connect()
        
        # Get user
        user = await prisma.user.find_unique(where={"email": email})
        if not user:
            await prisma.disconnect()
            raise HTTPException(status_code=404, detail="User not found.")
        
        # Create new chat session
        chat = await prisma.chatsession.create(
            data={
                "userId": user.id,
                "title": request.title or "New Chat"
            }
        )
        
        await prisma.disconnect()
        
        return ChatResponse(
            id=chat.id,
            title=chat.title or "New Chat",
            createdAt=chat.createdAt.isoformat(),
            updatedAt=chat.updatedAt.isoformat()
        )
        
    except Exception as e:
        print(f"[ERROR] Failed to create chat: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create chat: {e}")

@router.put("/chats/{chat_id}/title")
async def update_chat_title(
    chat_id: int,
    request: ChatTitleUpdateRequest,
    token: str = Depends(oauth2_scheme)
):
    """Update chat title"""
    try:
        payload = decode_access_token(token)
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token.")
        
        prisma = Prisma()
        await prisma.connect()
        
        # Get user
        user = await prisma.user.find_unique(where={"email": email})
        if not user:
            await prisma.disconnect()
            raise HTTPException(status_code=404, detail="User not found.")
        
        # Verify chat belongs to user and update title
        chat = await prisma.chatsession.update_many(
            where={"id": chat_id, "userId": user.id},
            data={"title": request.title}
        )
        
        if chat.count == 0:
            await prisma.disconnect()
            raise HTTPException(status_code=404, detail="Chat not found.")
        
        await prisma.disconnect()
        
        return {"message": "Chat title updated successfully"}
        
    except Exception as e:
        print(f"[ERROR] Failed to update chat title: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update chat title: {e}")

@router.delete("/chats/{chat_id}")
async def delete_chat(
    chat_id: int,
    token: str = Depends(oauth2_scheme)
):
    """Delete a chat and all its messages"""
    try:
        payload = decode_access_token(token)
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token.")
        
        prisma = Prisma()
        await prisma.connect()
        
        # Get user
        user = await prisma.user.find_unique(where={"email": email})
        if not user:
            await prisma.disconnect()
            raise HTTPException(status_code=404, detail="User not found.")
        
        # Verify chat belongs to user
        chat = await prisma.chatsession.find_first(
            where={"id": chat_id, "userId": user.id}
        )
        
        if not chat:
            await prisma.disconnect()
            raise HTTPException(status_code=404, detail="Chat not found.")
        
        # Delete all messages in the chat first (due to foreign key constraint)
        await prisma.message.delete_many(
            where={"chatSessionId": chat_id}
        )
        
        # Delete the chat session
        await prisma.chatsession.delete(
            where={"id": chat_id}
        )
        
        await prisma.disconnect()
        
        return {"message": "Chat deleted successfully"}
        
    except Exception as e:
        print(f"[ERROR] Failed to delete chat: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete chat: {e}")

async def generate_chat_title(first_message: str, deepseek_api_key: str) -> str:
    """Generate a title for the chat based on the first message"""
    try:
        # Initialize DeepSeek with the API key
        if not deepseek_service.initialize_with_api_key(deepseek_api_key):
            return "New Chat"
        
        # Create a simple prompt to generate a title
        title_prompt = f"""Generate a short, descriptive title (maximum 50 characters) for a chat that starts with this message: "{first_message}"

The title should be:
- Descriptive but concise
- Professional and clear
- Maximum 50 characters
- No quotes or special formatting

Return only the title, nothing else."""

        # Send the title generation request
        response = await deepseek_service.send_message(title_prompt)
        
        if response.get("content"):
            title = response["content"].strip()
            # Clean up the title - remove quotes, extra spaces, etc.
            title = title.replace('"', '').replace("'", "").strip()
            # Limit to 50 characters
            if len(title) > 50:
                title = title[:47] + "..."
            return title if title else "New Chat"
        else:
            return "New Chat"
            
    except Exception as e:
        print(f"[ERROR] Failed to generate chat title: {e}")
        return "New Chat"

@router.get("/chats")
async def list_chats(token: str = Depends(oauth2_scheme)):
    """Get all chat sessions for the user"""
    try:
        payload = decode_access_token(token)
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token.")
        
        prisma = Prisma()
        await prisma.connect()
        
        # Get user
        user = await prisma.user.find_unique(where={"email": email})
        if not user:
            await prisma.disconnect()
            raise HTTPException(status_code=404, detail="User not found.")
        
        # Get all chats for user
        chats = await prisma.chatsession.find_many(
            where={"userId": user.id}
        )
        # Sort chats by updatedAt in descending order
        chats.sort(key=lambda x: x.updatedAt, reverse=True)
        
        await prisma.disconnect()
        
        return [
            ChatResponse(
                id=chat.id,
                title=chat.title or "New Chat",
                createdAt=chat.createdAt.isoformat(),
                updatedAt=chat.updatedAt.isoformat()
            )
            for chat in chats
        ]
        
    except Exception as e:
        print(f"[ERROR] Failed to list chats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list chats: {e}")

@router.get("/chats/{chat_id}/messages")
async def get_chat_messages(
    chat_id: int,
    token: str = Depends(oauth2_scheme)
):
    """Get all messages for a specific chat"""
    try:
        payload = decode_access_token(token)
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token.")
        
        prisma = Prisma()
        await prisma.connect()
        
        # Get user
        user = await prisma.user.find_unique(where={"email": email})
        if not user:
            await prisma.disconnect()
            raise HTTPException(status_code=404, detail="User not found.")
        
        # Verify chat belongs to user
        chat = await prisma.chatsession.find_unique(
            where={"id": chat_id},
            include={"messages": True}
        )
        
        if not chat or chat.userId != user.id:
            await prisma.disconnect()
            raise HTTPException(status_code=404, detail="Chat not found.")
        
        # Sort messages by createdAt in ascending order
        sorted_messages = sorted(chat.messages, key=lambda x: x.createdAt)
        
        await prisma.disconnect()
        
        return [
            MessageResponse(
                id=msg.id,
                content=msg.content,
                role=msg.role,
                createdAt=msg.createdAt.isoformat()
            )
            for msg in sorted_messages
        ]
        
    except Exception as e:
        print(f"[ERROR] Failed to get messages: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get messages: {e}")

async def get_user_deepseek_api_key(email: str) -> Optional[str]:
    """Get user's DeepSeek API key from their stored API keys, or return default"""
    try:
        prisma = Prisma()
        await prisma.connect()
        
        user = await prisma.user.find_unique(where={"email": email})
        if not user:
            await prisma.disconnect()
            # Return default key if user not found
            import os
            return os.getenv("DEFAULT_DEEPSEEK_API_KEY")
        
        # Find user's DeepSeek API key
        deepseek_key = await prisma.apikey.find_first(
            where={
                "userId": user.id,
                "provider": "deepseek"
            }
        )
        
        await prisma.disconnect()
        
        if deepseek_key and deepseek_key.value:
            return deepseek_key.value
        else:
            # Fallback to default key if user hasn't set one
            import os
            default_key = os.getenv("DEFAULT_DEEPSEEK_API_KEY")
            print(f"[INFO] Using default DeepSeek API key for user: {email}")
            return default_key
        
    except Exception as e:
        print(f"[ERROR] Failed to get DeepSeek API key: {e}")
        # Fallback to default key on error
        import os
        return os.getenv("DEFAULT_DEEPSEEK_API_KEY")

async def initialize_mcp_servers(user_id: int) -> None:
    """Initialize all MCP servers for the user"""
    try:
        prisma = Prisma()
        await prisma.connect()
        
        # Get all MCP servers for user
        servers = await prisma.mcpserver.find_many(where={"userId": user_id})
        
        await prisma.disconnect()
        
        # Connect to each server
        for server in servers:
            server_id = f"user_{user_id}_server_{server.id}"
            await mcp_service.connect_to_server(server_id, server.config)
        
    except Exception as e:
        print(f"[ERROR] Failed to initialize MCP servers: {e}")

@router.post("/chats/{chat_id}/messages")
async def send_message(
    chat_id: int,
    request: MessageSendRequest,
    token: str = Depends(oauth2_scheme)
):
    """Send a message and get AI response"""
    try:
        payload = decode_access_token(token)
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token.")
        
        prisma = Prisma()
        await prisma.connect()
        
        # Get user
        user = await prisma.user.find_unique(where={"email": email})
        if not user:
            await prisma.disconnect()
            raise HTTPException(status_code=404, detail="User not found.")
        
        # Verify chat belongs to user
        chat = await prisma.chatsession.find_unique(
            where={"id": chat_id},
            include={"messages": True}
        )
        
        if not chat or chat.userId != user.id:
            await prisma.disconnect()
            raise HTTPException(status_code=404, detail="Chat not found.")
        
        # Get user's DeepSeek API key (or default) - needed for title generation and chat
        deepseek_api_key = await get_user_deepseek_api_key(email)
        if not deepseek_api_key:
            await prisma.disconnect()
            raise HTTPException(status_code=400, detail="No DeepSeek API key available. Please contact administrator or add your own API key in settings.")
        
        # Store user message
        user_message = await prisma.message.create(
            data={
                "chatSessionId": chat_id,
                "content": request.content,
                "role": "user"
            }
        )
        
        # Generate title for new chats (if this is the first message)
        if len(chat.messages) == 0 and (chat.title == "New Chat" or not chat.title):
            # This is the first message in a new chat, generate a title
            generated_title = await generate_chat_title(request.content, deepseek_api_key)
            if generated_title and generated_title != "New Chat":
                await prisma.chatsession.update(
                    where={"id": chat_id},
                    data={"title": generated_title}
                )
        
        # Initialize DeepSeek with user's API key
        if not deepseek_service.initialize_with_api_key(deepseek_api_key):
            await prisma.disconnect()
            raise HTTPException(status_code=400, detail="Failed to initialize DeepSeek API.")
        
        # Prepare chat history for Gemini
        history = []
        # Sort messages by createdAt in ascending order
        sorted_messages = sorted(chat.messages, key=lambda x: x.createdAt)
        for msg in sorted_messages:
            history.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # Add the new user message to history
        history.append({
            "role": "user",
            "content": request.content
        })
        
        # Start chat session with history
        if not deepseek_service.start_chat_session(history[:-1]):  # Exclude the last message as we'll send it
            await prisma.disconnect()
            raise HTTPException(status_code=500, detail="Failed to start chat session.")
        
        # Initialize MCP servers for this user
        await initialize_mcp_servers(user.id)
        
        # Get available tools from MCP servers
        available_tools = mcp_service.get_all_tools()
        
        # Send message to DeepSeek
        response = await deepseek_service.send_message(request.content, available_tools)
        
        # Handle different response types
        if response.get("type") == "function_call":
            # DeepSeek wants to call a tool
            tool_name = response["function_name"]
            tool_args = response["function_args"]
            
            # Call the MCP tool
            tool_result = await mcp_service.call_tool(tool_name, tool_args)
            
            # Send tool result back to DeepSeek
            final_response = deepseek_service.send_function_result(tool_name, tool_result)
            assistant_content = final_response.get("content", "Tool executed successfully.")
            
        elif response.get("error"):
            assistant_content = f"I encountered an error: {response['error']}"
        else:
            assistant_content = response.get("content", "I'm sorry, I couldn't generate a response.")
        
        # Store assistant message
        assistant_message = await prisma.message.create(
            data={
                "chatSessionId": chat_id,
                "content": assistant_content,
                "role": "assistant"
            }
        )
        
        await prisma.disconnect()
        
        return {
            "user_message": MessageResponse(
                id=user_message.id,
                content=user_message.content,
                role=user_message.role,
                createdAt=user_message.createdAt.isoformat()
            ),
            "assistant_message": MessageResponse(
                id=assistant_message.id,
                content=assistant_message.content,
                role=assistant_message.role,
                createdAt=assistant_message.createdAt.isoformat()
            )
        }
        
    except Exception as e:
        print(f"[ERROR] Failed to send message: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send message: {e}")

@router.post("/chats/{chat_id}/messages/stream")
async def send_message_stream(
    chat_id: int,
    request: MessageSendRequest,
    token: str = Depends(oauth2_scheme)
):
    """Send a message and stream the AI response"""
    async def generate_response():
        try:
            payload = decode_access_token(token)
            email = payload.get("sub")
            if not email:
                yield f"data: {json.dumps({'error': 'Invalid token'})}\n\n"
                return
            
            # Similar setup as send_message but with streaming
            prisma = Prisma()
            await prisma.connect()
            
            user = await prisma.user.find_unique(where={"email": email})
            if not user:
                yield f"data: {json.dumps({'error': 'User not found'})}\n\n"
                return
            
            chat = await prisma.chatsession.find_unique(
                where={"id": chat_id},
                include={"messages": {"order_by": {"createdAt": "asc"}}}
            )
            
            if not chat or chat.userId != user.id:
                yield f"data: {json.dumps({'error': 'Chat not found'})}\n\n"
                return
            
            # Store user message
            user_message = await prisma.message.create(
                data={
                    "chatSessionId": chat_id,
                    "content": request.content,
                    "role": "user"
                }
            )
            
            yield f"data: {json.dumps({'type': 'user_message', 'message': {'id': user_message.id, 'content': user_message.content, 'role': 'user'}})}\n\n"
            
            # Get Gemini API key and initialize
            gemini_api_key = await get_user_gemini_api_key(email)
            if not gemini_api_key:
                yield f"data: {json.dumps({'error': 'No Gemini API key available. Please contact administrator or add your own API key in settings.'})}\n\n"
                return
            
            if not gemini_service.initialize_with_api_key(gemini_api_key):
                yield f"data: {json.dumps({'error': 'Failed to initialize Gemini'})}\n\n"
                return
            
            # Prepare history and start session
            history = [{"role": msg.role, "content": msg.content} for msg in chat.messages]
            history.append({"role": "user", "content": request.content})
            
            if not gemini_service.start_chat_session(history[:-1]):
                yield f"data: {json.dumps({'error': 'Failed to start chat session'})}\n\n"
                return
            
            # Initialize MCP and get tools
            await initialize_mcp_servers(user.id)
            available_tools = mcp_service.get_all_tools()
            
            # Stream response from Gemini
            full_response = ""
            async for chunk in gemini_service.send_message_stream(request.content, available_tools):
                chunk_data = json.loads(chunk)
                if chunk_data.get("type") == "text_chunk":
                    full_response += chunk_data["content"]
                    yield f"data: {chunk}\n\n"
                elif chunk_data.get("type") == "complete":
                    # Store the complete assistant message
                    assistant_message = await prisma.message.create(
                        data={
                            "chatSessionId": chat_id,
                            "content": full_response,
                            "role": "assistant"
                        }
                    )
                    yield f"data: {json.dumps({'type': 'complete', 'message_id': assistant_message.id})}\n\n"
                else:
                    yield f"data: {chunk}\n\n"
            
            await prisma.disconnect()
            
        except Exception as e:
            yield f"data: {json.dumps({'error': f'Stream failed: {str(e)}'})}\n\n"
    
    return StreamingResponse(
        generate_response(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

@router.get("/mcp/tools")
async def get_available_tools(token: str = Depends(oauth2_scheme)):
    """Get all available MCP tools for the user"""
    try:
        payload = decode_access_token(token)
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token.")
        
        # Get all available tools from connected MCP servers
        tools = mcp_service.get_all_tools()
        connected_servers = mcp_service.get_connected_servers()
        
        return {
            "tools": tools,
            "connected_servers": connected_servers
        }
        
    except Exception as e:
        print(f"[ERROR] Failed to get tools: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get tools: {e}")

@router.post("/mcp/servers/{server_id}/connect")
async def connect_mcp_server(
    server_id: int,
    token: str = Depends(oauth2_scheme)
):
    """Connect to a specific MCP server"""
    try:
        payload = decode_access_token(token)
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token.")
        
        prisma = Prisma()
        await prisma.connect()
        
        user = await prisma.user.find_unique(where={"email": email})
        if not user:
            await prisma.disconnect()
            raise HTTPException(status_code=404, detail="User not found.")
        
        # Get the MCP server
        server = await prisma.mcpserver.find_unique(where={"id": server_id})
        if not server or server.userId != user.id:
            await prisma.disconnect()
            raise HTTPException(status_code=404, detail="MCP server not found.")
        
        await prisma.disconnect()
        
        # Connect to the server
        connection_id = f"user_{user.id}_server_{server.id}"
        success = await mcp_service.connect_to_server(connection_id, server.config)
        
        if success:
            return {"status": "connected", "server_id": connection_id}
        else:
            raise HTTPException(status_code=500, detail="Failed to connect to MCP server")
        
    except Exception as e:
        print(f"[ERROR] Failed to connect MCP server: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to connect: {e}") 