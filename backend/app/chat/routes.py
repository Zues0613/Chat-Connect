from fastapi import APIRouter, HTTPException, Depends, status, Request, Response
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import StreamingResponse
from email.utils import parsedate_to_datetime
from wsgiref.handlers import format_date_time
from pydantic import BaseModel
from prisma import Prisma
from typing import List, Dict, Any, Optional
import json
import asyncio
import re

from app.auth.jwt_handler import decode_access_token
import os
from app.services.deepseek_service import deepseek_service, InsufficientCreditsError, APITimeoutError
from app.services.mcp_service import mcp_service
from app.services.mcp_service_deepseek import mcp_service_deepseek
from app.services.intent_detector import intent_detector
from app.services.confirmation_handler import confirmation_handler

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

def _parse_tool_calls_from_text(text: str) -> List[Dict[str, Any]]:
    """Best-effort parse of tool call JSON from assistant text.

    Supports formats:
    - Code block JSON array: [{"name": "tool", "arguments": {...}}, ...]
    - Code block JSON object: {"action": "tool", "parameters": {...}}
    - Inline JSON (same as above)
    Returns a list of {name: str, arguments: dict}
    """
    if not text:
        return []
    candidates: List[str] = []
    # 1) Extract fenced ```json blocks
    for m in re.finditer(r"```json\s*([\s\S]*?)\s*```", text, re.IGNORECASE):
        candidates.append(m.group(1))
    # 2) Fallback: any {...} JSON-looking block
    if not candidates:
        for m in re.finditer(r"\{[\s\S]*\}", text):
            candidates.append(m.group(0))
    parsed_calls: List[Dict[str, Any]] = []
    for raw in candidates:
        try:
            data = json.loads(raw)
        except Exception:
            continue
        try:
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and item.get("name"):
                        args = item.get("arguments") or item.get("params") or {}
                        if isinstance(args, dict):
                            parsed_calls.append({"name": item["name"], "arguments": args})
            elif isinstance(data, dict):
                # { action/name, parameters/arguments }
                tool_name = data.get("name") or data.get("action")
                args = data.get("arguments") or data.get("parameters") or {}
                if tool_name and isinstance(args, dict):
                    parsed_calls.append({"name": tool_name, "arguments": args})
        except Exception:
            continue
    return parsed_calls

def _is_mcp_setup_query(text: str) -> bool:
    t = (text or "").lower()
    keywords = [
        "set up mcp", "setup mcp", "configure mcp", "add mcp", "mcp servers", "pipedream mcp",
        "how do i set up mcp", "how to set up mcp", "connect mcp", "mcp guide"
    ]
    return any(k in t for k in keywords)

def _generate_mcp_setup_help() -> str:
    return (
        "🔌 MCP Setup Guide (Pipedream)\n\n"
        "1. Open Settings → MCP Servers\n"
        "2. Click ‘Quick Add MCP’\n"
        "3. Paste your Pipedream MCP URL (format: https://mcp.pipedream.net/[workflow-id]/[endpoint])\n"
        "4. Save, then refresh servers and tools\n"
        "5. If OAuth is required, complete it via Settings when prompted\n\n"
        "Tips:\n"
        "- Ensure MCP Server is enabled in your Pipedream workflow settings\n"
        "- Use ‘tools/list’ to verify tools are exposed\n"
        "- See documentation: docs/integrations/pipedream.md"
    )

