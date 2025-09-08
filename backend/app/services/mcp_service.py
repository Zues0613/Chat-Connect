import asyncio
import json
import subprocess
import aiohttp
import websockets
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
import logging
from app.services.oauth_service import oauth_service

logger = logging.getLogger(__name__)

# For now, we'll create a simplified MCP service without the actual MCP library
# since we don't have MCP servers set up yet. This will be ready for when you add them.

class MCPClient:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.server_type = config.get("type", "custom")
        self.uri = config.get("uri", "")
        self.transport = config.get("transport", "http")
        self.connection = None
        self.available_tools = []
        self.is_connected = False
        self.server_name = config.get("name", "Unknown Server")
        self.last_error = None
    
    async def connect(self) -> bool:
        """Connect to the MCP server based on transport type"""
        try:
            if self.server_type == "stdio":
                return await self._connect_stdio()
            elif self.server_type == "sse":
                return await self._connect_sse()
            elif self.server_type == "websocket":
                return await self._connect_websocket()
            else:
                return await self._connect_custom()
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Failed to connect to MCP server: {e}")
            return False
    
    async def _connect_stdio(self) -> bool:
        """Connect to stdio-based MCP server"""
        try:
            # Parse the command from URI
            command_parts = self.uri.split()
            if not command_parts:
                self.last_error = "Invalid stdio command"
                return False
            
            # Start the process
            self.connection = await asyncio.create_subprocess_exec(
                *command_parts,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Initialize MCP protocol
            init_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "1.0.0",
                    "capabilities": {
                        "tools": {}
                    },
                    "clientInfo": {
                        "name": "vee-chatbot",
                        "version": "1.0.0"
                    }
                }
            }
            
            # Send initialization
            init_message = json.dumps(init_request) + "\n"
            self.connection.stdin.write(init_message.encode())
            await self.connection.stdin.drain()
            
            # Read response
            response_line = await self.connection.stdout.readline()
            if response_line:
                response = json.loads(response_line.decode().strip())
                if "result" in response:
                    self.is_connected = True
                    await self._discover_tools()
                    return True
            
            self.last_error = "Failed to initialize stdio connection"
            return False
        except Exception as e:
            self.last_error = f"Stdio connection error: {str(e)}"
            logger.error(f"Failed to connect via stdio: {e}")
            return False
    
    async def _connect_sse(self) -> bool:
        """Connect to SSE-based MCP server"""
        try:
            async with aiohttp.ClientSession() as session:
                # Test connection to SSE endpoint
                async with session.get(self.uri) as response:
                    if response.status == 200:
                        self.is_connected = True
                        await self._discover_tools()
                        return True
            self.last_error = "SSE connection failed"
            return False
        except Exception as e:
            self.last_error = f"SSE connection error: {str(e)}"
            logger.error(f"Failed to connect via SSE: {e}")
            return False
    
    async def _connect_websocket(self) -> bool:
        """Connect to WebSocket-based MCP server"""
        try:
            self.connection = await websockets.connect(self.uri)
            
            # Initialize MCP protocol
            init_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "1.0.0",
                    "capabilities": {"tools": {}},
                    "clientInfo": {"name": "vee-chatbot", "version": "1.0.0"}
                }
            }
            
            await self.connection.send(json.dumps(init_request))
            response = await self.connection.recv()
            response_data = json.loads(response)
            
            if "result" in response_data:
                self.is_connected = True
                await self._discover_tools()
                return True
            
            self.last_error = "WebSocket initialization failed"
            return False
        except Exception as e:
            self.last_error = f"WebSocket connection error: {str(e)}"
            logger.error(f"Failed to connect via WebSocket: {e}")
            return False
    
    async def _connect_custom(self) -> bool:
        """Connect to custom MCP server"""
        try:
            # For now, assume it's a simple HTTP endpoint
            parsed = urlparse(self.uri)
            if parsed.scheme in ['http', 'https']:
                async with aiohttp.ClientSession() as session:
                    # First try the /health endpoint
                    try:
                        async with session.get(self.uri + '/health') as response:
                            if response.status == 200:
                                self.is_connected = True
                                await self._discover_tools()
                                return True
                    except:
                        pass
                    
                    # If /health fails, try connecting directly to the base URL
                    # This is common for Pipedream MCP servers
                    try:
                        async with session.get(self.uri) as response:
                            if response.status in [200, 404, 405]:  # Accept various responses
                                self.is_connected = True
                                await self._discover_tools()
                                return True
                    except:
                        pass
                    
                    # For Pipedream MCP servers, we need to establish a session
                    if "pipedream.net" in self.uri:
                        logger.info(f"Establishing Pipedream MCP session: {self.uri}")
                        
                        # Get the session endpoint from the initial response
                        async with session.get(self.uri) as response:
                            if response.status == 200:
                                response_text = await response.text()
                                logger.info(f"Pipedream initial response: {response_text}")
                                
                                # Parse the session endpoint from SSE response
                                lines = response_text.strip().split('\n')
                                session_endpoint = None
                                
                                for line in lines:
                                    if line.startswith('data: '):
                                        try:
                                            data_json = line[6:]  # Remove "data: " prefix
                                            if data_json.startswith('/v1/'):
                                                session_endpoint = data_json
                                                break
                                        except:
                                            continue
                                
                                if session_endpoint:
                                    # Store the session endpoint for future use
                                    self.session_endpoint = session_endpoint
                                    logger.info(f"Pipedream session endpoint: {session_endpoint}")
                                    self.is_connected = True
                                    await self._discover_tools()
                                    return True
                                else:
                                    logger.warning("Could not parse session endpoint, trying fallback")
                                    self.is_connected = True
                                    await self._discover_tools()
                                    return True
                            else:
                                logger.error(f"Pipedream connection failed with status: {response.status}")
                                return False
                        
            self.last_error = f"Custom connection failed for URI: {self.uri}"
            return False
        except Exception as e:
            self.last_error = f"Custom connection error: {str(e)}"
            logger.error(f"Failed to connect via custom: {e}")
            return False
    
    async def _discover_tools(self) -> None:
        """Discover available tools from the MCP server"""
        try:
            if not self.is_connected:
                return
            
            tools_request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {}
            }
            
            if self.server_type == "stdio" and self.connection:
                # Send tools request
                message = json.dumps(tools_request) + "\n"
                self.connection.stdin.write(message.encode())
                await self.connection.stdin.drain()
                
                # Read response
                response_line = await self.connection.stdout.readline()
                if response_line:
                    response = json.loads(response_line.decode().strip())
                    if "result" in response and "tools" in response["result"]:
                        self.available_tools = response["result"]["tools"]
            
            elif self.server_type == "websocket" and self.connection:
                await self.connection.send(json.dumps(tools_request))
                response = await self.connection.recv()
                response_data = json.loads(response)
                if "result" in response_data and "tools" in response_data["result"]:
                    self.available_tools = response_data["result"]["tools"]
            
            elif self.server_type in ["custom", "sse"] and self.uri:
                # Handle HTTP-based MCP servers (like Pipedream)
                try:
                    async with aiohttp.ClientSession() as session:
                        # Try POST request to the MCP server with proper headers
                        headers = {
                            "Content-Type": "application/json",
                            "Accept": "application/json, text/event-stream"
                        }
                        
                        async with session.post(
                            self.uri,
                            json=tools_request,
                            headers=headers
                        ) as response:
                            if response.status == 200:
                                content_type = response.headers.get('content-type', '')
                                
                                # Handle Server-Sent Events (text/event-stream)
                                if 'text/event-stream' in content_type:
                                    logger.info("Detected Server-Sent Events response, parsing SSE stream")
                                    try:
                                        # Read the SSE stream and extract JSON data
                                        async for line in response.content:
                                            line = line.decode('utf-8').strip()
                                            if line.startswith('data: '):
                                                data = line[6:]  # Remove 'data: ' prefix
                                                if data and data != '[DONE]':
                                                    try:
                                                        response_data = json.loads(data)
                                                        if "result" in response_data and "tools" in response_data["result"]:
                                                            self.available_tools = response_data["result"]["tools"]
                                                            logger.info(f"Discovered {len(self.available_tools)} tools via SSE")
                                                            return
                                                    except json.JSONDecodeError:
                                                        continue
                                    except Exception as e:
                                        logger.error(f"Failed to parse SSE stream: {e}")
                                
                                # Handle regular JSON response
                                else:
                                    try:
                                        response_data = await response.json()
                                        if "result" in response_data and "tools" in response_data["result"]:
                                            self.available_tools = response_data["result"]["tools"]
                                            logger.info(f"Discovered {len(self.available_tools)} tools via HTTP JSON")
                                            return
                                    except Exception as e:
                                        logger.error(f"Failed to parse JSON response: {e}")
                                        
                            elif response.status == 406:
                                logger.info("Server requires both JSON and SSE support, trying alternative approach")
                                # Try with different headers or approach
                                pass
                        
                        # If POST fails, try GET request to /tools endpoint
                        try:
                            tools_url = self.uri.rstrip('/') + '/tools'
                            async with session.get(tools_url, headers=headers) as response:
                                if response.status == 200:
                                    content_type = response.headers.get('content-type', '')
                                    
                                    # Handle Server-Sent Events (text/event-stream)
                                    if 'text/event-stream' in content_type:
                                        logger.info("Detected Server-Sent Events response in GET request, parsing SSE stream")
                                        try:
                                            # Read the SSE stream and extract JSON data
                                            async for line in response.content:
                                                line = line.decode('utf-8').strip()
                                                if line.startswith('data: '):
                                                    data = line[6:]  # Remove 'data: ' prefix
                                                    if data and data != '[DONE]':
                                                        try:
                                                            response_data = json.loads(data)
                                                            if "tools" in response_data:
                                                                self.available_tools = response_data["tools"]
                                                                logger.info(f"Discovered {len(self.available_tools)} tools via GET /tools SSE")
                                                                return
                                                        except json.JSONDecodeError:
                                                            continue
                                        except Exception as e:
                                            logger.error(f"Failed to parse SSE stream in GET request: {e}")
                                    
                                    # Handle regular JSON response
                                    else:
                                        try:
                                            response_data = await response.json()
                                            if "tools" in response_data:
                                                self.available_tools = response_data["tools"]
                                                logger.info(f"Discovered {len(self.available_tools)} tools via GET /tools JSON")
                                                return
                                        except Exception as e:
                                            logger.error(f"Failed to parse JSON response in GET request: {e}")
                        except Exception as e:
                            logger.error(f"GET /tools request failed: {e}")
                            pass
                        
                        # For Pipedream MCP servers, we might need to hardcode some known tools
                        if "pipedream.net" in self.uri:
                            logger.info("Using hardcoded tools for Pipedream MCP server")
                            
                            # Base tools for any Pipedream MCP server
                            base_tools = [
                                {
                                    "name": "mcp_Gmail_gmail-send-email",
                                    "description": "Send an email from your Google Workspace email account",
                                    "inputSchema": {
                                        "type": "object",
                                        "properties": {
                                            "instruction": {
                                                "type": "string",
                                                "description": "Very detailed instructions describing the action to be taken"
                                            }
                                        },
                                        "required": ["instruction"]
                                    }
                                },
                                {
                                    "name": "mcp_Gmail_gmail-find-email",
                                    "description": "Find an email using Google's Search Engine",
                                    "inputSchema": {
                                        "type": "object",
                                        "properties": {
                                            "instruction": {
                                                "type": "string",
                                                "description": "Very detailed instructions describing the action to be taken"
                                            }
                                        },
                                        "required": ["instruction"]
                                    }
                                },
                                {
                                    "name": "mcp_Gmail_gmail-list-labels",
                                    "description": "List all the existing labels in the connected account",
                                    "inputSchema": {
                                        "type": "object",
                                        "properties": {
                                            "instruction": {
                                                "type": "string",
                                                "description": "Very detailed instructions describing the action to be taken"
                                            }
                                        },
                                        "required": ["instruction"]
                                    }
                                },
                                {
                                    "name": "mcp_Gmail_gmail-create-draft",
                                    "description": "Create a draft from your Google Workspace email account",
                                    "inputSchema": {
                                        "type": "object",
                                        "properties": {
                                            "instruction": {
                                                "type": "string",
                                                "description": "Very detailed instructions describing the action to be taken"
                                            }
                                        },
                                        "required": ["instruction"]
                                    }
                                },
                                {
                                    "name": "mcp_Gmail_gmail-add-label-to-email",
                                    "description": "Add label(s) to an email message",
                                    "inputSchema": {
                                        "type": "object",
                                        "properties": {
                                            "instruction": {
                                                "type": "string",
                                                "description": "Very detailed instructions describing the action to be taken"
                                            }
                                        },
                                        "required": ["instruction"]
                                    }
                                },
                                {
                                    "name": "mcp_Gmail_gmail-remove-label-from-email",
                                    "description": "Remove label(s) from an email message",
                                    "inputSchema": {
                                        "type": "object",
                                        "properties": {
                                            "instruction": {
                                                "type": "string",
                                                "description": "Very detailed instructions describing the action to be taken"
                                            }
                                        },
                                        "required": ["instruction"]
                                    }
                                },
                                {
                                    "name": "mcp_Gmail_gmail-archive-email",
                                    "description": "Archive an email message",
                                    "inputSchema": {
                                        "type": "object",
                                        "properties": {
                                            "instruction": {
                                                "type": "string",
                                                "description": "Very detailed instructions describing the action to be taken"
                                            }
                                        },
                                        "required": ["instruction"]
                                    }
                                },
                                {
                                    "name": "mcp_Gmail_gmail-delete-email",
                                    "description": "Moves the specified message to the trash",
                                    "inputSchema": {
                                        "type": "object",
                                        "properties": {
                                            "instruction": {
                                                "type": "string",
                                                "description": "Very detailed instructions describing the action to be taken"
                                            }
                                        },
                                        "required": ["instruction"]
                                    }
                                }
                            ]
                            
                            # Add specific tools based on the server type
                            if "gmail" in self.uri:
                                logger.info("Adding Gmail-specific tools")
                                self.available_tools = base_tools
                            else:
                                # For other Pipedream servers, use base tools
                                self.available_tools = base_tools
                            
                            logger.info(f"Hardcoded {len(self.available_tools)} tools for Pipedream server")
                            
                except Exception as e:
                    logger.error(f"Failed to discover tools via HTTP: {e}")
            
            logger.info(f"Discovered {len(self.available_tools)} tools")
            
        except Exception as e:
            logger.error(f"Failed to discover tools: {e}")
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any], user_id: Optional[int] = None) -> Dict[str, Any]:
        """Call a specific tool with given arguments"""
        try:
            # Step 1: Log the function call generation
            logger.info(f"🔧 [MCP DEBUG] 1. Function call generated:")
            logger.info(f"   Tool: {tool_name}")
            logger.info(f"   Arguments: {json.dumps(arguments, indent=2)}")
            logger.info(f"   Server: {self.server_name} ({self.server_type})")
            
            if not self.is_connected:
                logger.error(f"❌ [MCP DEBUG] Connection check failed - not connected")
                return {
                    "error": f"MCP server '{self.server_name}' is not connected",
                    "error_type": "connection_error",
                    "server_name": self.server_name,
                    "last_error": self.last_error
                }
            
            logger.info(f"✅ [MCP DEBUG] 2. Connection verified - proceeding with execution")
            
            # Step 1.5: Check for OAuth tokens if user_id is provided
            oauth_tokens = None
            if user_id:
                # Detect provider from server URI
                provider = oauth_service.detect_oauth_provider_from_url(self.uri)
                if provider:
                    # Get server ID from config or generate one
                    server_id = getattr(self, 'server_id', None)
                    if server_id:
                        await oauth_service.connect()
                        oauth_tokens = await oauth_service.get_oauth_tokens(user_id, server_id, provider)
                        await oauth_service.disconnect()
                        
                        if oauth_tokens:
                            logger.info(f"🔐 [MCP DEBUG] 2.5. OAuth tokens found for provider: {provider}")
                        else:
                            logger.info(f"🔐 [MCP DEBUG] 2.5. No OAuth tokens found for provider: {provider}")
            
            call_request = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }
            
            # Step 2: Log the MCP request being sent
            logger.info(f"📤 [MCP DEBUG] 3. Sending MCP request:")
            logger.info(f"   Request: {json.dumps(call_request, indent=2)}")
            
            if self.server_type == "stdio" and self.connection:
                # Send tool call request
                message = json.dumps(call_request) + "\n"
                self.connection.stdin.write(message.encode())
                await self.connection.stdin.drain()
                
                # Read response
                response_line = await self.connection.stdout.readline()
                if response_line:
                    response = json.loads(response_line.decode().strip())
                    if "result" in response:
                        return response["result"]
                    elif "error" in response:
                        return {"error": response["error"]}
            
            elif self.server_type == "websocket" and self.connection:
                await self.connection.send(json.dumps(call_request))
                response = await self.connection.recv()
                response_data = json.loads(response)
                if "result" in response_data:
                    return response_data["result"]
                elif "error" in response_data:
                    return {"error": response_data["error"]}
            
            elif self.server_type in ["custom", "sse"] and self.uri:
                # Handle HTTP-based MCP servers (like Pipedream)
                try:
                    async with aiohttp.ClientSession() as session:
                        # Try POST request to the MCP server
                        async with session.post(
                            self.uri,
                            json=call_request,
                            headers={"Content-Type": "application/json"}
                        ) as response:
                            if response.status == 200:
                                response_data = await response.json()
                                if "result" in response_data:
                                    return response_data["result"]
                                elif "error" in response_data:
                                    return {"error": response_data["error"]}
                        
                        # For Pipedream MCP servers, handle tool calls properly
                        if "pipedream.net" in self.uri:
                            logger.info(f"🌐 [MCP DEBUG] 4. Handling Pipedream MCP tool call: {tool_name}")
                            
                            # Use session endpoint if available, otherwise fall back to base URI
                            target_uri = self.uri
                            if hasattr(self, 'session_endpoint') and self.session_endpoint:
                                # Construct the full session URL
                                base_uri = self.uri.rstrip('/')
                                if self.session_endpoint.startswith('/'):
                                    target_uri = base_uri + self.session_endpoint
                                else:
                                    target_uri = base_uri + '/' + self.session_endpoint
                                logger.info(f"Using Pipedream session endpoint: {target_uri}")
                            
                            # Make a proper HTTP POST request to the Pipedream endpoint using JSON-RPC 2.0
                            try:
                                pipedream_request = {
                                    "jsonrpc": "2.0",
                                    "id": 1,
                                    "method": "tools/call",
                                    "params": {
                                        "name": tool_name,
                                        "arguments": arguments
                                    }
                                }
                                
                                # Add OAuth headers if tokens are available
                                headers = {
                                    "Content-Type": "application/json",
                                    "Accept": "application/json, text/event-stream",
                                    "User-Agent": "VeeChatbot-MCP-Client/1.0"
                                }
                                
                                if oauth_tokens and oauth_tokens.get("access_token"):
                                    headers["Authorization"] = f"{oauth_tokens['token_type']} {oauth_tokens['access_token']}"
                                    logger.info(f"🔐 [MCP DEBUG] 4.5. Added OAuth authorization header")
                                
                                logger.info(f"📡 [MCP DEBUG] 5. Making HTTP request to Pipedream:")
                                logger.info(f"   URL: {target_uri}")
                                logger.info(f"   Request: {json.dumps(pipedream_request, indent=2)}")
                                logger.info(f"   Headers: {headers}")
                                
                                async with session.post(
                                    target_uri,
                                    json=pipedream_request,
                                    headers=headers,
                                    timeout=aiohttp.ClientTimeout(total=120)  # Increased timeout for OAuth flow
                                ) as pipedream_response:
                                    
                                    logger.info(f"📥 [MCP DEBUG] 6. Received Pipedream response:")
                                    logger.info(f"   Status: {pipedream_response.status}")
                                    logger.info(f"   Headers: {dict(pipedream_response.headers)}")
                                    
                                    if pipedream_response.status == 200:
                                        # Handle Server-Sent Events (SSE) response
                                        content_type = pipedream_response.headers.get('content-type', '')
                                        
                                        if 'text/event-stream' in content_type:
                                            # Parse SSE response
                                            response_text = await pipedream_response.text()
                                            logger.info(f"Pipedream SSE response: {response_text}")
                                            
                                            # Parse SSE format: "event: message\ndata: {...}"
                                            lines = response_text.strip().split('\n')
                                            for line in lines:
                                                if line.startswith('data: '):
                                                    try:
                                                        data_json = line[6:]  # Remove "data: " prefix
                                                        response_data = json.loads(data_json)
                                                        logger.info(f"Parsed SSE data: {response_data}")
                                                        
                                                        # Check for OAuth authentication requirements
                                                        if isinstance(response_data, dict):
                                                            # Check if response indicates OAuth is needed
                                                            if "error" in response_data and "oauth" in response_data["error"].lower():
                                                                result = {
                                                                    "error": "OAuth authentication required",
                                                                    "oauth_required": True,
                                                                    "message": "Please authenticate with Gmail first",
                                                                    "details": response_data.get("error", "")
                                                                }
                                                                logger.info(f"🔐 [MCP DEBUG] 7. OAuth required: {json.dumps(result, indent=2)}")
                                                                return result
                                                            
                                                            # Check if response contains OAuth URL
                                                            if "oauth_url" in response_data or "auth_url" in response_data:
                                                                result = {
                                                                    "oauth_required": True,
                                                                    "oauth_url": response_data.get("oauth_url") or response_data.get("auth_url"),
                                                                    "message": "Please click the link to authenticate with Gmail"
                                                                }
                                                                logger.info(f"🔐 [MCP DEBUG] 7. OAuth URL provided: {json.dumps(result, indent=2)}")
                                                                return result
                                                            
                                                            # Check for success with OAuth flow
                                                            if "success" in response_data and response_data.get("success"):
                                                                result = {
                                                                    "success": True,
                                                                    "message": response_data.get("message", "Operation completed successfully"),
                                                                    "data": response_data.get("data", {})
                                                                }
                                                                logger.info(f"✅ [MCP DEBUG] 7. Success response: {json.dumps(result, indent=2)}")
                                                                return result
                                                        
                                                        logger.info(f"📄 [MCP DEBUG] 7. Raw response data: {json.dumps(response_data, indent=2)}")
                                                        return response_data
                                                    except json.JSONDecodeError as e:
                                                        logger.error(f"Failed to parse SSE data: {e}")
                                                        return {"error": f"Failed to parse SSE response: {e}"}
                                            
                                            return {"error": "No valid data found in SSE response"}
                                        else:
                                            # Regular JSON response
                                            response_data = await pipedream_response.json()
                                            logger.info(f"Pipedream JSON response: {response_data}")
                                            return response_data
                                    else:
                                        error_text = await pipedream_response.text()
                                        logger.error(f"❌ [MCP DEBUG] 7. Pipedream HTTP error {pipedream_response.status}: {error_text}")
                                        result = {
                                            "error": f"Pipedream server returned HTTP {pipedream_response.status}",
                                            "details": error_text
                                        }
                                        logger.info(f"❌ [MCP DEBUG] 8. Final error result: {json.dumps(result, indent=2)}")
                                        return result
                                        
                            except asyncio.TimeoutError:
                                logger.error(f"⏰ [MCP DEBUG] 7. Pipedream request timed out")
                                result = {"error": "Request to Pipedream timed out"}
                                logger.info(f"⏰ [MCP DEBUG] 8. Final timeout result: {json.dumps(result, indent=2)}")
                                return result
                            except Exception as e:
                                logger.error(f"💥 [MCP DEBUG] 7. Pipedream request failed: {e}")
                                result = {"error": f"Pipedream request failed: {str(e)}"}
                                logger.info(f"💥 [MCP DEBUG] 8. Final exception result: {json.dumps(result, indent=2)}")
                                return result
                            
                except Exception as e:
                    logger.error(f"Failed to call tool via HTTP: {e}")
                    return {"error": f"HTTP tool call failed: {str(e)}"}
            
            return {"error": "Failed to call tool"}
            
        except Exception as e:
            logger.error(f"Failed to call tool {tool_name}: {e}")
            return {"error": f"Tool call failed: {str(e)}"}
    
    async def disconnect(self) -> None:
        """Disconnect from the MCP server"""
        try:
            if self.server_type == "stdio" and self.connection:
                self.connection.terminate()
                await self.connection.wait()
            elif self.server_type == "websocket" and self.connection:
                await self.connection.close()
            
            self.is_connected = False
            self.connection = None
            self.available_tools = []
            
        except Exception as e:
            logger.error(f"Failed to disconnect: {e}")

