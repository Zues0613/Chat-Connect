from pydantic import BaseModel, EmailStr
from prisma import Prisma
from fastapi import APIRouter, HTTPException, Depends, status, Request, Query
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import RedirectResponse
from app.auth.models import SendOTPRequest, VerifyOTPRequest, TokenResponse, MeResponse
from app.auth.otp_manager import OTPManager
from app.auth.jwt_handler import create_access_token, decode_access_token
from app.auth.send_email import send_email
from app.services.oauth_service import oauth_service
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from app.auth.models import MCPServerRequest
from app.auth.models import APIKeyRequest
from typing import List, Dict, Any, Optional
import json
import os
import asyncio
from datetime import datetime, timedelta

router = APIRouter()
otp_manager = OTPManager()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Registration request model
class RegisterRequest(BaseModel):
    name: str
    email: EmailStr

# Register endpoint
@router.post("/register")
async def register_user(data: RegisterRequest):
    prisma = Prisma()
    await prisma.connect()
    existing = await prisma.user.find_unique(where={"email": data.email})
    if existing:
        await prisma.disconnect()
        raise HTTPException(status_code=400, detail="Email already registered.")
    user = await prisma.user.create(
        data={
            "name": data.name,
            "email": data.email,
        }
    )
    await prisma.disconnect()
    return {"message": "Registration successful", "user": {"id": user.id, "name": user.name, "email": user.email}}


@router.post("/send-otp")
def send_otp(data: SendOTPRequest):
    # For test email, don't actually send email
    if data.email == "test@gmail.com":
        print(f"[DEBUG] Test email detected: {data.email}, skipping actual email send")
        return {"message": "OTP sent to email (test mode)."}
    
    otp = otp_manager.generate_otp(data.email)
    send_email(data.email, otp)
    return {"message": "OTP sent to email."}

@router.post("/verify-otp", response_model=TokenResponse)
async def verify_otp(data: VerifyOTPRequest):
    if not otp_manager.verify_otp(data.email, data.otp):
        raise HTTPException(status_code=400, detail="Invalid or expired OTP.")
    
    # Ensure user exists in database (especially for test email)
    prisma = Prisma()
    await prisma.connect()
    
    # Check if user exists
    existing_user = await prisma.user.find_unique(where={"email": data.email})
    
    if not existing_user:
        # Create user if they don't exist (especially for test email)
        if data.email == "test@gmail.com":
            user = await prisma.user.create(
                data={
                    "name": "Test Admin",
                    "email": data.email,
                }
            )
            print(f"[DEBUG] Created test user: {user.name} ({user.email})")
        else:
            await prisma.disconnect()
            raise HTTPException(status_code=400, detail="User not found. Please register first.")
    else:
        print(f"[DEBUG] User found: {existing_user.name} ({existing_user.email})")
    
    await prisma.disconnect()
    
    token = create_access_token({"sub": data.email})
    print(f"[DEBUG] Generated token for {data.email}: {token[:20]}...")
    return TokenResponse(access_token=token)

@router.get("/me", response_model=MeResponse)
async def get_me(token: str = Depends(oauth2_scheme)):
    try:
        print(f"[DEBUG] /auth/me called with token: {token[:20]}..." if token else "[DEBUG] /auth/me called with no token")
        payload = decode_access_token(token)
        print(f"[DEBUG] Decoded payload: {payload}")
        email = payload.get("sub")
        if not email:
            print("[DEBUG] No email found in token payload")
            raise HTTPException(status_code=401, detail="Invalid token.")
        
        print(f"[DEBUG] User email from token: {email}")
        
        # Get user details from database
        prisma = Prisma()
        await prisma.connect()
        
        user = await prisma.user.find_unique(where={"email": email})
        if not user:
            await prisma.disconnect()
            raise HTTPException(status_code=404, detail="User not found.")
        
        await prisma.disconnect()
        
        print(f"[DEBUG] User found: {user.name} ({user.email})")
        return MeResponse(email=user.email, name=user.name)
        
    except Exception as e:
        print(f"[DEBUG] Error in /auth/me: {e}")
        raise HTTPException(status_code=401, detail="Invalid or expired token.")