def _extract_text_from_tool_results(tool_results: List[Dict[str, Any]]) -> str:
    """Extract a user-friendly text from MCP tool_results structure."""
    texts: List[str] = []
    for tr in tool_results:
        res = tr.get("result", {}) or {}
        # Common Pipedream result shape: { "result": { "content": [ {"type": "text", "text": "..."}, ... ] } }
        if isinstance(res, dict):
            inner = res.get("result") if isinstance(res.get("result"), dict) else res
            if isinstance(inner, dict):
                content = inner.get("content")
                if isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and item.get("type") == "text" and isinstance(item.get("text"), str):
                            texts.append(item["text"])
                elif isinstance(content, str):
                    texts.append(content)
            # Direct text fallback
            if not texts and isinstance(res.get("text"), str):
                texts.append(res["text"])
            # Error fallback
            if not texts and isinstance(res.get("error"), str):
                texts.append(f"Error: {res['error']}")
    return "\n\n".join(texts).strip()

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
async def list_chats(request: Request, response: Response, token: str = Depends(oauth2_scheme)):
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
        
        # Build a stable ETag based on user + count + most recent updatedAt
        try:
            latest_updated = int(chats[0].updatedAt.timestamp()) if chats else 0
        except Exception:
            latest_updated = 0
        etag_value = f'W/"chats:{user.id}:{len(chats)}:{latest_updated}"'
        if_none_match = request.headers.get("if-none-match")
        if if_none_match == etag_value:
            return Response(status_code=304)

        # Last-Modified handling
        if_modified_since = request.headers.get("if-modified-since")
        if latest_updated and if_modified_since:
            try:
                ims_dt = parsedate_to_datetime(if_modified_since)
                if int(ims_dt.timestamp()) >= latest_updated:
                    return Response(status_code=304)
            except Exception:
                pass

        response.headers["ETag"] = etag_value
        response.headers["Cache-Control"] = "private, max-age=60, must-revalidate"
        response.headers["Vary"] = "Authorization"
        if latest_updated:
            response.headers["Last-Modified"] = format_date_time(latest_updated)

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
    request: Request,
    response: Response,
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
        
        # Compute ETag for this chat's messages (count + last createdAt)
        try:
            last_ts = int(sorted_messages[-1].createdAt.timestamp()) if sorted_messages else 0
        except Exception:
            last_ts = 0
        etag_value = f'W/"msgs:{chat_id}:{len(sorted_messages)}:{last_ts}"'
        if_none_match = request.headers.get("if-none-match")
        if if_none_match == etag_value:
            return Response(status_code=304)

        # Last-Modified handling
        if_modified_since = request.headers.get("if-modified-since")
        if last_ts and if_modified_since:
            try:
                ims_dt = parsedate_to_datetime(if_modified_since)
                if int(ims_dt.timestamp()) >= last_ts:
                    return Response(status_code=304)
            except Exception:
                pass

        response.headers["ETag"] = etag_value
        response.headers["Cache-Control"] = "private, max-age=60, must-revalidate"
        response.headers["Vary"] = "Authorization"
        if last_ts:
            response.headers["Last-Modified"] = format_date_time(last_ts)

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
    request: Request,
    response: Response,
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
        
        # Compute ETag for this chat hash messages
        try:
            last_ts = int(sorted_messages[-1].createdAt.timestamp()) if sorted_messages else 0
        except Exception:
            last_ts = 0
        etag_value = f'W/"msgs_hash:{chat_hash}:{len(sorted_messages)}:{last_ts}"'
        if_none_match = request.headers.get("if-none-match")
        if if_none_match == etag_value:
            return Response(status_code=304)

        # Last-Modified handling
        if_modified_since = request.headers.get("if-modified-since")
        if last_ts and if_modified_since:
            try:
                ims_dt = parsedate_to_datetime(if_modified_since)
                if int(ims_dt.timestamp()) >= last_ts:
                    return Response(status_code=304)
            except Exception:
                pass

        response.headers["ETag"] = etag_value
        response.headers["Cache-Control"] = "private, max-age=60, must-revalidate"
        response.headers["Vary"] = "Authorization"
        if last_ts:
            response.headers["Last-Modified"] = format_date_time(last_ts)

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

