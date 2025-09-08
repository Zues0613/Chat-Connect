import asyncio
import json
import aiohttp
import websockets
import httpx
import time
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class MCPLogger:
    """Enhanced logging for MCP operations"""
    
    def __init__(self):
        self.log_file = f"mcp_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    def log_function_call(self, step: int, message: str, data: Dict[str, Any] = None):
        """Log function call steps"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "step": step,
            "message": message,
            "data": data
        }
        logger.info(f"MCP Function Call Step {step}: {message}")
        if data:
            logger.debug(f"Step {step} Data: {json.dumps(data, indent=2)}")
    
    def log_execution_result(self, success: bool, result: Dict[str, Any]):
        """Log execution results"""
        status = "SUCCESS" if success else "FAILURE"
        logger.info(f"MCP Execution {status}: {json.dumps(result, indent=2)}")
    
    def log_connection_attempt(self, server_name: str, uri: str, success: bool):
        """Log connection attempts"""
        status = "SUCCESS" if success else "FAILED"
        logger.info(f"MCP Connection {status}: {server_name} at {uri}")

class ValidationResult:
    """Result of function call validation"""
    def __init__(self, valid: bool, errors: List[str] = None):
        self.valid = valid
        self.errors = errors or []

class PipedreamHealthChecker:
    """Check Pipedream workflow health before executing"""
    
    def __init__(self):
        self.health_cache = {}
        self.cache_ttl = 300  # 5 minutes
    
    async def check_workflow_health(self, workflow_url: str) -> Dict:
        """Check if Pipedream workflow is healthy"""
        
        # Check cache first
        cache_key = f"health_{workflow_url}"
        if cache_key in self.health_cache:
            cached_result = self.health_cache[cache_key]
            if time.time() - cached_result["timestamp"] < self.cache_ttl:
                return cached_result["result"]
        
        try:
            # Send a simple health check request
            health_request = {
                "jsonrpc": "2.0",
                "id": "health_check",
                "method": "tools/list",
                "params": {}
            }
            
            # httpx requires either a default or all four params; set all explicitly
            timeout = httpx.Timeout(connect=10.0, read=30.0, write=30.0, pool=30.0)
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    workflow_url,
                    json=health_request,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    result = {
                        "healthy": True,
                        "response_time": response.elapsed.total_seconds(),
                        "message": "Workflow is responding normally"
                    }
                else:
                    result = {
                        "healthy": False,
                        "error": f"HTTP {response.status_code}",
                        "message": "Workflow returned error status"
                    }
                
                # Cache the result
                self.health_cache[cache_key] = {
                    "result": result,
                    "timestamp": time.time()
                }
                
                return result
                
        except httpx.TimeoutException:
            return {
                "healthy": False,
                "error": "Health check timeout",
                "message": "Workflow is not responding to health checks"
            }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "message": "Health check failed with exception"
            }

class EmailFallbackService:
    """Fallback email service when Pipedream fails"""
    
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
    
    async def send_email_fallback(self, to: str, subject: str, body: str) -> dict:
        """Send email using SMTP as fallback"""
        
        if not self.smtp_username or not self.smtp_password:
            return {
                "success": False,
                "error": "SMTP credentials not configured",
                "suggestion": "Configure SMTP_USERNAME and SMTP_PASSWORD in environment variables"
            }
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.smtp_username
            msg['To'] = to
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            text = msg.as_string()
            server.sendmail(self.smtp_username, to, text)
            server.quit()
            
            return {
                "success": True,
                "message_id": f"fallback_{int(time.time())}",
                "message": "Email sent successfully using fallback SMTP service"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"SMTP fallback failed: {str(e)}",
                "suggestion": "Check SMTP credentials and server settings"
            }

class MCPServiceDeepSeek:
    """Enhanced MCP Service for DeepSeek R1 Integration with Pipedream Timeout Fix"""
    
    def __init__(self):
        self.servers = {}
        self.tools_cache = {}
        self.logger = MCPLogger()
        self.session_endpoints = {}
        # Increased timeout values
        self.pipedream_timeout = int(os.getenv("PIPEDREAM_TIMEOUT", "90"))  # default 90s to avoid UI timeouts
        self.session_timeout = int(os.getenv("MCP_TIMEOUT", "120"))
        self.health_checker = PipedreamHealthChecker()
        self.email_fallback = EmailFallbackService()
    
    async def connect_to_server(self, server_id: str, config: Dict[str, Any]) -> bool:
        """Connect to an MCP server with enhanced logging"""
        try:
            server_name = config.get("name", "Unknown Server")
            uri = config.get("uri", "")
            
            self.logger.log_connection_attempt(server_name, uri, False)
            
            # Create MCP client
            client = MCPClientDeepSeek(config)
            success = await client.connect()
            
            if success:
                self.servers[server_id] = client
                self.logger.log_connection_attempt(server_name, uri, True)
                logger.info(f"Successfully connected to MCP server: {server_name}")
                return True
            else:
                logger.error(f"Failed to connect to MCP server: {server_name}")
                return False
                
        except Exception as e:
            logger.error(f"Error connecting to MCP server: {e}")
            return False
    
    async def discover_tools(self, message: str) -> List[Dict[str, Any]]:
        """Discover available tools from all connected servers"""
        all_tools = []
        
        for server_id, client in self.servers.items():
            try:
                tools = await client.discover_tools()
                for tool in tools:
                    tool['server_id'] = server_id
                    tool['server_name'] = client.server_name
                all_tools.extend(tools)
            except Exception as e:
                logger.error(f"Failed to discover tools from server {server_id}: {e}")
        
        return all_tools
    
    def validate_function_call(self, function_name: str, parameters: Dict[str, Any]) -> ValidationResult:
        """Validate function call parameters against schema"""
        errors = []
        
        # Find the tool definition
        tool_definition = None
        for server_id, client in self.servers.items():
            for tool in client.available_tools:
                if tool.get('name') == function_name:
                    tool_definition = tool
                    break
            if tool_definition:
                break
        
        if not tool_definition:
            return ValidationResult(False, [f"Function '{function_name}' not found"])
        
        # Validate required parameters
        required_params = tool_definition.get('parameters', {}).get('required', [])
        for param in required_params:
            if param not in parameters:
                errors.append(f"Required parameter '{param}' is missing")
        
        # Validate parameter types (basic validation)
        param_schema = tool_definition.get('parameters', {}).get('properties', {})
        for param_name, param_value in parameters.items():
            if param_name in param_schema:
                param_type = param_schema[param_name].get('type')
                if param_type == 'string' and not isinstance(param_value, str):
                    errors.append(f"Parameter '{param_name}' must be a string")
                elif param_type == 'integer' and not isinstance(param_value, int):
                    errors.append(f"Parameter '{param_name}' must be an integer")
                elif param_type == 'boolean' and not isinstance(param_value, bool):
                    errors.append(f"Parameter '{param_name}' must be a boolean")
        
        return ValidationResult(len(errors) == 0, errors)
    
    async def execute_tool_with_health_check(self, function_call) -> dict:
        """Execute tool with health check and optimization suggestions"""
        
        # Check if this is a Pipedream workflow
        if self._is_pipedream_workflow(function_call.name):
            workflow_url = self._get_workflow_url(function_call.name)
            
            # Health check first
            health_result = await self.health_checker.check_workflow_health(workflow_url)
            
            if not health_result.get("healthy"):
                # Don't block execution; warn and try anyway to mimic no-OAuth/no-gate flows
                logger.warning(f"Pipedream health check reported unhealthy: {health_result}")
            
            # If health check shows slow response, warn user
            if health_result.get("response_time", 0) > 10:
                logger.warning(f"⚠️ Pipedream workflow is slow (response time: {health_result['response_time']}s)")
        
        # Proceed with normal execution; if it fails, attach suggestions
        result = await self.execute_tool_with_confirmation(function_call)
        if not result.get("success") and self._is_pipedream_workflow(function_call.name):
            result.setdefault("suggestion", self._get_workflow_optimization_suggestions())
        return result
    
    def _is_pipedream_workflow(self, function_name: str) -> bool:
        """Check if function is a Pipedream workflow"""
        # Treat any mcp_* names or common providers as Pipedream-capable
        name_lower = function_name.lower()
        return (
            name_lower.startswith("mcp_")
            or "gmail" in name_lower
            or "google_drive" in name_lower
            or "drive" in name_lower
        )
    
    def _get_workflow_url(self, function_name: str) -> str:
        """Get workflow URL for a function"""
        # Find the server that has this tool
        for server_id, client in self.servers.items():
            if any(tool.get('name') == function_name for tool in client.available_tools):
                return client.uri
        return ""
    
    def _get_workflow_optimization_suggestions(self) -> str:
        """Get workflow optimization suggestions"""
        return """