@router.get("/mcp-servers")
async def get_mcp_servers(token: str = Depends(oauth2_scheme)):
    """Get all MCP servers for the authenticated user"""
    try:
        payload = decode_access_token(token)
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token.")
        
        # Get user from database
        prisma = Prisma()
        await prisma.connect()
        
        # Find user by email
        user = await prisma.user.find_unique(where={"email": email})
        if not user:
            await prisma.disconnect()
            raise HTTPException(status_code=404, detail="User not found.")
        
        # Get all MCP servers for the user
        servers = await prisma.mcpserver.find_many(where={"userId": user.id})
        
        await prisma.disconnect()
        
        # Convert to response format
        server_list = []
        for server in servers:
            server_list.append({
                "id": server.id,
                "name": server.name,
                "description": server.description,
                "config": server.config,
                "createdAt": server.createdAt.isoformat()
            })
        
        print(f"[DEBUG] Found {len(server_list)} MCP servers for user {email}")
        return server_list
        
    except Exception as e:
        print(f"[DEBUG] Error getting MCP servers: {e}")
        raise HTTPException(status_code=500, detail="Failed to get MCP servers.")

@router.post("/mcp-servers")
async def create_mcp_server(request: MCPServerRequest, token: str = Depends(oauth2_scheme)):
    """Create a new MCP server for the authenticated user"""
    try:
        payload = decode_access_token(token)
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token.")
        
        # Get user from database
        prisma = Prisma()
        await prisma.connect()
        
        # Find user by email
        user = await prisma.user.find_unique(where={"email": email})
        if not user:
            await prisma.disconnect()
            raise HTTPException(status_code=404, detail="User not found.")
        
        # Validate MCP server configuration
        config = request.config or {}
        uri = config.get("uri", "")
        
        # Special handling for Pipedream URLs
        if "pipedream.net" in uri:
            print(f"[DEBUG] Adding Pipedream MCP server: {uri}")
            
            # Validate Pipedream URL format
            if not uri.startswith("https://mcp.pipedream.net/"):
                raise HTTPException(
                    status_code=400, 
                    detail="Invalid Pipedream URL. Expected format: https://mcp.pipedream.net/[workflow-id]/[endpoint]"
                )
            
            # Set appropriate configuration for Pipedream
            config.update({
                "type": "custom",
                "transport": "http",
                "name": request.name,
                "pipedream_workflow": True
            })
            
            # Test the Pipedream connection
            try:
                test_result = await test_pipedream_connection(uri)
                if not test_result["success"]:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Failed to connect to Pipedream workflow: {test_result['error']}"
                    )
                print(f"[DEBUG] Pipedream connection test successful: {test_result['tools_count']} tools found")
            except Exception as e:
                print(f"[DEBUG] Pipedream connection test failed: {e}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to test Pipedream connection: {str(e)}"
                )
        
        # Create MCP server in database
        server = await prisma.mcpserver.create(
            data={
                "userId": user.id,
                "name": request.name,
                "description": request.description,
                "config": config
            }
        )
        
        await prisma.disconnect()
        
        # Return the created server
        server_response = {
            "id": server.id,
            "name": server.name,
            "description": server.description,
            "config": server.config,
            "createdAt": server.createdAt.isoformat()
        }
        
        print(f"[DEBUG] Created MCP server: {server_response['name']} for user {email}")
        return server_response
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[DEBUG] Error creating MCP server: {e}")
        raise HTTPException(status_code=500, detail="Failed to create MCP server.")

@router.delete("/mcp-servers/{server_id}")
async def delete_mcp_server(server_id: int, token: str = Depends(oauth2_scheme)):
    """Delete an MCP server for the authenticated user"""
    try:
        payload = decode_access_token(token)
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token.")
        
        # Get user and verify ownership
        prisma = Prisma()
        await prisma.connect()
        
        # Find user by email
        user = await prisma.user.find_unique(where={"email": email})
        if not user:
            await prisma.disconnect()
            raise HTTPException(status_code=404, detail="User not found.")
        
        # Find the MCP server and verify ownership
        server = await prisma.mcpserver.find_first(
            where={
                "id": server_id,
                "userId": user.id
            }
        )
        
        if not server:
            await prisma.disconnect()
            raise HTTPException(status_code=404, detail="MCP server not found.")
        
        # Delete the server
        await prisma.mcpserver.delete(where={"id": server_id})
        
        await prisma.disconnect()
        
        print(f"[DEBUG] Deleted MCP server: {server.name} for user {email}")
        return {"message": "MCP server deleted successfully."}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[DEBUG] Error deleting MCP server: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete MCP server.")

