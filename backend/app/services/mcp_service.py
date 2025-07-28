import asyncio
import json
import subprocess
import aiohttp
import websockets
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
import logging

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
            logger.error(f"Failed to connect to MCP server: {e}")
            return False
    
    async def _connect_stdio(self) -> bool:
        """Connect to stdio-based MCP server"""
        try:
            # Parse the command from URI
            command_parts = self.uri.split()
            if not command_parts:
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
            
            return False
        except Exception as e:
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
            return False
        except Exception as e:
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
            
            return False
        except Exception as e:
            logger.error(f"Failed to connect via WebSocket: {e}")
            return False
    
    async def _connect_custom(self) -> bool:
        """Connect to custom MCP server"""
        try:
            # For now, assume it's a simple HTTP endpoint
            parsed = urlparse(self.uri)
            if parsed.scheme in ['http', 'https']:
                async with aiohttp.ClientSession() as session:
                    async with session.get(self.uri + '/health') as response:
                        if response.status == 200:
                            self.is_connected = True
                            await self._discover_tools()
                            return True
            return False
        except Exception as e:
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
            
            logger.info(f"Discovered {len(self.available_tools)} tools")
            
        except Exception as e:
            logger.error(f"Failed to discover tools: {e}")
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a specific tool with given arguments"""
        try:
            if not self.is_connected:
                return {"error": "Not connected to MCP server"}
            
            call_request = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }
            
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
                logger.error(f"Failed to connect to MCP server {server_id}")
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
                all_tools.append(tool_with_server)
        return all_tools
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any], server_id: str = None) -> Dict[str, Any]:
        """Call a tool, optionally specifying which server"""
        try:
            # If server_id is specified, use that server
            if server_id and server_id in self.clients:
                return await self.clients[server_id].call_tool(tool_name, arguments)
            
            # Otherwise, find the server that has this tool
            for client in self.clients.values():
                for tool in client.available_tools:
                    if tool.get("name") == tool_name:
                        return await client.call_tool(tool_name, arguments)
            
            return {"error": f"Tool '{tool_name}' not found in any connected server"}
            
        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {e}")
            return {"error": f"Tool call failed: {str(e)}"}
    
    def get_connected_servers(self) -> List[Dict[str, Any]]:
        """Get list of connected servers with their info"""
        servers = []
        for server_id, client in self.clients.items():
            servers.append({
                "id": server_id,
                "type": client.server_type,
                "uri": client.uri,
                "is_connected": client.is_connected,
                "tool_count": len(client.available_tools)
            })
        return servers

# Global MCP service instance
mcp_service = MCPService() 