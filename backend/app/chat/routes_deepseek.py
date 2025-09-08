from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from prisma import Prisma
from typing import List, Dict, Any, Optional
import json
import asyncio
import logging

from app.auth.jwt_handler import decode_access_token
from app.services.deepseek_r1_service import deepseek_r1_service, AIResponse, FunctionCall
from app.services.mcp_service_deepseek import mcp_service_deepseek

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
logger = logging.getLogger(__name__)

# Request/Response Models
class ChatRequest(BaseModel):
    message: str
    chat_id: Optional[int] = None

class ChatResponse(BaseModel):
    message: str
    reasoning: Optional[str] = None
    function_calls: List[Dict[str, Any]] = []
    execution_results: List[Dict[str, Any]] = []
    model_used: str = "deepseek-r1"
    error: Optional[str] = None

class ChatCreateRequest(BaseModel):
    title: Optional[str] = "New Chat"

class MessageSendRequest(BaseModel):
    content: str
    chatId: int

class ChatTitleUpdateRequest(BaseModel):
    title: str

class ChatResponseModel(BaseModel):
    id: int
    title: str
    createdAt: str
    updatedAt: str

class MessageResponse(BaseModel):
    id: int
    content: str
    role: str
    createdAt: str

# Utility Functions
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
            return os.getenv("DEEPSEEK_API_KEY")
        
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
            default_key = os.getenv("DEEPSEEK_API_KEY")
            logger.info(f"Using default DeepSeek API key for user: {email}")
            return default_key
        
    except Exception as e:
        logger.error(f"Failed to get DeepSeek API key: {e}")
        # Fallback to default key on error
        import os
        return os.getenv("DEEPSEEK_API_KEY")

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
                
                logger.info(f"Connecting to MCP server: {server.name}")
                logger.debug(f"Config: {json.dumps(config, indent=2)}")
                
                success = await mcp_service_deepseek.connect_to_server(server_id, config)
                
                if success:
                    logger.info(f"Successfully connected to MCP server: {server.name}")
                else:
                    logger.error(f"Failed to connect to MCP server: {server.name}")
                    
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse config for server {server.name}: {e}")
                logger.error(f"Raw config: {server.config}")
            except Exception as e:
                logger.error(f"Failed to connect to server {server.name}: {e}")
        
    except Exception as e:
        logger.error(f"Failed to initialize MCP servers: {e}")

async def generate_chat_title(first_message: str, deepseek_api_key: str) -> str:
    """Generate a title for the chat based on the first message"""
    try:
        # Initialize DeepSeek with the API key
        if not deepseek_r1_service.initialize_with_api_key(deepseek_api_key):
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
        response = await deepseek_r1_service.process_message(title_prompt)
        
        if response.message:
            title = response.message.strip()
            # Clean up the title - remove quotes, extra spaces, etc.
            title = title.replace('"', '').replace("'", "").strip()
            # Limit to 50 characters
            if len(title) > 50:
                title = title[:47] + "..."
            return title if title else "New Chat"
        else:
            return "New Chat"
            
    except Exception as e:
        logger.error(f"Failed to generate chat title: {e}")
        return "New Chat"

# Chat Management Endpoints
@router.post("/chats", response_model=ChatResponseModel)
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
        
        return ChatResponseModel(
            id=chat.id,
            title=chat.title or "New Chat",
            createdAt=chat.createdAt.isoformat(),
            updatedAt=chat.updatedAt.isoformat()
        )
        
    except Exception as e:
        logger.error(f"Failed to create chat: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create chat: {e}")

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
            ChatResponseModel(
                id=chat.id,
                title=chat.title or "New Chat",
                createdAt=chat.createdAt.isoformat(),
                updatedAt=chat.updatedAt.isoformat()
            )
            for chat in chats
        ]
        
    except Exception as e:
        logger.error(f"Failed to list chats: {e}")
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
        logger.error(f"Failed to get messages: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get messages: {e}")

