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
from app.services.mcp_service_deepseek import mcp_service_deepseek

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
    hash: str

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
        
        # Create new chat session with hash
        import uuid
        chat_hash = f"chat_{uuid.uuid4().hex[:16]}"
        
        chat = await prisma.chatsession.create(
            data={
                "userId": user.id,
                "title": request.title or "New Chat",
                "hash": chat_hash
            }
        )
        
        await prisma.disconnect()
        
        return ChatResponse(
            id=chat.id,
            title=chat.title or "New Chat",
            createdAt=chat.createdAt.isoformat(),
            updatedAt=chat.updatedAt.isoformat(),
            hash=chat.hash
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
                updatedAt=chat.updatedAt.isoformat(),
                hash=chat.hash or f"chat_{chat.id}"
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
    prisma = None
    try:
        print(f"[DEBUG] Getting messages for chat {chat_id}")
        
        payload = decode_access_token(token)
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token.")
        
        prisma = Prisma()
        await prisma.connect()
        print(f"[DEBUG] Connected to database")
        
        # Get user
        user = await prisma.user.find_unique(where={"email": email})
        if not user:
            await prisma.disconnect()
            raise HTTPException(status_code=404, detail="User not found.")
        
        print(f"[DEBUG] Found user: {user.email}")
        
        # Verify chat belongs to user and get messages
        chat = await prisma.chatsession.find_unique(
            where={"id": chat_id},
            include={"messages": True}
        )
        
        if not chat:
            await prisma.disconnect()
            raise HTTPException(status_code=404, detail="Chat not found.")
        
        if chat.userId != user.id:
            await prisma.disconnect()
            raise HTTPException(status_code=403, detail="Access denied.")
        
        print(f"[DEBUG] Found chat with {len(chat.messages)} messages")
        
        # Sort messages by createdAt in ascending order
        sorted_messages = sorted(chat.messages, key=lambda x: x.createdAt)
        
        await prisma.disconnect()
        print(f"[DEBUG] Disconnected from database")
        
        result = [
            MessageResponse(
                id=msg.id,
                content=msg.content,
                role=msg.role,
                createdAt=msg.createdAt.isoformat()
            )
            for msg in sorted_messages
        ]
        
        print(f"[DEBUG] Returning {len(result)} messages")
        return result
        
    except Exception as e:
        print(f"[ERROR] Failed to get messages for chat {chat_id}: {e}")
        if prisma:
            try:
                await prisma.disconnect()
            except:
                pass
        raise HTTPException(status_code=500, detail=f"Failed to get messages: {e}")

@router.get("/chats/hash/{chat_hash}")
async def get_chat_by_hash(
    chat_hash: str,
    token: str = Depends(oauth2_scheme)
):
    """Get chat by hash"""
    prisma = None
    try:
        print(f"[DEBUG] Getting chat by hash: {chat_hash}")
        
        payload = decode_access_token(token)
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token.")
        
        prisma = Prisma()
        await prisma.connect()
        print(f"[DEBUG] Connected to database")
        
        # Get user
        user = await prisma.user.find_unique(where={"email": email})
        if not user:
            await prisma.disconnect()
            raise HTTPException(status_code=404, detail="User not found.")
        
        print(f"[DEBUG] Found user: {user.email}")
        
        # Find chat by hash
        chat = await prisma.chatsession.find_unique(
            where={"hash": chat_hash}
        )
        
        if not chat:
            await prisma.disconnect()
            raise HTTPException(status_code=404, detail="Chat not found.")
        
        if chat.userId != user.id:
            await prisma.disconnect()
            raise HTTPException(status_code=403, detail="Access denied.")
        
        print(f"[DEBUG] Found chat: {chat.id} ({chat.title})")
        
        await prisma.disconnect()
        print(f"[DEBUG] Disconnected from database")
        
        return ChatResponse(
            id=chat.id,
            title=chat.title or "New Chat",
            createdAt=chat.createdAt.isoformat(),
            updatedAt=chat.updatedAt.isoformat(),
            hash=chat.hash
        )
        
    except Exception as e:
        print(f"[ERROR] Failed to get chat by hash {chat_hash}: {e}")
        if prisma:
            try:
                await prisma.disconnect()
            except:
                pass
        raise HTTPException(status_code=500, detail=f"Failed to get chat: {e}")

@router.get("/chats/hash/{chat_hash}/messages")
async def get_chat_messages_by_hash(
    chat_hash: str,
    token: str = Depends(oauth2_scheme)
):
    """Get messages for a chat by hash"""
    prisma = None
    try:
        print(f"[DEBUG] Getting messages for chat hash: {chat_hash}")
        
        payload = decode_access_token(token)
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token.")
        
        prisma = Prisma()
        await prisma.connect()
        print(f"[DEBUG] Connected to database")
        
        # Get user
        user = await prisma.user.find_unique(where={"email": email})
        if not user:
            await prisma.disconnect()
            raise HTTPException(status_code=404, detail="User not found.")
        
        print(f"[DEBUG] Found user: {user.email}")
        
        # Find chat by hash and verify ownership
        chat = await prisma.chatsession.find_unique(
            where={"hash": chat_hash},
            include={"messages": True}
        )
        
        if not chat:
            await prisma.disconnect()
            raise HTTPException(status_code=404, detail="Chat not found.")
        
        if chat.userId != user.id:
            await prisma.disconnect()
            raise HTTPException(status_code=403, detail="Access denied.")
        
        print(f"[DEBUG] Found chat with {len(chat.messages)} messages")
        
        # Sort messages by createdAt in ascending order
        sorted_messages = sorted(chat.messages, key=lambda x: x.createdAt)
        
        await prisma.disconnect()
        print(f"[DEBUG] Disconnected from database")
        
        result = [
            MessageResponse(
                id=msg.id,
                content=msg.content,
                role=msg.role,
                createdAt=msg.createdAt.isoformat()
            )
            for msg in sorted_messages
        ]
        
        print(f"[DEBUG] Returning {len(result)} messages")
        return result
        
    except Exception as e:
        print(f"[ERROR] Failed to get messages for chat hash {chat_hash}: {e}")
        if prisma:
            try:
                await prisma.disconnect()
            except:
                pass
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
            
            # Parse config from JSON string to dictionary
            try:
                if isinstance(server.config, str):
                    config = json.loads(server.config)
                else:
                    config = server.config
                
                # Add server name to config for better error messages
                config['name'] = server.name
                
                print(f"[DEBUG] Connecting to MCP server: {server.name}")
                print(f"[DEBUG] Config: {json.dumps(config, indent=2)}")
                
                success = await mcp_service.connect_to_server(server_id, config)
                
                if success:
                    print(f"[DEBUG] Successfully connected to MCP server: {server.name}")
                else:
                    print(f"[DEBUG] Failed to connect to MCP server: {server.name}")
                    
            except json.JSONDecodeError as e:
                print(f"[ERROR] Failed to parse config for server {server.name}: {e}")
                print(f"[ERROR] Raw config: {server.config}")
            except Exception as e:
                print(f"[ERROR] Failed to connect to server {server.name}: {e}")
        
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
        
        # Prepare chat history
        history = []
        # Sort messages by createdAt in ascending order
        sorted_messages = sorted(chat.messages, key=lambda x: x.createdAt)
        for msg in sorted_messages:
            history.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # Start chat session with history
        if not deepseek_service.start_chat_session(history):
            await prisma.disconnect()
            raise HTTPException(status_code=500, detail="Failed to start chat session.")
        
        # Initialize MCP servers and get tools for DeepSeek
        print(f"[DEBUG] Initializing MCP servers for user {user.id}")
        await initialize_mcp_servers(user.id)
        
        # Get MCP tools in OpenAI format for DeepSeek
        mcp_tools = mcp_service.get_openai_tools()
        print(f"[DEBUG] Available MCP tools for DeepSeek: {len(mcp_tools)} tools")
        
        if mcp_tools:
            print(f"[DEBUG] Tool names: {[tool['function']['name'] for tool in mcp_tools]}")
        
        # Send message to DeepSeek with MCP tools
        response = await deepseek_service.send_message(request.content, tools=mcp_tools if mcp_tools else None)
        
        # Handle tool calls if DeepSeek wants to use tools
        if response.get("type") == "tool_calls":
            print(f"[DEBUG] DeepSeek requested tool calls: {response.get('tool_calls')}")
            
            tool_results = []
            for tool_call in response.get("tool_calls", []):
                try:
                    # Extract tool call information
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    tool_call_id = tool_call.id
                    
                    print(f"[DEBUG] Calling tool: {function_name} with args: {function_args}")
                    
                    # Use enhanced MCP service with health checks and fallbacks
                    tool_result = await mcp_service_deepseek.execute_tool_with_health_check(tool_call)
                    
                    # Check if tool call failed and generate user-friendly message
                    if not tool_result.get("success", False):
                        error_msg = tool_result.get("error", "Unknown error")
                        suggestion = tool_result.get("suggestion", "Please try again")
                        user_friendly_error = f"❌ {error_msg}\n\n💡 {suggestion}"
                        print(f"[DEBUG] Tool call failed: {user_friendly_error}")
                        tool_result["user_friendly_error"] = user_friendly_error
                    
                    tool_results.append({
                        "tool_call_id": tool_call_id,
                        "result": tool_result
                    })
                    
                    print(f"[DEBUG] Tool result: {tool_result}")
                    
                except Exception as e:
                    print(f"[ERROR] Failed to call tool {function_name}: {e}")
                    error_result = {"error": f"Tool call failed: {str(e)}"}
                    user_friendly_error = f"❌ Tool execution failed: {str(e)}\n\n💡 Please check your configuration and try again."
                    tool_results.append({
                        "tool_call_id": tool_call.id,
                        "result": {
                            "error": f"Tool call failed: {str(e)}",
                            "user_friendly_error": user_friendly_error
                        }
                    })
            
            # Send tool results back to DeepSeek
            if tool_results:
                print(f"[DEBUG] Sending tool results back to DeepSeek")
                response = await deepseek_service.send_tool_results(tool_results)
                assistant_content = response.get("content", "I'm sorry, I couldn't process the tool results.")
            else:
                assistant_content = "I'm sorry, I couldn't execute the requested tools."
        else:
            # Regular text response
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
            
            # Get DeepSeek API key and initialize
            deepseek_api_key = await get_user_deepseek_api_key(email)
            if not deepseek_api_key:
                yield f"data: {json.dumps({'error': 'No DeepSeek API key available. Please contact administrator or add your own API key in settings.'})}\n\n"
                return
            
            if not deepseek_service.initialize_with_api_key(deepseek_api_key):
                yield f"data: {json.dumps({'error': 'Failed to initialize DeepSeek'})}\n\n"
                return
            
            # Prepare history and start session
            history = [{"role": msg.role, "content": msg.content} for msg in chat.messages]
            
            if not deepseek_service.start_chat_session(history):
                yield f"data: {json.dumps({'error': 'Failed to start chat session'})}\n\n"
                return
            
            # Initialize MCP servers and get tools for DeepSeek
            print(f"[DEBUG] Initializing MCP servers for user {user.id}")
            await initialize_mcp_servers(user.id)
            
            # Get MCP tools in OpenAI format for DeepSeek
            mcp_tools = mcp_service.get_openai_tools()
            print(f"[DEBUG] Available MCP tools for DeepSeek streaming: {len(mcp_tools)} tools")
            
            if mcp_tools:
                print(f"[DEBUG] Tool names: {[tool['function']['name'] for tool in mcp_tools]}")
            
            # Stream response from DeepSeek with MCP tools
            full_response = ""
            async for chunk in deepseek_service.send_message_stream(request.content, tools=mcp_tools if mcp_tools else None):
                full_response += chunk
                yield f"data: {json.dumps({'type': 'text_chunk', 'content': chunk})}\n\n"
            
            # Store the complete assistant message
            assistant_message = await prisma.message.create(
                data={
                    "chatSessionId": chat_id,
                    "content": full_response,
                    "role": "assistant"
                }
            )
            yield f"data: {json.dumps({'type': 'complete', 'message_id': assistant_message.id})}\n\n"
            
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