🔧 Pipedream Workflow Optimization Suggestions:

1. **Check for Infinite Loops**: Ensure your workflow doesn't have loops that never terminate
2. **Reduce API Calls**: Minimize the number of external API calls in your workflow
3. **Add Timeouts**: Set appropriate timeouts for each step in your workflow
4. **Simplify Logic**: Remove unnecessary complex logic or data processing
5. **Check Gmail Authentication**: Ensure Gmail OAuth is properly configured
6. **Use Async Steps**: Use asynchronous steps where possible to improve performance

🔍 Debug Steps:
1. Go to your Pipedream dashboard
2. Find workflow ID: 6919d1b2-8143-422f-a5ae-6bca936cdbe6
3. Check the execution logs for stuck steps
4. Look for steps taking longer than 30 seconds
5. Optimize or remove slow steps

💡 Quick Fix: Create a simpler test workflow with just basic email sending to verify the integration works.
        """
    
    async def execute_tool_with_confirmation(self, function_call) -> Dict[str, Any]:
        """Execute tool and provide detailed feedback for DeepSeek R1"""
        
        self.logger.log_function_call(1, "DeepSeek R1 function call received", {
            "function": function_call.name,
            "parameters": function_call.parameters
        })
        
        try:
            # 1. Validate function call
            validation = self.validate_function_call(function_call.name, function_call.parameters)
            if not validation.valid:
                # If the function itself isn't found, guide user to add MCP server
                if any("not found" in e.lower() for e in validation.errors):
                    error_msg = f"Function '{function_call.name}' is not available on any connected MCP server"
                    suggestion = (
                        "To use this function, add the appropriate MCP server first.\n\n"
                        "Steps:\n"
                        "1. Open Settings → MCP Servers\n"
                        "2. Click Quick Add MCP and paste your Pipedream MCP URL (format: https://mcp.pipedream.net/[workflow-id]/[endpoint])\n"
                        "3. Save, then refresh servers and tools\n"
                        "4. Try your request again"
                    )
                    self.logger.log_execution_result(False, {"error": error_msg})
                    return {
                        "success": False,
                        "error": error_msg,
                        "error_type": "tool_not_available",
                        "suggestion": suggestion
                    }
                error_msg = f"Invalid parameters: {', '.join(validation.errors)}"
                self.logger.log_execution_result(False, {"error": error_msg})
                return {
                    "success": False,
                    "error": error_msg,
                    "suggestion": "Please check the required parameters and try again"
                }
            
            # 2. Execute the function
            # Prefer server that actually exposes this tool
            result = await self.execute_tool(function_call.name, function_call.parameters)
            
            # 3. Verify execution (DeepSeek R1 specific)
            verification = await self.verify_action_completed(function_call.name, result)
            
            self.logger.log_execution_result(True, result)
            
            return {
                "success": True,
                "result": result,
                "verification": verification,
                "message": f"Successfully executed {function_call.name}"
            }
            
        except Exception as e:
            error_result = {"error": str(e)}
            self.logger.log_execution_result(False, error_result)
            return {
                "success": False,
                "error": str(e),
                "suggestion": "Please try again or check your authentication"
            }
    
    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any], server_id: str = None) -> Dict[str, Any]:
        """Execute a tool with enhanced error handling"""
        
        self.logger.log_function_call(2, f"Executing tool: {tool_name}", {
            "tool_name": tool_name,
            "arguments": arguments,
            "server_id": server_id
        })
        
        try:
            # Normalize common aliases and arguments
            orig_name = tool_name
            tool_name = (tool_name or "").strip()
            normalized_args = arguments.copy() if arguments else {}
            alias_map = {
                "google_drive-create-document": "google_drive-create-file-from-text",
                "google_drive-create-doc": "google_drive-create-file-from-text",
                "create-google-doc": "google_drive-create-file-from-text",
            }
            if tool_name in alias_map:
                tool_name = alias_map[tool_name]
                # Map typical fields
                if "title" in normalized_args and "name" not in normalized_args:
                    normalized_args["name"] = normalized_args.pop("title")
                if "content" in normalized_args and "text" not in normalized_args:
                    normalized_args["text"] = normalized_args.pop("content")
                # Default to Google Docs mime type
                normalized_args.setdefault("mimeType", "application/vnd.google-apps.document")
                # Folder mapping
                if "folder" in normalized_args and "parents" not in normalized_args:
                    folder = normalized_args.pop("folder")
                    normalized_args["parents"] = [folder if isinstance(folder, str) else "root"]
                if "folder_id" in normalized_args and "parents" not in normalized_args:
                    folder_id = normalized_args.pop("folder_id")
                    normalized_args["parents"] = [folder_id]
                arguments = normalized_args

            # Find the server that has this tool
            target_server = None
            if server_id and server_id in self.servers:
                target_server = self.servers[server_id]
            else:
                for sid, server in self.servers.items():
                    if any(tool.get('name') == tool_name for tool in server.available_tools):
                        target_server = server
                        break
            
            if not target_server:
                error_msg = f"Tool '{orig_name}' not available on any connected server"
                self.logger.log_execution_result(False, {"error": error_msg})
                guide = (
                    "You need to add a compatible MCP server before using this function.\n\n"
                    "Steps:\n"
                    "1. Go to Settings → MCP Servers\n"
                    "2. Click Quick Add MCP and paste your Pipedream MCP URL for this capability\n"
                    "3. Save and refresh tools\n"
                    "4. Re-run your request"
                )
                return {"error": error_msg, "error_type": "tool_not_available", "suggestion": guide}
            
            # Execute the tool
            result = await target_server.call_tool(tool_name, arguments)
            
            self.logger.log_execution_result(True, result)
            return result
            
        except Exception as e:
            error_result = {"error": str(e)}
            self.logger.log_execution_result(False, error_result)
            return error_result
    
    async def verify_action_completed(self, function_name: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """Verify that the action was actually completed"""
        
        self.logger.log_function_call(3, f"Verifying action completion: {function_name}", {
            "function_name": function_name,
            "result": result
        })
        
        verification_methods = {
            "gmail-send-email": self._verify_email_sent,
            "mcp_Gmail_gmail-send-email": self._verify_email_sent,
            "slack-send-message": self._verify_slack_message,
            "github-create-issue": self._verify_github_issue
        }
        
        if function_name in verification_methods:
            verification_result = await verification_methods[function_name](result)
            self.logger.log_function_call(4, f"Verification result for {function_name}", verification_result)
            return verification_result
        
        # Default verification
        default_verification = {"verified": True, "method": "result_check"}
        self.logger.log_function_call(4, f"Default verification for {function_name}", default_verification)
        return default_verification
    
    async def _verify_email_sent(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Verify email was actually sent"""
        if "message_id" in result or "id" in result:
            return {
                "verified": True,
                "method": "message_id_check",
                "details": "Email has a valid message ID"
            }
        elif "success" in result and result.get("success"):
            return {
                "verified": True,
                "method": "success_flag",
                "details": "Email service reported success"
            }
        elif "oauth_required" in result:
            return {
                "verified": False,
                "method": "oauth_required",
                "details": "OAuth authentication required"
            }
        else:
            return {
                "verified": False,
                "method": "no_confirmation",
                "details": "No confirmation of email sending found"
            }
    
    async def _verify_slack_message(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Verify Slack message was sent"""
        if "ok" in result and result.get("ok"):
            return {
                "verified": True,
                "method": "slack_ok_flag",
                "details": "Slack API reported success"
            }
        return {"verified": False, "reason": "No success confirmation from Slack"}
    
    async def _verify_github_issue(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Verify GitHub issue was created"""
        if "number" in result or "id" in result:
            return {
                "verified": True,
                "method": "issue_number_check",
                "details": "GitHub issue has a valid number/ID"
            }
        return {"verified": False, "reason": "No issue number/ID found"}
    
    def get_all_tools(self) -> List[Dict[str, Any]]:
        """Get all available tools from all servers"""
        all_tools = []
        for server_id, client in self.servers.items():
            for tool in client.available_tools:
                tool_copy = tool.copy()
                tool_copy['server_id'] = server_id
                tool_copy['server_name'] = client.server_name
                all_tools.append(tool_copy)
        return all_tools
    
    def get_openai_tools(self) -> List[Dict[str, Any]]:
        """Get tools in OpenAI format for DeepSeek R1"""
        tools = []
        for server_id, client in self.servers.items():
            for tool in client.available_tools:
                # Fix common tool schemas for better compatibility
                tool_name = tool.get('name', '')
                tool_description = tool.get('description', '')
                tool_parameters = tool.get('parameters', {})
                
                # Fix specific tool schemas
                if tool_name == 'google_drive-list-files':
                    # Ensure the tool has the correct parameter schema
                    if not tool_parameters or 'properties' not in tool_parameters:
                        tool_parameters = {
                            "type": "object",
                            "properties": {
                                "instruction": {
                                    "type": "string",
                                    "description": "What files to list (e.g., 'List all files in root directory')"
                                },
                                "folder_id": {
                                    "type": "string",
                                    "description": "ID of the folder to list files from (default: 'root')"
                                }
                            },
                            "required": ["instruction"]
                        }
                    tool_description = "List files and folders from Google Drive. Use 'instruction' to specify what you want to list."
                
                elif tool_name == 'google_drive-find-file':
                    if not tool_parameters or 'properties' not in tool_parameters:
                        tool_parameters = {
                            "type": "object",
                            "properties": {
                                "instruction": {
                                    "type": "string",
                                    "description": "What file to find (e.g., 'Find documents with keyword X')"
                                }
                            },
                            "required": ["instruction"]
                        }
                    tool_description = "Find specific files in Google Drive based on your instruction."
                
                elif tool_name == 'google_drive-find-folder':
                    if not tool_parameters or 'properties' not in tool_parameters:
                        tool_parameters = {
                            "type": "object",
                            "properties": {
                                "instruction": {
                                    "type": "string",
                                    "description": "What folder to find (e.g., 'Find folder named X')"
                                }
                            },
                            "required": ["instruction"]
                        }
                    tool_description = "Find specific folders in Google Drive based on your instruction."
                
                openai_tool = {
                    "type": "function",
                    "function": {
                        "name": tool_name,
                        "description": tool_description,
                        "parameters": tool_parameters
                    }
                }
                tools.append(openai_tool)
                print(f"[DEBUG] Added tool: {tool_name} with parameters: {tool_parameters}")
        
        print(f"[DEBUG] Total tools returned: {len(tools)}")
        return tools
    
    def get_connected_servers(self) -> List[Dict[str, Any]]:
        """Get information about connected servers"""
        servers_info = []
        for server_id, client in self.servers.items():
            servers_info.append({
                "id": server_id,
                "name": client.server_name,
                "uri": client.uri,
                "connected": client.is_connected,
                "tools_count": len(client.available_tools)
            })
        return servers_info

class MCPClientDeepSeek:
    """Enhanced MCP Client for DeepSeek R1 Integration with Pipedream Timeout Fix"""
    
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
        self.session_endpoint = None
        # Increased timeout values
        self.pipedream_timeout = int(os.getenv("PIPEDREAM_TIMEOUT", "300"))  # 5 minutes
        self.session_timeout = int(os.getenv("MCP_TIMEOUT", "300"))  # 5 minutes
    
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
            logger.error(f"Failed to connect to MCP server {self.server_name}: {e}")
            return False
    
    async def _connect_custom(self) -> bool:
        """Connect to custom HTTP-based MCP server (e.g., Pipedream)"""
        try:
            async with aiohttp.ClientSession() as session:
                # Special handling for Pipedream servers: prefer JSON-RPC POST over GET/SSE
                if "pipedream.net" in self.uri:
                    logger.info(f"Establishing Pipedream MCP session: {self.uri}")
                    tools_request = {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "tools/list"
                    }
                    try:
                        timeout = aiohttp.ClientTimeout(total=10)
                        async with session.post(
                            self.uri,
                            json=tools_request,
                            headers={
                                "Content-Type": "application/json",
                                "Accept": "application/json, text/event-stream"
                            },
                            timeout=timeout
                        ) as response:
                            if response.status == 200:
                                content_type = response.headers.get('content-type', '')
                                if 'text/event-stream' in content_type:
                                    text = await response.text()
                                    for line in text.strip().split('\n'):
                                        if line.startswith('data: '):
                                            try:
                                                data_json = line[6:]
                                                data = json.loads(data_json)
                                                if "result" in data and "tools" in data["result"]:
                                                    self.available_tools = data["result"]["tools"]
                                                    break
                                            except Exception:
                                                continue
                                else:
                                    try:
                                        data = await response.json()
                                        if "result" in data and "tools" in data["result"]:
                                            self.available_tools = data["result"]["tools"]
                                    except Exception as e:
                                        logger.warning(f"Pipedream tools/list JSON parse failed: {e}")
                            else:
                                logger.warning(f"Pipedream tools/list returned HTTP {response.status}")
                    except Exception as e:
                        logger.warning(f"Pipedream initial tools/list check failed: {e}")
                    # Consider connected to allow later discovery and calls
                    self.is_connected = True
                    await self._discover_tools()
                    return True
                else:
                    # Standard HTTP connection: try GET /health then proceed
                    try:
                        timeout = aiohttp.ClientTimeout(total=5)
                        async with session.get(self.uri, timeout=timeout) as response:
                            if response.status in (200, 405):
                                self.is_connected = True
                                await self._discover_tools()
                                return True
                    except Exception:
                        pass
            
            self.last_error = "Failed to establish connection"
            return False
        except Exception as e:
            self.last_error = f"Custom connection error: {str(e)}"
            logger.error(f"Failed to connect via custom transport: {e}")
            return False
    
    async def _connect_stdio(self) -> bool:
        """Connect to stdio-based MCP server"""
        try:
            command_parts = self.uri.split()
            if not command_parts:
                self.last_error = "Invalid stdio command"
                return False
            
            self.connection = await asyncio.create_subprocess_exec(
                *command_parts,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            init_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "1.0.0",
                    "capabilities": {"tools": {}},
                    "clientInfo": {
                        "name": "chatconnect-deepseek",
                        "version": "1.0.0"
                    }
                }
            }
            
            init_message = json.dumps(init_request) + "\n"
            self.connection.stdin.write(init_message.encode())
            await self.connection.stdin.drain()
            
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
                async with session.get(self.uri) as response:
                    if response.status == 200:
                        self.is_connected = True
                        await self._discover_tools()
                        return True
            return False
        except Exception as e:
            self.last_error = f"SSE connection error: {str(e)}"
            logger.error(f"Failed to connect via SSE: {e}")
            return False
    
    async def _connect_websocket(self) -> bool:
        """Connect to WebSocket-based MCP server"""
        try:
            self.connection = await websockets.connect(self.uri)
            
            init_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "1.0.0",
                    "capabilities": {"tools": {}},
                    "clientInfo": {
                        "name": "chatconnect-deepseek",
                        "version": "1.0.0"
                    }
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
            self.last_error = f"WebSocket connection error: {str(e)}"
            logger.error(f"Failed to connect via WebSocket: {e}")
            return False
    
    async def _discover_tools(self) -> None:
        """Discover available tools from the server"""
        try:
            if self.server_type == "custom" and "pipedream.net" in self.uri:
                # Use session endpoint for Pipedream
                await self._discover_pipedream_tools()
            else:
                await self._discover_standard_tools()
        except Exception as e:
            logger.error(f"Failed to discover tools: {e}")
    
    async def _discover_pipedream_tools(self) -> None:
        """Discover tools from Pipedream server"""
        try:
            base_uri = self.uri.rstrip('/')
            # Prefer session endpoint when available; otherwise try base URI directly
            if self.session_endpoint:
                if self.session_endpoint.startswith('/'):
                    target_uri = base_uri + self.session_endpoint
                else:
                    target_uri = base_uri + '/' + self.session_endpoint
            else:
                logger.info("No session endpoint available for Pipedream, trying base URI for tools/list")
                target_uri = base_uri
            
            async with aiohttp.ClientSession() as session:
                
                tools_request = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/list"
                }
                
                # Increased timeout for tool discovery
                timeout = aiohttp.ClientTimeout(total=60)
                async with session.post(
                    target_uri,
                    json=tools_request,
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "application/json, text/event-stream"
                    },
                    timeout=timeout
                ) as response:
                    if response.status == 200:
                        content_type = response.headers.get('content-type', '')
                        if 'text/event-stream' in content_type:
                            response_text = await response.text()
                            lines = response_text.strip().split('\n')
                            for line in lines:
                                if line.startswith('data: '):
                                    try:
                                        data_json = line[6:]
                                        tools_data = json.loads(data_json)
                                        if "result" in tools_data and "tools" in tools_data["result"]:
                                            self.available_tools = tools_data["result"]["tools"]
                                            logger.info(f"Discovered {len(self.available_tools)} tools from Pipedream")
                                            print(f"[DEBUG] Pipedream tools discovered: {[t.get('name', 'unknown') for t in self.available_tools]}")
                                            
                                            # Debug the first tool to see its schema
                                            if self.available_tools:
                                                first_tool = self.available_tools[0]
                                                print(f"[DEBUG] First tool schema: {json.dumps(first_tool, indent=2)}")
                                            
                                            break
                                    except:
                                        continue
                        else:
                            # Handle regular JSON response
                            try:
                                tools_data = await response.json()
                                if "result" in tools_data and "tools" in tools_data["result"]:
                                    self.available_tools = tools_data["result"]["tools"]
                                    logger.info(f"Discovered {len(self.available_tools)} tools from Pipedream (JSON)")
                            except Exception as e:
                                logger.error(f"Failed to parse Pipedream JSON tools response: {e}")
        except Exception as e:
            logger.error(f"Failed to discover Pipedream tools: {e}")
    
    async def _discover_standard_tools(self) -> None:
        """Discover tools from standard MCP server"""
        try:
            if self.server_type == "stdio":
                tools_request = {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/list"
                }
                
                tools_message = json.dumps(tools_request) + "\n"
                self.connection.stdin.write(tools_message.encode())
                await self.connection.stdin.drain()
                
                response_line = await self.connection.stdout.readline()
                if response_line:
                    response = json.loads(response_line.decode().strip())
                    if "result" in response and "tools" in response["result"]:
                        self.available_tools = response["result"]["tools"]
            
            elif self.server_type == "websocket":
                tools_request = {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/list"
                }
                
                await self.connection.send(json.dumps(tools_request))
                response = await self.connection.recv()
                response_data = json.loads(response)
                
                if "result" in response_data and "tools" in response_data["result"]:
                    self.available_tools = response_data["result"]["tools"]
            
            logger.info(f"Discovered {len(self.available_tools)} tools from {self.server_name}")
            
        except Exception as e:
            logger.error(f"Failed to discover standard tools: {e}")
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool with enhanced error handling and logging"""
        try:
            logger.info(f"Calling tool {tool_name} on {self.server_name} with arguments: {arguments}")
            
            # Validate and enhance arguments for common tools
            enhanced_arguments = self._enhance_tool_arguments(tool_name, arguments)
            
            if self.server_type == "custom" and ("pipedream.net" in self.uri or "mcp.pipedream.net" in self.uri):
                return await self._call_pipedream_tool(tool_name, enhanced_arguments)
            elif self.server_type == "stdio":
                return await self._call_stdio_tool(tool_name, enhanced_arguments)
            elif self.server_type == "websocket":
                return await self._call_websocket_tool(tool_name, enhanced_arguments)
            else:
                return await self._call_http_tool(tool_name, enhanced_arguments)
                
        except Exception as e:
            logger.error(f"Failed to call tool {tool_name}: {e}")
            return {"error": f"Tool call failed: {str(e)}"}
    
    def _enhance_tool_arguments(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance tool arguments with defaults and validation for common tools"""
        enhanced = arguments.copy() if arguments else {}
        
        # Google Drive tools that commonly need instruction parameter
        drive_tools = [
            'google_drive-list-files',
            'google_drive-find-file',
            'google_drive-find-folder',
            'google_drive-search-shared-drives',
            'google_drive-list-access-proposals'
        ]
        
        # If it's a drive tool and no instruction provided, add a sensible default
        if tool_name in drive_tools and 'instruction' not in enhanced:
            if tool_name == 'google_drive-list-files':
                enhanced['instruction'] = "List all files in the root directory"
            elif tool_name == 'google_drive-find-file':
                enhanced['instruction'] = "Find files by name or type"
            elif tool_name == 'google_drive-find-folder':
                enhanced['instruction'] = "Find folders by name"
            elif tool_name == 'google_drive-search-shared-drives':
                enhanced['instruction'] = "List all shared drives"
            elif tool_name == 'google_drive-list-access-proposals':
                enhanced['instruction'] = "List pending access proposals"
        
        # Gmail tools that commonly need instruction parameter
        gmail_tools = [
            'gmail-send-email',
            'mcp_Gmail_gmail-send-email'
        ]
        
        if tool_name in gmail_tools and 'instruction' not in enhanced:
            enhanced['instruction'] = "Send an email with the specified content"
        
        # YouTube tools that commonly need instruction parameter
        youtube_tools = [
            'youtube-search',
            'youtube-get-video-info'
        ]
        
        if tool_name in youtube_tools and 'instruction' not in enhanced:
            enhanced['instruction'] = "Search for videos or get video information"
        
        logger.info(f"Enhanced arguments for {tool_name}: {enhanced}")
        return enhanced
    
    async def _call_pipedream_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call tool on Pipedream server with increased timeout"""
        try:
            async with aiohttp.ClientSession() as session:
                target_uri = self.uri
                if self.session_endpoint:
                    base_uri = self.uri.rstrip('/')
                    if self.session_endpoint.startswith('/'):
                        target_uri = base_uri + self.session_endpoint
                    else:
                        target_uri = base_uri + '/' + self.session_endpoint
                    logger.info(f"Using Pipedream session endpoint: {target_uri}")

                pipedream_request = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {
                        "name": tool_name,
                        "arguments": arguments
                    }
                }
                
                # Increased timeout configuration
                timeout = aiohttp.ClientTimeout(
                    connect=15.0,
                    sock_read=self.pipedream_timeout,
                    sock_connect=15.0
                )
                
                logger.info(f"📡 [MCP DEBUG] 5. Making HTTP request to Pipedream:")
                logger.info(f"   URL: {target_uri}")
                logger.info(f"   Timeout: {self.pipedream_timeout} seconds")
                
                async with session.post(
                    target_uri,
                    json=pipedream_request,
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "text/event-stream, application/json",
                        "User-Agent": "ChatConnect-DeepSeek-MCP-Client/1.0"
                    },
                    timeout=timeout
                ) as pipedream_response:
                    logger.info(f"📥 [MCP DEBUG] 6. Received Pipedream response:")
                    logger.info(f"   Status: {pipedream_response.status}")
                    logger.info(f"   Headers: {dict(pipedream_response.headers)}")
                    
                    if pipedream_response.status == 200:
                        content_type = pipedream_response.headers.get('content-type', '')
                        if 'text/event-stream' in content_type:
                            response_text = await pipedream_response.text()
                            lines = response_text.strip().split('\n')
                            for line in lines:
                                if line.startswith('data: '):
                                    data_json = line[6:]
                                    try:
                                        response_data = json.loads(data_json)
                                        
                                        # Check for Pipedream validation errors
                                        if isinstance(response_data, dict) and "result" in response_data:
                                            result = response_data["result"]
                                            if isinstance(result, dict) and "content" in result:
                                                content = result["content"]
                                                if isinstance(content, list) and len(content) > 0:
                                                    first_content = content[0]
                                                    if isinstance(first_content, dict) and "text" in first_content:
                                                        text = first_content["text"]
                                                        if "Error parsing arguments" in text:
                                                            # Extract the specific error details
                                                            error_msg = "The tool requires specific parameters that weren't provided."
                                                            suggestion = "Try rephrasing your request with more specific details."
                                                            
                                                            # Check if it's a missing instruction parameter
                                                            if "instruction" in text and "Required" in text:
                                                                error_msg = "The tool needs more specific instructions about what you want to do."
                                                                suggestion = "Instead of 'list files', try 'list all files in my Google Drive' or 'show me the files in the root folder'."
                                                            
                                                            return {
                                                                "error": error_msg,
                                                                "error_type": "parameter_validation",
                                                                "suggestion": suggestion,
                                                                "technical_details": text,
                                                                "enhanced_arguments": arguments
                                                            }
                                        
                                        # OAuth handling logic
                                        if isinstance(response_data, dict):
                                            if "error" in response_data and "oauth" in response_data["error"].lower():
                                                return {"error": "OAuth authentication required", "oauth_required": True, "message": "Please authenticate with Gmail first", "details": response_data.get("error", "")}
                                            if "oauth_url" in response_data or "auth_url" in response_data:
                                                return {"oauth_required": True, "oauth_url": response_data.get("oauth_url") or response_data.get("auth_url"), "message": "Please click the link to authenticate with Gmail"}
                                            if "success" in response_data and response_data.get("success"):
                                                return {"success": True, "message": response_data.get("message", "Operation completed successfully"), "data": response_data.get("data", {})}
                                        
                                        return response_data
                                    except json.JSONDecodeError as e:
                                        logger.error(f"Failed to parse Pipedream response JSON: {e}")
                                        return {"error": "Invalid response format from Pipedream", "raw_response": data_json}
                        else:
                            # Handle regular JSON response
                            try:
                                response_data = await pipedream_response.json()
                                
                                # Check for the same validation errors in JSON responses
                                if isinstance(response_data, dict) and "result" in response_data:
                                    result = response_data["result"]
                                    if isinstance(result, dict) and "content" in result:
                                        content = result["content"]
                                        if isinstance(content, list) and len(content) > 0:
                                            first_content = content[0]
                                            if isinstance(first_content, dict) and "text" in first_content:
                                                text = first_content["text"]
                                                if "Error parsing arguments" in text:
                                                    error_msg = "The tool requires specific parameters that weren't provided."
                                                    suggestion = "Try rephrasing your request with more specific details."
                                                    
                                                    if "instruction" in text and "Required" in text:
                                                        error_msg = "The tool needs more specific instructions about what you want to do."
                                                        suggestion = "Instead of 'list files', try 'list all files in my Google Drive' or 'show me the files in the root folder'."
                                                    
                                                    return {
                                                        "error": error_msg,
                                                        "error_type": "parameter_validation",
                                                        "suggestion": suggestion,
                                                        "technical_details": text,
                                                        "enhanced_arguments": arguments
                                                    }
                                
                                return response_data
                            except json.JSONDecodeError as e:
                                logger.error(f"Failed to parse Pipedream JSON response: {e}")
                                return {"error": "Invalid JSON response from Pipedream"}
                    else:
                        return {"error": f"HTTP {pipedream_response.status}: {await pipedream_response.text()}"}
                        
        except asyncio.TimeoutError:
            logger.error(f"⏰ [MCP DEBUG] 7. Pipedream request timed out after {self.pipedream_timeout} seconds")
            return {
                "error": f"Pipedream workflow is taking too long (timeout after {self.pipedream_timeout}s). Please check your workflow configuration.",
                "suggestion": "Try simplifying your Pipedream workflow or check for infinite loops.",
                "timeout_seconds": self.pipedream_timeout
            }
        except Exception as e:
            logger.error(f"Pipedream tool call failed: {e}")
            return {"error": f"Pipedream tool call failed: {str(e)}"}
    
    async def _call_stdio_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call tool on stdio-based server"""
        try:
            tool_request = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }
            
            tool_message = json.dumps(tool_request) + "\n"
            self.connection.stdin.write(tool_message.encode())
            await self.connection.stdin.drain()
            
            response_line = await self.connection.stdout.readline()
            if response_line:
                response = json.loads(response_line.decode().strip())
                if "result" in response:
                    return response["result"]
                elif "error" in response:
                    return {"error": response["error"]}
            
            return {"error": "No response from stdio server"}
            
        except Exception as e:
            return {"error": f"Stdio tool call failed: {str(e)}"}
    
    async def _call_websocket_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call tool on WebSocket-based server"""
        try:
            tool_request = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }
            
            await self.connection.send(json.dumps(tool_request))
            response = await self.connection.recv()
            response_data = json.loads(response)
            
            if "result" in response_data:
                return response_data["result"]
            elif "error" in response_data:
                return {"error": response_data["error"]}
            
            return {"error": "No response from WebSocket server"}
            
        except Exception as e:
            return {"error": f"WebSocket tool call failed: {str(e)}"}
    
    async def _call_http_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call tool on HTTP-based server"""
        try:
            async with aiohttp.ClientSession() as session:
                tool_request = {
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "tools/call",
                    "params": {
                        "name": tool_name,
                        "arguments": arguments
                    }
                }
                
                async with session.post(
                    self.uri,
                    json=tool_request,
                    headers={"Content-Type": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        response_data = await response.json()
                        if "result" in response_data:
                            return response_data["result"]
                        elif "error" in response_data:
                            return {"error": response_data["error"]}
                    else:
                        return {"error": f"HTTP {response.status}: {await response.text()}"}
            
            return {"error": "No response from HTTP server"}
            
        except Exception as e:
            return {"error": f"HTTP tool call failed: {str(e)}"}
    
    async def disconnect(self) -> None:
        """Disconnect from the server"""
        try:
            if self.connection:
                if self.server_type == "stdio":
                    self.connection.terminate()
                    await self.connection.wait()
                elif self.server_type == "websocket":
                    await self.connection.close()
            
            self.is_connected = False
            logger.info(f"Disconnected from MCP server: {self.server_name}")
            
        except Exception as e:
            logger.error(f"Error disconnecting from {self.server_name}: {e}")

# Global instance
mcp_service_deepseek = MCPServiceDeepSeek() 