# Main ChatConnect DeepSeek R1 Endpoint
@router.post("/message", response_model=ChatResponse)
async def send_message_deepseek(
    request: ChatRequest,
    token: str = Depends(oauth2_scheme)
):
    """Process chat message with DeepSeek R1 - Main ChatConnect endpoint"""
    
    try:
        # 1. Authenticate user
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
        
        # 2. Handle chat session
        chat_id = request.chat_id
        if not chat_id:
            # Create new chat if no chat_id provided
            chat = await prisma.chatsession.create(
                data={
                    "userId": user.id,
                    "title": "New Chat"
                }
            )
            chat_id = chat.id
        
        # Verify chat belongs to user
        chat = await prisma.chatsession.find_unique(
            where={"id": chat_id},
            include={"messages": True}
        )
        
        if not chat or chat.userId != user.id:
            await prisma.disconnect()
            raise HTTPException(status_code=404, detail="Chat not found.")
        
        # 3. Get DeepSeek API key
        deepseek_api_key = await get_user_deepseek_api_key(email)
        if not deepseek_api_key:
            await prisma.disconnect()
            raise HTTPException(status_code=400, detail="No DeepSeek API key available. Please contact administrator or add your own API key in settings.")
        
        # 4. Store user message
        user_message = await prisma.message.create(
            data={
                "chatSessionId": chat_id,
                "content": request.message,
                "role": "user"
            }
        )
        
        # 5. Generate title for new chats (if this is the first message)
        if len(chat.messages) == 0 and (chat.title == "New Chat" or not chat.title):
            generated_title = await generate_chat_title(request.message, deepseek_api_key)
            if generated_title and generated_title != "New Chat":
                await prisma.chatsession.update(
                    where={"id": chat_id},
                    data={"title": generated_title}
                )
        
        # 6. Initialize DeepSeek R1
        if not deepseek_r1_service.initialize_with_api_key(deepseek_api_key):
            await prisma.disconnect()
            raise HTTPException(status_code=400, detail="Failed to initialize DeepSeek R1 API.")
        
        # 7. Prepare chat history
        history = []
        sorted_messages = sorted(chat.messages, key=lambda x: x.createdAt)
        for msg in sorted_messages:
            history.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # 8. Start chat session with history
        if not deepseek_r1_service.start_chat_session(history):
            await prisma.disconnect()
            raise HTTPException(status_code=500, detail="Failed to start chat session.")
        
        # 9. Initialize MCP servers and discover tools
        logger.info(f"Initializing MCP servers for user {user.id}")
        await initialize_mcp_servers(user.id)
        
        # Get MCP tools for DeepSeek R1
        available_tools = await mcp_service_deepseek.discover_tools(request.message)
        logger.info(f"Available MCP tools for DeepSeek R1: {len(available_tools)} tools")
        
        if available_tools:
            logger.info(f"Tool names: {[tool.get('name', 'unknown') for tool in available_tools]}")
        
        # 10. Process message with DeepSeek R1
        ai_response = await deepseek_r1_service.process_message(request.message, available_tools)
        
        # 11. Execute function calls with confirmation
        execution_results = []
        for function_call in ai_response.function_calls:
            try:
                logger.info(f"Executing function call: {function_call.name}")
                result = await mcp_service_deepseek.execute_tool_with_confirmation(function_call)
                execution_results.append(result)
                logger.info(f"Function execution result: {result}")
            except Exception as e:
                logger.error(f"Failed to execute function call {function_call.name}: {e}")
                execution_results.append({
                    "success": False,
                    "error": f"Function execution failed: {str(e)}"
                })
        
        # 12. Generate final response with DeepSeek R1
        final_response = await deepseek_r1_service.generate_final_response(
            ai_response.message,
            ai_response.reasoning or "",
            execution_results
        )
        
        # 13. Store assistant message
        assistant_message = await prisma.message.create(
            data={
                "chatSessionId": chat_id,
                "content": final_response,
                "role": "assistant"
            }
        )
        
        await prisma.disconnect()
        
        # 14. Return response
        return ChatResponse(
            message=final_response,
            reasoning=ai_response.reasoning,
            function_calls=[{
                "name": fc.name,
                "parameters": fc.parameters,
                "call_id": fc.call_id
            } for fc in ai_response.function_calls],
            execution_results=execution_results,
            model_used="deepseek-r1"
        )
        
    except Exception as e:
        logger.error(f"DeepSeek R1 processing error: {str(e)}")
        return ChatResponse(
            message="I encountered an error processing your request. Please try again.",
            error=str(e)
        )