@router.post("/mcp-servers/{server_id}/test")
async def test_mcp_server(server_id: int, token: str = Depends(oauth2_scheme)):
    """Test connection to an MCP server"""
    try:
        payload = decode_access_token(token)
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token.")
        
        # Get user and verify ownership
        prisma = Prisma()
        await prisma.connect()
        
        # Find user by email
        user = await prisma.user.find_unique(where={"email": email})
        if not user:
            await prisma.disconnect()
            raise HTTPException(status_code=404, detail="User not found.")
        
        # Find the MCP server and verify ownership
        server = await prisma.mcpserver.find_first(
            where={
                "id": server_id,
                "userId": user.id
            }
        )
        
        if not server:
            await prisma.disconnect()
            raise HTTPException(status_code=404, detail="MCP server not found.")
        
        await prisma.disconnect()
        
        # Test the connection based on server type
        config = server.config
        uri = config.get("uri", "")
        
        if "pipedream.net" in uri:
            test_result = await test_pipedream_connection(uri)
        else:
            test_result = await test_generic_mcp_connection(uri, config)
        
        return test_result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[DEBUG] Error testing MCP server: {e}")
        raise HTTPException(status_code=500, detail="Failed to test MCP server.")

async def test_pipedream_connection(uri: str) -> Dict[str, Any]:
    """Test connection to a Pipedream MCP server"""
    try:
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            # Test the connection with a tools/list request
            test_request = {
                "jsonrpc": "2.0",
                "id": "test_connection",
                "method": "tools/list",
                "params": {}
            }
            
            timeout = aiohttp.ClientTimeout(total=30)
            async with session.post(
                uri,
                json=test_request,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream"
                },
                timeout=timeout
            ) as response:
                if response.status == 200:
                    content_type = response.headers.get('content-type', '')
                    
                    if 'text/event-stream' in content_type:
                        # Handle Server-Sent Events response
                        response_text = await response.text()
                        lines = response_text.strip().split('\n')
                        
                        for line in lines:
                            if line.startswith('data: '):
                                try:
                                    data_json = line[6:]
                                    tools_data = json.loads(data_json)
                                    if "result" in tools_data and "tools" in tools_data["result"]:
                                        tools = tools_data["result"]["tools"]
                                        return {
                                            "success": True,
                                            "tools_count": len(tools),
                                            "tools": [tool.get("name", "") for tool in tools],
                                            "message": f"Successfully connected to Pipedream workflow. Found {len(tools)} tools."
                                        }
                                except:
                                    continue
                        
                        return {
                            "success": False,
                            "error": "Invalid response format from Pipedream workflow"
                        }
                    else:
                        # Handle regular JSON response
                        response_data = await response.json()
                        if "result" in response_data and "tools" in response_data["result"]:
                            tools = response_data["result"]["tools"]
                            return {
                                "success": True,
                                "tools_count": len(tools),
                                "tools": [tool.get("name", "") for tool in tools],
                                "message": f"Successfully connected to Pipedream workflow. Found {len(tools)} tools."
                            }
                        else:
                            return {
                                "success": False,
                                "error": "No tools found in Pipedream workflow response"
                            }
                else:
                    return {
                        "success": False,
                        "error": f"HTTP {response.status}: {await response.text()}"
                    }
                    
    except asyncio.TimeoutError:
        return {
            "success": False,
            "error": "Connection timeout. Pipedream workflow is not responding."
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Connection failed: {str(e)}"
        }