async def get_available_mcp_server_names(user_id: int) -> List[str]:
    """Get list of available MCP server names for a user"""
    try:
        prisma = Prisma()
        await prisma.connect()
        
        # Get all MCP servers for user
        servers = await prisma.mcpserver.find_many(where={"userId": user_id})
        
        await prisma.disconnect()
        
        # Extract server names (assuming they're stored in a name field)
        server_names = []
        for server in servers:
            # Try to get server name from config or name field
            if hasattr(server, 'name') and server.name:
                server_names.append(server.name.lower().replace(" ", "_"))
            elif hasattr(server, 'config') and server.config:
                # Try to extract name from config
                try:
                    if isinstance(server.config, str):
                        config = json.loads(server.config)
                    else:
                        config = server.config
                    
                    if 'name' in config:
                        server_names.append(str(config['name']).lower().replace(" ", "_"))
                    elif 'type' in config:
                        server_names.append(str(config['type']).lower().replace(" ", "_"))
                except:
                    pass
        
        return server_names
        
    except Exception as e:
        print(f"[ERROR] Failed to get MCP server names: {e}")
        return []

async def initialize_mcp_servers(user_id: int) -> None:
    """Initialize all MCP servers for the user (non-blocking)"""
    try:
        prisma = Prisma()
        await prisma.connect()
        
        # Get all MCP servers for user
        servers = await prisma.mcpserver.find_many(where={"userId": user_id})
        
        await prisma.disconnect()
        
        if not servers:
            print(f"[INFO] No MCP servers configured for user {user_id}")
            return
        
        print(f"[DEBUG] Found {len(servers)} MCP servers for user {user_id}")
        
        # Connect to each server with timeout
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
                
                # Connect using DeepSeek MCP service for consistency with execution
                try:
                    # Longer timeout for Pipedream endpoints to establish session
                    uri = str(config.get("uri", ""))
                    timeout_seconds = 20.0 if ("pipedream.net" in uri or "mcp.pipedream.net" in uri) else 8.0
                    success = await asyncio.wait_for(
                        mcp_service_deepseek.connect_to_server(server_id, config),
                        timeout=timeout_seconds
                    )
                    
                    if success:
                        print(f"[DEBUG] Successfully connected to MCP server: {server.name}")
                    else:
                        print(f"[DEBUG] Failed to connect to MCP server: {server.name}")
                        
                except asyncio.TimeoutError:
                    print(f"[WARNING] Timeout connecting to MCP server: {server.name}")
                except Exception as e:
                    print(f"[ERROR] Failed to connect to server {server.name}: {e}")
                    
            except json.JSONDecodeError as e:
                print(f"[ERROR] Failed to parse config for server {server.name}: {e}")
            except Exception as e:
                print(f"[ERROR] Failed to connect to server {server.name}: {e}")
        
    except Exception as e:
        print(f"[ERROR] Failed to initialize MCP servers: {e}")
        # Don't raise the exception - MCP servers are optional

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
        
        # Check for confirmation commands first
        if request.content.lower().startswith(('confirm ', 'cancel ')):
            # Handle confirmation commands
            parts = request.content.split(' ', 1)
            if len(parts) == 2:
                command, confirmation_id = parts
                
                if command.lower() == 'confirm':
                    confirmation = confirmation_handler.confirm_action(confirmation_id)
                    if confirmation and confirmation.user_id == user.id:
                        # Mark as executed and proceed with MCP action
                        confirmation_handler.execute_confirmed_action(confirmation_id)
                        
                        # Store user confirmation message
                        user_message = await prisma.message.create(
                            data={
                                "chatSessionId": chat_id,
                                "content": request.content,
                                "role": "user"
                            }
                        )
                        
                        # Proceed with MCP action execution
                        return await _execute_mcp_action(chat_id, user.id, confirmation, prisma, user_message)
                    else:
                        # Invalid or expired confirmation
                        user_message = await prisma.message.create(
                            data={
                                "chatSessionId": chat_id,
                                "content": request.content,
                                "role": "user"
                            }
                        )
                        
                        assistant_message = await prisma.message.create(
                            data={
                                "chatSessionId": chat_id,
                                "content": "❌ Invalid or expired confirmation. Please make your request again.",
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
                
                elif command.lower() == 'cancel':
                    confirmation = confirmation_handler.get_confirmation(confirmation_id)
                    if confirmation and confirmation.user_id == user.id:
                        confirmation_handler.cancel_confirmation(confirmation_id)
                        
                        # Store user cancellation message
                        user_message = await prisma.message.create(
                            data={
                                "chatSessionId": chat_id,
                                "content": request.content,
                                "role": "user"
                            }
                        )
                        
                        assistant_message = await prisma.message.create(
                            data={
                                "chatSessionId": chat_id,
                                "content": confirmation_handler.generate_cancellation_message(confirmation),
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
        
        # Check for intent detection
        available_mcp_servers = await get_available_mcp_server_names(user.id)
        intent_match = intent_detector.detect_intent(request.content, available_mcp_servers)
        
        if intent_match:
            # Intent detected - handle based on MCP server availability
            if not intent_match.available_mcp_servers:
                # No MCP servers available - provide setup guide
                user_message = await prisma.message.create(
                    data={
                        "chatSessionId": chat_id,
                        "content": request.content,
                        "role": "user"
                    }
                )
                
                assistant_message = await prisma.message.create(
                    data={
                        "chatSessionId": chat_id,
                        "content": intent_detector.generate_response(intent_match),
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
            else:
                # MCP servers available - create confirmation
                confirmation_id = confirmation_handler.create_confirmation(
                    user_id=user.id,
                    chat_id=chat_id,
                    intent_type=intent_match.intent_type,
                    original_message=request.content,
                    mcp_servers=intent_match.available_mcp_servers
                )
                
                confirmation = confirmation_handler.get_confirmation(confirmation_id)
                
                # Store user message
                user_message = await prisma.message.create(
                    data={
                        "chatSessionId": chat_id,
                        "content": request.content,
                        "role": "user"
                    }
                )
                
                assistant_message = await prisma.message.create(
                    data={
                        "chatSessionId": chat_id,
                        "content": confirmation_handler.generate_confirmation_message(confirmation),
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
        
        # No intent detected or no MCP servers - proceed with regular chat
        # Quick guard: Provide built-in MCP setup help for generic setup questions
        if _is_mcp_setup_query(request.content):
            # Store the user's setup question first
            user_message = await prisma.message.create(
                data={
                    "chatSessionId": chat_id,
                    "content": request.content,
                    "role": "user"
                }
            )
            # Then store the assistant's setup guidance
            setup_msg = await prisma.message.create(
                data={
                    "chatSessionId": chat_id,
                    "content": _generate_mcp_setup_help(),
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
                    id=setup_msg.id,
                    content=setup_msg.content,
                    role=setup_msg.role,
                    createdAt=setup_msg.createdAt.isoformat()
                )
            }
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
        
        # Prepare chat history (cap to last N to reduce latency)
        history = []
        sorted_messages = sorted(chat.messages, key=lambda x: x.createdAt)
        cap = int(os.getenv("CHAT_HISTORY_CAP", "12"))
        recent_messages = sorted_messages[-cap:] if cap > 0 else sorted_messages
        for msg in recent_messages:
            history.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # Start chat session with history
        if not deepseek_service.start_chat_session(history):
            await prisma.disconnect()
            raise HTTPException(status_code=500, detail="Failed to start chat session.")
        
        # Initialize MCP servers and get tools for DeepSeek (OPTIONAL - non-blocking)
        mcp_tools = []
        
        # Check if MCP servers are enabled
        import os
        mcp_enabled = os.getenv("ENABLE_MCP_SERVERS", "true").lower() == "true"
        
        if mcp_enabled:
            try:
                print(f"[DEBUG] Initializing MCP servers for user {user.id}")
                await initialize_mcp_servers(user.id)
                # Get MCP tools in OpenAI format for DeepSeek
                mcp_tools = mcp_service_deepseek.get_openai_tools()
                print(f"[DEBUG] Available MCP tools for DeepSeek: {len(mcp_tools)} tools")
                if mcp_tools:
                    print(f"[DEBUG] Tool names: {[tool['function']['name'] for tool in mcp_tools]}")
                    # Debug the first tool schema
                    if mcp_tools:
                        first_tool = mcp_tools[0]
                        print(f"[DEBUG] First tool schema: {json.dumps(first_tool, indent=2)}")
                        
                        # Check if google_drive-list-files exists and show its schema
                        drive_tool = next((t for t in mcp_tools if t['function']['name'] == 'google_drive-list-files'), None)
                        if drive_tool:
                            print(f"[DEBUG] google_drive-list-files schema: {json.dumps(drive_tool, indent=2)}")
                        else:
                            print(f"[DEBUG] google_drive-list-files NOT FOUND in tools")
            except Exception as e:
                print(f"[INFO] MCP servers not available - continuing with regular chat: {e}")
                # Continue without MCP tools - this is normal for general chat usage
                mcp_tools = None
        else:
            print(f"[INFO] MCP servers disabled - using regular chat mode")
            mcp_tools = None
        
        # Send message to DeepSeek (with or without MCP tools)
        print(f"[DEBUG] Sending message to DeepSeek...")
        print(f"[DEBUG] User message: {request.content}")
        print(f"[DEBUG] MCP tools available: {len(mcp_tools) if mcp_tools else 0}")
        
        # Allow longer LLM timeout when tools may be invoked
        try:
            response = await deepseek_service.send_message(
                request.content,
                tools=mcp_tools if mcp_tools else None,
                timeout_seconds=float(os.getenv("OPENROUTER_TIMEOUT", "60"))
            )
        except InsufficientCreditsError as ice:
            await prisma.disconnect()
            raise HTTPException(
                status_code=402,
                detail=str(ice)
            )
        except APITimeoutError as te:
            await prisma.disconnect()
            raise HTTPException(
                status_code=504,
                detail=str(te)
            )
        
        print(f"[DEBUG] DeepSeek response type: {response.get('type')}")
        print(f"[DEBUG] DeepSeek response content: {response.get('content')}")
        print(f"[DEBUG] DeepSeek tool calls: {response.get('tool_calls')}")
        
        # Handle tool calls if DeepSeek wants to use tools
        tool_results = []  # Initialize here
        if response.get("type") == "tool_calls":
            print(f"[DEBUG] DeepSeek requested tool calls: {response.get('tool_calls')}")
            
            for tool_call in response.get("tool_calls", []):
                try:
                    # Extract tool call information
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    tool_call_id = tool_call.id
                    
                    print(f"[DEBUG] Calling tool: {function_name} with args: {function_args}")
                    
                    # Use enhanced MCP service with health checks and fallbacks
                    # Wrap OpenAI tool call into a simple object with expected attributes
                    from types import SimpleNamespace
                    function_call = SimpleNamespace(name=function_name, parameters=function_args)
                    tool_result = await mcp_service_deepseek.execute_tool_with_health_check(function_call)
                    
                    print(f"[DEBUG] Tool execution result: {tool_result}")
                    
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
        else:
            print(f"[DEBUG] No tool calls in response - this might be the issue!")
            print(f"[DEBUG] Response was: {response}")
            # Fallback: parse JSON tool instructions from assistant text and execute
            parsed = _parse_tool_calls_from_text(response.get("content", "")) if response.get("content") else []
            if parsed:
                print(f"[DEBUG] Parsed {len(parsed)} tool instructions from assistant text: {parsed}")
                for idx, item in enumerate(parsed):
                    try:
                        name = item.get("name")
                        args = item.get("arguments", {})
                        print(f"[DEBUG] Fallback executing tool {name} with args {args}")
                        from types import SimpleNamespace
                        function_call = SimpleNamespace(name=name, parameters=args)
                        result = await mcp_service_deepseek.execute_tool_with_health_check(function_call)
                        tool_results.append({
                            "tool_call_id": f"fallback_{idx}",
                            "result": result
                        })
                    except Exception as e:
                        print(f"[ERROR] Fallback tool exec failed for {item}: {e}")
                        tool_results.append({
                            "tool_call_id": f"fallback_{idx}",
                            "result": {
                                "error": f"Fallback tool exec failed: {str(e)}",
                                "user_friendly_error": f"❌ Tool execution failed: {str(e)}\n\n💡 Please verify your MCP server and parameters."
                            }
                        })
            else:
                print(f"[DEBUG] No parsable tool instructions found in assistant text.")
        
        # Send tool results back to DeepSeek
        if tool_results:
            print(f"[DEBUG] Sending tool results back to DeepSeek")
            response = await deepseek_service.send_tool_results(tool_results)
            assistant_content = response.get("content") or ""
            
            if not assistant_content:
                # Fallback to raw tool text when model follow-up fails (e.g., 402) or returns empty
                extracted = _extract_text_from_tool_results(tool_results)
                if extracted:
                    assistant_content = extracted
                else:
                    assistant_content = "I'm sorry, I couldn't process the tool results."

            # Append clear tool feedback if any tool failed
            error_messages = []
            for tr in tool_results:
                res = tr.get("result", {}) or {}
                if isinstance(res, dict):
                    if res.get("user_friendly_error"):
                        error_messages.append(res["user_friendly_error"])
                    elif res.get("error_type") == "parameter_validation":
                        # Handle parameter validation errors with enhanced suggestions
                        error_msg = res.get("error", "Parameter validation failed")
                        suggestion = res.get("suggestion", "Please try again with more specific details")
                        enhanced_args = res.get("enhanced_arguments", {})
                        
                        error_message = f"❌ {error_msg}\n\n💡 {suggestion}"
                        if enhanced_args:
                            error_message += f"\n\n🔧 I tried to enhance your request with: {json.dumps(enhanced_args, indent=2)}"
                        
                        error_messages.append(error_message)
                    elif res.get("error"):
                        error_msg = res.get("error", "Unknown error")
                        suggestion = res.get("suggestion", "Please try again")
                        error_message = f"❌ {error_msg}"
                        if suggestion:
                            error_message += f"\n\n💡 {suggestion}"
                        error_messages.append(error_message)
            
            if error_messages:
                assistant_content = assistant_content + "\n\n" + "\n\n".join(error_messages)
            # Progress footer
            assistant_content += "\n\n✅ Action processed. If you don't see results, please refresh tools and try again."
        else:
            # No tool calls or no results
            if response.get("type") == "tool_calls":
                assistant_content = "I'm sorry, I couldn't execute the requested tools."
            else:
                # Regular text response
                assistant_content = response.get("content", "I'm sorry, I couldn't generate a response.")
                assistant_content += "\n\nℹ️ No actionable tool calls were executed."
        
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
        
    except HTTPException as http_exc:
        # Preserve intended HTTP status codes like 402 from upstream
        raise http_exc
    except Exception as e:
        print(f"[ERROR] Failed to send message: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send message: {e}")

async def _execute_mcp_action(chat_id: int, user_id: int, confirmation, prisma, user_message=None) -> Dict:
    """Execute a confirmed MCP action"""
    try:
        # Get user's DeepSeek API key
        user = await prisma.user.find_unique(where={"id": user_id})
        deepseek_api_key = await get_user_deepseek_api_key(user.email)
        
        if not deepseek_api_key:
            raise HTTPException(status_code=400, detail="No DeepSeek API key available.")
        
        # Initialize DeepSeek
        if not deepseek_service.initialize_with_api_key(deepseek_api_key):
            raise HTTPException(status_code=400, detail="Failed to initialize DeepSeek API.")
        
        # Initialize MCP servers
        await initialize_mcp_servers(user_id)
        
        # Get MCP tools (DeepSeek-compatible)
        mcp_tools = mcp_service_deepseek.get_openai_tools()
        
        # Send the original message to DeepSeek with MCP tools
        response = await deepseek_service.send_message(
            confirmation.original_message,
            tools=mcp_tools if mcp_tools else None,
            timeout_seconds=float(os.getenv("OPENROUTER_TIMEOUT", "60"))
        )
        
        # Handle tool calls if any
        if response.get("type") == "tool_calls":
            tool_results = []
            for tool_call in response.get("tool_calls", []):
                try:
                    # Wrap OpenAI tool call to expected structure
                    from types import SimpleNamespace
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    function_call = SimpleNamespace(name=function_name, parameters=function_args)
                    tool_result = await mcp_service_deepseek.execute_tool_with_health_check(function_call)
                    tool_results.append({
                        "tool_call_id": tool_call.id,
                        "result": tool_result
                    })
                except Exception as e:
                    print(f"[ERROR] Failed to call tool: {e}")
                    tool_results.append({
                        "tool_call_id": tool_call.id,
                        "result": {"error": f"Tool call failed: {str(e)}"}
                    })
            
            # Send tool results back to DeepSeek
            if tool_results:
                response = await deepseek_service.send_tool_results(tool_results)
                assistant_content = response.get("content", "I'm sorry, I couldn't process the tool results.")
                
                # Append clear tool feedback if any tool failed
                error_messages = []
                for tr in tool_results:
                    res = tr.get("result", {}) or {}
                    if isinstance(res, dict):
                        if res.get("user_friendly_error"):
                            error_messages.append(res["user_friendly_error"])
                        elif res.get("error_type") == "parameter_validation":
                            # Handle parameter validation errors with enhanced suggestions
                            error_msg = res.get("error", "Parameter validation failed")
                            suggestion = res.get("suggestion", "Please try again with more specific details")
                            enhanced_args = res.get("enhanced_arguments", {})
                            
                            error_message = f"❌ {error_msg}\n\n💡 {suggestion}"
                            if enhanced_args:
                                error_message += f"\n\n🔧 I tried to enhance your request with: {json.dumps(enhanced_args, indent=2)}"
                            
                            error_messages.append(error_message)
                        elif res.get("error"):
                            error_msg = res.get("error", "Unknown error")
                            suggestion = res.get("suggestion", "Please try again")
                            error_message = f"❌ {error_msg}"
                            if suggestion:
                                error_message += f"\n\n💡 {suggestion}"
                            error_messages.append(error_message)
                
                if error_messages:
                    assistant_content = assistant_content + "\n\n" + "\n\n".join(error_messages)
            else:
                assistant_content = "I'm sorry, I couldn't execute the requested tools."
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
                id=(user_message.id if user_message else 0),
                content=(user_message.content if user_message else confirmation.original_message),
                role=(user_message.role if user_message else "user"),
                createdAt=(user_message.createdAt.isoformat() if user_message else confirmation.created_at.isoformat())
            ),
            "assistant_message": MessageResponse(
                id=assistant_message.id,
                content=assistant_message.content,
                role=assistant_message.role,
                createdAt=assistant_message.createdAt.isoformat()
            )
        }
        
    except Exception as e:
        print(f"[ERROR] Failed to execute MCP action: {e}")
        await prisma.disconnect()
        raise HTTPException(status_code=500, detail=f"Failed to execute MCP action: {str(e)}")

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
            
            # Initialize MCP servers and get tools for DeepSeek (OPTIONAL - non-blocking)
            mcp_tools = []
            
            # Check if MCP servers are enabled
            import os
            mcp_enabled = os.getenv("ENABLE_MCP_SERVERS", "true").lower() == "true"
            
            if mcp_enabled:
                try:
                    print(f"[DEBUG] Initializing MCP servers for user {user.id}")
                    await initialize_mcp_servers(user.id)
                    
                    # Get MCP tools in OpenAI format for DeepSeek
                    mcp_tools = mcp_service_deepseek.get_openai_tools()
                    print(f"[DEBUG] Available MCP tools for DeepSeek streaming: {len(mcp_tools)} tools")
                    
                    if mcp_tools:
                        print(f"[DEBUG] Tool names: {[tool['function']['name'] for tool in mcp_tools]}")
                except Exception as e:
                    print(f"[INFO] MCP servers not available for streaming - continuing with regular chat: {e}")
                    # Continue without MCP tools - this is normal for general chat usage
                    mcp_tools = None
            else:
                print(f"[INFO] MCP servers disabled for streaming - using regular chat mode")
                mcp_tools = None
            
            # Stream response from DeepSeek (with or without MCP tools)
            full_response = ""
            try:
                async for chunk in deepseek_service.send_message_stream(request.content, tools=mcp_tools if mcp_tools else None):
                    full_response += chunk
                    yield f"data: {json.dumps({'type': 'text_chunk', 'content': chunk})}\n\n"
            except InsufficientCreditsError as ice:
                yield f"data: {json.dumps({'error': str(ice), 'code': 402})}\n\n"
                return
            
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
        
        prisma = Prisma()
        await prisma.connect()
        
        # Get user
        user = await prisma.user.find_unique(where={"email": email})
        if not user:
            await prisma.disconnect()
            raise HTTPException(status_code=404, detail="User not found.")
        
        await prisma.disconnect()
        
        # Initialize MCP servers for this user
        print(f"[DEBUG] Initializing MCP servers for user {user.id}")
        await initialize_mcp_servers(user.id)
        
        # Get all available tools from connected MCP servers (DeepSeek MCP service)
        tools = mcp_service_deepseek.get_all_tools()
        connected_servers = mcp_service_deepseek.get_connected_servers()
        
        print(f"[DEBUG] Found {len(tools)} tools and {len(connected_servers)} connected servers")
        
        return {
            "tools": tools,
            "connected_servers": connected_servers,
            "total_tools": len(tools),
            "total_servers": len(connected_servers)
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
        
        # Connect to the server using DeepSeek MCP service for consistency
        connection_id = f"user_{user.id}_server_{server.id}"
        success = await mcp_service_deepseek.connect_to_server(connection_id, server.config)
        
        if success:
            return {"status": "connected", "server_id": connection_id}
        else:
            raise HTTPException(status_code=500, detail="Failed to connect to MCP server")
        
    except Exception as e:
        print(f"[ERROR] Failed to connect MCP server: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to connect: {e}") 

@router.get("/test-tools")
async def test_tools():
    """Test endpoint to verify MCP tools are working"""
    try:
        # Initialize MCP servers
        await initialize_mcp_servers(1)  # Use user ID 1 for testing
        
        # Get tools
        tools = mcp_service_deepseek.get_openai_tools()
        
        # Test a simple tool call
        test_result = None
        if tools:
            # Find google_drive-list-files tool
            drive_tool = next((t for t in tools if t['function']['name'] == 'google_drive-list-files'), None)
            if drive_tool:
                print(f"[DEBUG] Testing tool call to google_drive-list-files")
                from types import SimpleNamespace
                test_call = SimpleNamespace(
                    name='google_drive-list-files',
                    parameters={'instruction': 'List all files in root directory'}
                )
                test_result = await mcp_service_deepseek.execute_tool_with_health_check(test_call)
                print(f"[DEBUG] Test result: {test_result}")
        
        return {
            "tools_count": len(tools),
            "tool_names": [t['function']['name'] for t in tools],
            "drive_tool_exists": any(t['function']['name'] == 'google_drive-list-files' for t in tools),
            "test_result": test_result
        }
    except Exception as e:
        print(f"[ERROR] Test tools failed: {e}")
        return {"error": str(e)} 