# Streaming endpoint for real-time responses
@router.post("/message/stream")
async def send_message_stream_deepseek(
    request: ChatRequest,
    token: str = Depends(oauth2_scheme)
):
    """Stream chat message with DeepSeek R1"""
    
    async def generate_response():
        try:
            # Similar setup as send_message_deepseek but with streaming
            payload = decode_access_token(token)
            email = payload.get("sub")
            if not email:
                yield f"data: {json.dumps({'error': 'Invalid token'})}\n\n"
                return
            
            prisma = Prisma()
            await prisma.connect()
            
            user = await prisma.user.find_unique(where={"email": email})
            if not user:
                yield f"data: {json.dumps({'error': 'User not found'})}\n\n"
                return
            
            # Handle chat session
            chat_id = request.chat_id
            if not chat_id:
                chat = await prisma.chatsession.create(
                    data={
                        "userId": user.id,
                        "title": "New Chat"
                    }
                )
                chat_id = chat.id
            
            chat = await prisma.chatsession.find_unique(
                where={"id": chat_id},
                include={"messages": True}
            )
            
            if not chat or chat.userId != user.id:
                yield f"data: {json.dumps({'error': 'Chat not found'})}\n\n"
                return
            
            # Store user message
            user_message = await prisma.message.create(
                data={
                    "chatSessionId": chat_id,
                    "content": request.message,
                    "role": "user"
                }
            )
            
            yield f"data: {json.dumps({'type': 'user_message', 'message': {'id': user_message.id, 'content': user_message.content, 'role': 'user'}})}\n\n"
            
            # Get DeepSeek API key and initialize
            deepseek_api_key = await get_user_deepseek_api_key(email)
            if not deepseek_api_key:
                yield f"data: {json.dumps({'error': 'No DeepSeek API key available'})}\n\n"
                return
            
            if not deepseek_r1_service.initialize_with_api_key(deepseek_api_key):
                yield f"data: {json.dumps({'error': 'Failed to initialize DeepSeek R1'})}\n\n"
                return
            
            # Prepare history and start session
            history = [{"role": msg.role, "content": msg.content} for msg in chat.messages]
            
            if not deepseek_r1_service.start_chat_session(history):
                yield f"data: {json.dumps({'error': 'Failed to start chat session'})}\n\n"
                return
            
            # Initialize MCP servers and get tools
            await initialize_mcp_servers(user.id)
            available_tools = await mcp_service_deepseek.discover_tools(request.message)
            
            # Stream response from DeepSeek R1
            full_response = ""
            async for chunk in deepseek_r1_service.send_message_stream(request.message, available_tools):
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

# MCP Tools Endpoints
@router.get("/mcp/tools")
async def get_available_tools(token: str = Depends(oauth2_scheme)):
    """Get all available MCP tools for the user"""
    try:
        payload = decode_access_token(token)
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token.")
        
        # Get all available tools from connected MCP servers
        tools = mcp_service_deepseek.get_all_tools()
        connected_servers = mcp_service_deepseek.get_connected_servers()
        
        return {
            "tools": tools,
            "connected_servers": connected_servers
        }
        
    except Exception as e:
        logger.error(f"Failed to get tools: {e}")
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
        success = await mcp_service_deepseek.connect_to_server(connection_id, server.config)
        
        if success:
            return {"status": "connected", "server_id": connection_id}
        else:
            raise HTTPException(status_code=500, detail="Failed to connect to MCP server")
        
    except Exception as e:
        logger.error(f"Failed to connect MCP server: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to connect: {e}")

# Chat Management Endpoints (continued)
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
        logger.error(f"Failed to update chat title: {e}")
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
        logger.error(f"Failed to delete chat: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete chat: {e}") 