async def test_generic_mcp_connection(uri: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """Test connection to a generic MCP server"""
    try:
        import aiohttp
        
        # Try different connection methods based on config
        server_type = config.get("type", "custom")
        
        if server_type == "custom":
            # Test HTTP connection
            async with aiohttp.ClientSession() as session:
                timeout = aiohttp.ClientTimeout(total=30)
                async with session.get(uri, timeout=timeout) as response:
                    if response.status == 200:
                        return {
                            "success": True,
                            "message": "Successfully connected to MCP server"
                        }
                    else:
                        return {
                            "success": False,
                            "error": f"HTTP {response.status}: Server not responding correctly"
                        }
        else:
            return {
                "success": False,
                "error": f"Unsupported server type: {server_type}"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Connection failed: {str(e)}"
        }

@router.get("/api-keys")
async def get_api_keys(token: str = Depends(oauth2_scheme)):
    """Get API keys for the authenticated user"""
    try:
        payload = decode_access_token(token)
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token.")
        
        # Get user and their API keys from database
        prisma = Prisma()
        await prisma.connect()
        
        # Find user by email
        user = await prisma.user.find_unique(where={"email": email})
        if not user:
            await prisma.disconnect()
            raise HTTPException(status_code=404, detail="User not found.")
        
        # Get API keys for this user
        api_keys = await prisma.apikey.find_many(where={"userId": user.id})
        
        await prisma.disconnect()
        
        # Convert to response format (mask the values)
        key_list = []
        for key in api_keys:
            key_list.append({
                "id": key.id,
                "name": key.name,
                "provider": key.provider,
                "value": "sk-..." + "x" * 20,  # Masked value
                "createdAt": key.createdAt.isoformat()
            })
        
        print(f"[DEBUG] Found {len(key_list)} API keys for user {email}")
        return key_list
    except Exception as e:
        print(f"[DEBUG] Error getting API keys: {e}")
        raise HTTPException(status_code=500, detail="Failed to get API keys.")

@router.post("/api-keys")
async def create_api_key(request: APIKeyRequest, token: str = Depends(oauth2_scheme)):
    """Create a new API key for the authenticated user"""
    try:
        payload = decode_access_token(token)
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token.")
        
        # Get user from database
        prisma = Prisma()
        await prisma.connect()
        
        # Find user by email
        user = await prisma.user.find_unique(where={"email": email})
        if not user:
            await prisma.disconnect()
            raise HTTPException(status_code=404, detail="User not found.")
        
        # Create API key in database
        api_key = await prisma.apikey.create(
            data={
                "userId": user.id,
                "name": request.name,
                "provider": request.provider,
                "value": request.value
            }
        )
        
        await prisma.disconnect()
        
        # Return the created API key (with masked value)
        key_response = {
            "id": api_key.id,
            "name": api_key.name,
            "provider": api_key.provider,
            "value": "sk-..." + "x" * 20,  # Masked value
            "createdAt": api_key.createdAt.isoformat()
        }
        
        print(f"[DEBUG] Created API key: {key_response['name']} for user {email}")
        return key_response
    except Exception as e:
        print(f"[DEBUG] Error creating API key: {e}")
        raise HTTPException(status_code=500, detail="Failed to create API key.")

@router.delete("/api-keys/{key_id}")
async def delete_api_key(key_id: int, token: str = Depends(oauth2_scheme)):
    """Delete an API key"""
    try:
        payload = decode_access_token(token)
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token.")
        
        # Get user and verify ownership
        prisma = Prisma()
        await prisma.connect()
        
        # Find user by email
        user = await prisma.user.find_unique(where={"email": email})
        if not user:
            await prisma.disconnect()
            raise HTTPException(status_code=404, detail="User not found.")
        
        # Find the API key and verify ownership
        api_key = await prisma.apikey.find_first(
            where={
                "id": key_id,
                "userId": user.id
            }
        )
        
        if not api_key:
            await prisma.disconnect()
            raise HTTPException(status_code=404, detail="API key not found.")
        
        # Delete the API key
        await prisma.apikey.delete(where={"id": key_id})
        await prisma.disconnect()
        
        return {"message": "API key deleted successfully."}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[DEBUG] Error deleting API key: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete API key.")

# OAuth Endpoints
@router.post("/oauth/authorize")
async def initiate_oauth_flow(
    server_id: int,
    provider: Optional[str] = None,
    token: str = Depends(oauth2_scheme)
):
    """Initiate OAuth flow for an MCP server"""
    try:
        payload = decode_access_token(token)
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token.")
        
        # Get user and verify ownership
        prisma = Prisma()
        await prisma.connect()
        
        # Find user by email
        user = await prisma.user.find_unique(where={"email": email})
        if not user:
            await prisma.disconnect()
            raise HTTPException(status_code=404, detail="User not found.")
        
        # Find the MCP server and verify ownership
        server = await prisma.mcpserver.find_first(
            where={
                "id": server_id,
                "userId": user.id
            }
        )
        
        if not server:
            await prisma.disconnect()
            raise HTTPException(status_code=404, detail="MCP server not found.")
        
        await prisma.disconnect()
        
        # Detect provider if not specified
        if not provider:
            provider = oauth_service.detect_oauth_provider_from_url(server.config.get("uri", ""))
        
        if not provider:
            raise HTTPException(status_code=400, detail="Could not detect OAuth provider for this server.")
        
        # Connect to OAuth service
        await oauth_service.connect()
        
        # Create OAuth state
        redirect_uri = os.getenv("OAUTH_REDIRECT_URI", "http://localhost:3000/oauth/callback")
        state = await oauth_service.create_oauth_state(
            user_id=user.id,
            server_id=server.id,
            provider=provider,
            redirect_uri=redirect_uri
        )
        
        # Generate OAuth URL
        oauth_url = oauth_service.generate_oauth_url(provider, state)
        
        if not oauth_url:
            await oauth_service.disconnect()
            raise HTTPException(status_code=500, detail="Failed to generate OAuth URL.")
        
        await oauth_service.disconnect()
        
        return {
            "oauth_url": oauth_url,
            "state": state,
            "provider": provider,
            "server_name": server.name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[DEBUG] Error initiating OAuth flow: {e}")
        raise HTTPException(status_code=500, detail="Failed to initiate OAuth flow.")

@router.get("/oauth/callback")
async def oauth_callback(
    code: str = Query(...),
    state: str = Query(...),
    error: Optional[str] = Query(None)
):
    """Handle OAuth callback from provider"""
    try:
        if error:
            # OAuth error occurred
            return RedirectResponse(
                url=f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/settings?tab=mcp-servers&oauth_error={error}"
            )
        
        # Connect to OAuth service
        await oauth_service.connect()
        
        # Validate OAuth state
        oauth_state = await oauth_service.validate_oauth_state(state)
        if not oauth_state:
            await oauth_service.disconnect()
            return RedirectResponse(
                url=f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/settings?tab=mcp-servers&oauth_error=invalid_state"
            )
        
        # Exchange code for tokens
        tokens = await oauth_service.exchange_code_for_tokens(
            oauth_state["provider"], 
            code
        )
        
        if not tokens:
            await oauth_service.cleanup_oauth_state(oauth_state["id"])
            await oauth_service.disconnect()
            return RedirectResponse(
                url=f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/settings?tab=mcp-servers&oauth_error=token_exchange_failed"
            )
        
        # Store tokens
        await oauth_service.store_oauth_tokens(
            oauth_state["userId"],
            oauth_state["serverId"],
            oauth_state["provider"],
            tokens
        )
        
        # Clean up OAuth state
        await oauth_service.cleanup_oauth_state(oauth_state["id"])
        await oauth_service.disconnect()
        
        # Redirect back to settings with success message
        return RedirectResponse(
            url=f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/settings?tab=mcp-servers&oauth_success=true&server_name={oauth_state['server'].name}"
        )
        
    except Exception as e:
        print(f"[DEBUG] Error in OAuth callback: {e}")
        return RedirectResponse(
            url=f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/settings?tab=mcp-servers&oauth_error=callback_failed"
        )

@router.get("/oauth/status")
async def get_oauth_status(token: str = Depends(oauth2_scheme)):
    """Get OAuth status for all user's MCP servers"""
    try:
        payload = decode_access_token(token)
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token.")
        
        # Get user
        prisma = Prisma()
        await prisma.connect()
        
        user = await prisma.user.find_unique(where={"email": email})
        if not user:
            await prisma.disconnect()
            raise HTTPException(status_code=404, detail="User not found.")
        
        await prisma.disconnect()
        
        # Connect to OAuth service
        await oauth_service.connect()
        
        # Get OAuth status
        status_list = await oauth_service.get_user_oauth_status(user.id)
        
        await oauth_service.disconnect()
        
        return status_list
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[DEBUG] Error getting OAuth status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get OAuth status.")

@router.delete("/oauth/tokens/{server_id}")
async def revoke_oauth_tokens(
    server_id: int,
    provider: str,
    token: str = Depends(oauth2_scheme)
):
    """Revoke OAuth tokens for a specific server"""
    try:
        payload = decode_access_token(token)
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token.")
        
        # Get user and verify ownership
        prisma = Prisma()
        await prisma.connect()
        
        # Find user by email
        user = await prisma.user.find_unique(where={"email": email})
        if not user:
            await prisma.disconnect()
            raise HTTPException(status_code=404, detail="User not found.")
        
        # Find the MCP server and verify ownership
        server = await prisma.mcpserver.find_first(
            where={
                "id": server_id,
                "userId": user.id
            }
        )
        
        if not server:
            await prisma.disconnect()
            raise HTTPException(status_code=404, detail="MCP server not found.")
        
        await prisma.disconnect()
        
        # Connect to OAuth service
        await oauth_service.connect()
        
        # Delete OAuth tokens
        await oauth_service.delete_oauth_tokens(user.id, server_id, provider)
        
        await oauth_service.disconnect()
        
        return {"message": "OAuth tokens revoked successfully."}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[DEBUG] Error revoking OAuth tokens: {e}")
        raise HTTPException(status_code=500, detail="Failed to revoke OAuth tokens.")