class MCPService:
    def __init__(self):
        self.clients: Dict[str, MCPClient] = {}
    
    async def connect_to_server(self, server_id: str, config: Dict[str, Any]) -> bool:
        """Connect to an MCP server and store the client"""
        try:
            client = MCPClient(config)
            success = await client.connect()
            
            if success:
                self.clients[server_id] = client
                logger.info(f"Connected to MCP server {server_id}")
                return True
            else:
                logger.error(f"Failed to connect to MCP server {server_id}: {client.last_error}")
                return False
                
        except Exception as e:
            logger.error(f"Error connecting to MCP server {server_id}: {e}")
            return False
    
    async def disconnect_from_server(self, server_id: str) -> None:
        """Disconnect from an MCP server"""
        if server_id in self.clients:
            await self.clients[server_id].disconnect()
            del self.clients[server_id]
            logger.info(f"Disconnected from MCP server {server_id}")
    
    def get_all_tools(self) -> List[Dict[str, Any]]:
        """Get all available tools from all connected servers"""
        all_tools = []
        for server_id, client in self.clients.items():
            for tool in client.available_tools:
                tool_with_server = tool.copy()
                tool_with_server["server_id"] = server_id
                tool_with_server["server_name"] = client.server_name
                all_tools.append(tool_with_server)
        return all_tools
    
    def get_openai_tools(self) -> List[Dict[str, Any]]:
        """Convert MCP tools to OpenAI function calling format"""
        openai_tools = []
        for server_id, client in self.clients.items():
            for tool in client.available_tools:
                # Convert MCP tool to OpenAI function format
                openai_tool = {
                    "type": "function",
                    "function": {
                        "name": tool.get("name", ""),
                        "description": tool.get("description", ""),
                        "parameters": tool.get("inputSchema", {})
                    }
                }
                openai_tools.append(openai_tool)
        return openai_tools
    
    def is_tool_available(self, tool_name: str) -> bool:
        """Check if a specific tool is available"""
        for client in self.clients.values():
            for tool in client.available_tools:
                if tool.get("name") == tool_name:
                    return True
        return False
    
    def get_tool_server_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get information about which server provides a specific tool"""
        for server_id, client in self.clients.items():
            for tool in client.available_tools:
                if tool.get("name") == tool_name:
                    return {
                        "server_id": server_id,
                        "server_name": client.server_name,
                        "server_type": client.server_type,
                        "tool_info": tool
                    }
        return None
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any], server_id: str = None, user_id: Optional[int] = None) -> Dict[str, Any]:
        """Call a tool, optionally specifying which server"""
        try:
            # If server_id is specified, use that server
            if server_id and server_id in self.clients:
                return await self.clients[server_id].call_tool(tool_name, arguments, user_id)
            
            # Otherwise, find the server that has this tool
            for client in self.clients.values():
                for tool in client.available_tools:
                    if tool.get("name") == tool_name:
                        return await client.call_tool(tool_name, arguments, user_id)
            
            # Tool not found in any connected server
            return {
                "error": f"Tool '{tool_name}' is not available. No MCP server provides this tool.",
                "error_type": "tool_not_available",
                "available_tools": [tool.get("name") for tool in self.get_all_tools()],
                "connected_servers": [client.server_name for client in self.clients.values()]
            }
            
        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {e}")
            return {"error": f"Tool call failed: {str(e)}"}
    
    def get_connected_servers(self) -> List[Dict[str, Any]]:
        """Get list of connected servers with their info"""
        servers = []
        for server_id, client in self.clients.items():
            servers.append({
                "id": server_id,
                "name": client.server_name,
                "type": client.server_type,
                "uri": client.uri,
                "is_connected": client.is_connected,
                "tool_count": len(client.available_tools),
                "last_error": client.last_error
            })
        return servers
    
    def generate_user_friendly_error_message(self, tool_name: str, error_result: Dict[str, Any]) -> str:
        """Generate user-friendly error messages for MCP tool failures"""
        
        # Check for OAuth authentication requirements
        if error_result.get("oauth_required"):
            oauth_url = error_result.get("oauth_url")
            if oauth_url:
                return f"🔐 **Gmail Authentication Required**\n\nTo use {tool_name}, you need to authenticate with Gmail first.\n\n**Please click this link to authorize access:**\n{oauth_url}\n\nOnce you've connected your Gmail account, you'll be able to use this feature."
            else:
                return f"🔐 **Gmail Authentication Required**\n\nTo use {tool_name}, you need to authenticate with Gmail first. Please check your Pipedream workflow configuration."
        
        # Check for success messages
        if error_result.get("success"):
            return error_result.get("message", f"✅ {tool_name} completed successfully!")
        
        error_type = error_result.get("error_type", "unknown")
        
        if error_type == "tool_not_available":
            guide = (
                "❌ The requested function is not available because the required MCP server isn't connected.\n\n"
                "How to fix this:\n"
                "1. Open Settings → MCP Servers\n"
                "2. Click Quick Add MCP and paste your Pipedream MCP URL (format: https://mcp.pipedream.net/[workflow-id]/[endpoint])\n"
                "3. Save and refresh servers/tools\n"
                "4. Re-run your request"
            )
            return guide
        
        elif error_type == "connection_error":
            server_name = error_result.get("server_name", "Unknown")
            last_error = error_result.get("last_error", "")
            return f"❌ MCP server '{server_name}' is not connected. Error: {last_error}"
        
        else:
            error_msg = error_result.get("error", "Unknown error")
            return f"❌ Failed to execute '{tool_name}': {error_msg}"

# Global MCP service instance
mcp_service = MCPService()

# Test mode function for direct MCP testing (as recommended by Pipedream)
async def test_mcp_call_directly(server_name: str, function_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Test MCP calls directly (as recommended by Pipedream)
    This function allows direct testing of MCP functionality without going through the AI layer
    """
    try:
        logger.info(f"🧪 [DIRECT TEST] Testing MCP call directly:")
        logger.info(f"   Server: {server_name}")
        logger.info(f"   Function: {function_name}")
        logger.info(f"   Params: {json.dumps(params, indent=2)}")
        
        # Find the server
        server_id = None
        for sid, client in mcp_service.clients.items():
            if client.server_name == server_name:
                server_id = sid
                break
        
        if not server_id:
            logger.error(f"❌ [DIRECT TEST] Server '{server_name}' not found")
            return {"error": f"Server '{server_name}' not found"}
        
        # Make the call
        result = await mcp_service.call_tool(function_name, params, server_id)
        
        logger.info(f"📄 [DIRECT TEST] Direct MCP test result: {json.dumps(result, indent=2)}")
        
        # Verify the action was actually completed
        if result.get("success"):
            logger.info(f"✅ [DIRECT TEST] Action reported success - verification passed")
        elif result.get("oauth_required"):
            logger.info(f"🔐 [DIRECT TEST] OAuth authentication required")
        else:
            logger.warning(f"⚠️ [DIRECT TEST] Action may not have completed successfully")
        
        return result
        
    except Exception as e:
        logger.error(f"💥 [DIRECT TEST] Direct MCP test failed: {e}")
        return {"error": f"Direct MCP test failed: {str(e)}"} 