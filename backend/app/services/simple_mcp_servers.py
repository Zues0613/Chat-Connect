"""
Simple MCP Servers for Testing ChatConnect Functionality

These are lightweight MCP servers that can be used to test the MCP host functionality
without the complexity of external services like Gmail or Pipedream.
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

logger = logging.getLogger(__name__)

class SimpleMCPServer:
    """Base class for simple MCP servers"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.available_tools = []
        self.is_connected = False
    
    async def initialize(self):
        """Initialize the server"""
        self.is_connected = True
        await self._discover_tools()
        logger.info(f"Initialized {self.name} MCP server")
    
    async def _discover_tools(self):
        """Discover available tools - to be implemented by subclasses"""
        pass
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool - to be implemented by subclasses"""
        pass
    
    def get_tools_list(self) -> Dict[str, Any]:
        """Get tools list in MCP format"""
        return {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "tools": self.available_tools
            }
        }

class CalculatorMCPServer(SimpleMCPServer):
    """Simple calculator MCP server for testing"""
    
    def __init__(self):
        super().__init__(
            name="Calculator",
            description="Simple calculator with basic arithmetic operations"
        )
    
    async def _discover_tools(self):
        """Discover calculator tools"""
        self.available_tools = [
            {
                "name": "calculator_add",
                "description": "Add two numbers together",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "a": {
                            "type": "number",
                            "description": "First number"
                        },
                        "b": {
                            "type": "number",
                            "description": "Second number"
                        }
                    },
                    "required": ["a", "b"]
                }
            },
            {
                "name": "calculator_multiply",
                "description": "Multiply two numbers",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "a": {
                            "type": "number",
                            "description": "First number"
                        },
                        "b": {
                            "type": "number",
                            "description": "Second number"
                        }
                    },
                    "required": ["a", "b"]
                }
            },
            {
                "name": "calculator_divide",
                "description": "Divide first number by second number",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "a": {
                            "type": "number",
                            "description": "Numerator"
                        },
                        "b": {
                            "type": "number",
                            "description": "Denominator"
                        }
                    },
                    "required": ["a", "b"]
                }
            }
        ]
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute calculator operations"""
        try:
            if tool_name == "calculator_add":
                result = arguments.get("a", 0) + arguments.get("b", 0)
                return {
                    "success": True,
                    "result": result,
                    "operation": "addition",
                    "a": arguments.get("a"),
                    "b": arguments.get("b")
                }
            
            elif tool_name == "calculator_multiply":
                result = arguments.get("a", 0) * arguments.get("b", 0)
                return {
                    "success": True,
                    "result": result,
                    "operation": "multiplication",
                    "a": arguments.get("a"),
                    "b": arguments.get("b")
                }
            
            elif tool_name == "calculator_divide":
                b = arguments.get("b", 0)
                if b == 0:
                    return {
                        "success": False,
                        "error": "Division by zero is not allowed"
                    }
                result = arguments.get("a", 0) / b
                return {
                    "success": True,
                    "result": result,
                    "operation": "division",
                    "a": arguments.get("a"),
                    "b": b
                }
            
            else:
                return {
                    "success": False,
                    "error": f"Unknown tool: {tool_name}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Calculator error: {str(e)}"
            }

class WeatherMCPServer(SimpleMCPServer):
    """Simple weather simulator MCP server for testing"""
    
    def __init__(self):
        super().__init__(
            name="Weather Simulator",
            description="Simulate weather data for testing purposes"
        )
    
    async def _discover_tools(self):
        """Discover weather tools"""
        self.available_tools = [
            {
                "name": "weather_get_current",
                "description": "Get current weather for a location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "City name or location"
                        }
                    },
                    "required": ["location"]
                }
            },
            {
                "name": "weather_get_forecast",
                "description": "Get 5-day weather forecast",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "City name or location"
                        },
                        "days": {
                            "type": "integer",
                            "description": "Number of days (1-7)",
                            "default": 5
                        }
                    },
                    "required": ["location"]
                }
            }
        ]
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute weather operations"""
        try:
            location = arguments.get("location", "Unknown")
            
            if tool_name == "weather_get_current":
                # Simulate current weather
                import random
                temperatures = [15, 18, 22, 25, 28, 30, 32, 35]
                conditions = ["Sunny", "Cloudy", "Partly Cloudy", "Rainy", "Windy"]
                
                return {
                    "success": True,
                    "location": location,
                    "temperature": random.choice(temperatures),
                    "condition": random.choice(conditions),
                    "humidity": random.randint(40, 80),
                    "timestamp": datetime.now().isoformat()
                }
            
            elif tool_name == "weather_get_forecast":
                days = min(arguments.get("days", 5), 7)
                
                # Simulate forecast
                import random
                forecast = []
                for i in range(days):
                    forecast.append({
                        "day": i + 1,
                        "date": (datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + 
                                timedelta(days=i)).isoformat(),
                        "high": random.randint(20, 35),
                        "low": random.randint(10, 25),
                        "condition": random.choice(["Sunny", "Cloudy", "Rainy", "Windy"])
                    })
                
                return {
                    "success": True,
                    "location": location,
                    "forecast": forecast,
                    "days": days
                }
            
            else:
                return {
                    "success": False,
                    "error": f"Unknown tool: {tool_name}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Weather error: {str(e)}"
            }

class FileOperationsMCPServer(SimpleMCPServer):
    """Simple file operations MCP server for testing"""
    
    def __init__(self):
        super().__init__(
            name="File Operations",
            description="Simple file operations for testing"
        )
        self.base_dir = os.path.join(os.getcwd(), "temp_files")
        os.makedirs(self.base_dir, exist_ok=True)
    
    async def _discover_tools(self):
        """Discover file operation tools"""
        self.available_tools = [
            {
                "name": "file_write",
                "description": "Write text to a file",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filename": {
                            "type": "string",
                            "description": "Name of the file to write"
                        },
                        "content": {
                            "type": "string",
                            "description": "Content to write to the file"
                        }
                    },
                    "required": ["filename", "content"]
                }
            },
            {
                "name": "file_read",
                "description": "Read content from a file",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filename": {
                            "type": "string",
                            "description": "Name of the file to read"
                        }
                    },
                    "required": ["filename"]
                }
            },
            {
                "name": "file_list",
                "description": "List all files in the temp directory",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            }
        ]
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute file operations"""
        try:
            if tool_name == "file_write":
                filename = arguments.get("filename", "")
                content = arguments.get("content", "")
                
                # Sanitize filename
                filename = "".join(c for c in filename if c.isalnum() or c in "._-")
                filepath = os.path.join(self.base_dir, filename)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                return {
                    "success": True,
                    "filename": filename,
                    "bytes_written": len(content),
                    "message": f"Successfully wrote {len(content)} characters to {filename}"
                }
            
            elif tool_name == "file_read":
                filename = arguments.get("filename", "")
                
                # Sanitize filename
                filename = "".join(c for c in filename if c.isalnum() or c in "._-")
                filepath = os.path.join(self.base_dir, filename)
                
                if not os.path.exists(filepath):
                    return {
                        "success": False,
                        "error": f"File {filename} not found"
                    }
                
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                return {
                    "success": True,
                    "filename": filename,
                    "content": content,
                    "bytes_read": len(content)
                }
            
            elif tool_name == "file_list":
                files = []
                for filename in os.listdir(self.base_dir):
                    filepath = os.path.join(self.base_dir, filename)
                    if os.path.isfile(filepath):
                        files.append({
                            "name": filename,
                            "size": os.path.getsize(filepath),
                            "modified": datetime.fromtimestamp(os.path.getmtime(filepath)).isoformat()
                        })
                
                return {
                    "success": True,
                    "files": files,
                    "count": len(files)
                }
            
            else:
                return {
                    "success": False,
                    "error": f"Unknown tool: {tool_name}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"File operation error: {str(e)}"
            }

# FastAPI app for serving MCP servers
app = FastAPI(title="Simple MCP Servers", version="1.0.0")

# Global server instances
calculator_server = CalculatorMCPServer()
weather_server = WeatherMCPServer()
file_server = FileOperationsMCPServer()

@app.on_event("startup")
async def startup_event():
    """Initialize all servers on startup"""
    await calculator_server.initialize()
    await weather_server.initialize()
    await file_server.initialize()

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Simple MCP Servers for Testing",
        "servers": [
            {"name": calculator_server.name, "description": calculator_server.description},
            {"name": weather_server.name, "description": weather_server.description},
            {"name": file_server.name, "description": file_server.description}
        ]
    }

@app.post("/calculator")
async def calculator_endpoint(request: Dict[str, Any]):
    """Calculator MCP server endpoint"""
    try:
        if request.get("method") == "tools/list":
            return calculator_server.get_tools_list()
        elif request.get("method") == "tools/call":
            params = request.get("params", {})
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            result = await calculator_server.call_tool(tool_name, arguments)
            return {
                "jsonrpc": "2.0",
                "id": request.get("id", 1),
                "result": result
            }
        else:
            return {"error": "Unknown method"}
    except Exception as e:
        return {"error": str(e)}

@app.post("/weather")
async def weather_endpoint(request: Dict[str, Any]):
    """Weather MCP server endpoint"""
    try:
        if request.get("method") == "tools/list":
            return weather_server.get_tools_list()
        elif request.get("method") == "tools/call":
            params = request.get("params", {})
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            result = await weather_server.call_tool(tool_name, arguments)
            return {
                "jsonrpc": "2.0",
                "id": request.get("id", 1),
                "result": result
            }
        else:
            return {"error": "Unknown method"}
    except Exception as e:
        return {"error": str(e)}

@app.post("/files")
async def files_endpoint(request: Dict[str, Any]):
    """File operations MCP server endpoint"""
    try:
        if request.get("method") == "tools/list":
            return file_server.get_tools_list()
        elif request.get("method") == "tools/call":
            params = request.get("params", {})
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            result = await file_server.call_tool(tool_name, arguments)
            return {
                "jsonrpc": "2.0",
                "id": request.get("id", 1),
                "result": result
            }
        else:
            return {"error": "Unknown method"}
    except Exception as e:
        return {"error": str(e)}

# Combined endpoint for all servers
@app.post("/mcp")
async def mcp_endpoint(request: Dict[str, Any]):
    """Combined MCP endpoint that routes to appropriate server"""
    try:
        method = request.get("method")
        
        if method == "tools/list":
            # Return tools from all servers
            all_tools = []
            all_tools.extend(calculator_server.available_tools)
            all_tools.extend(weather_server.available_tools)
            all_tools.extend(file_server.available_tools)
            
            return {
                "jsonrpc": "2.0",
                "id": request.get("id", 1),
                "result": {
                    "tools": all_tools
                }
            }
        
        elif method == "tools/call":
            params = request.get("params", {})
            tool_name = params.get("name", "")
            arguments = params.get("arguments", {})
            
            # Route to appropriate server based on tool name
            if tool_name.startswith("calculator_"):
                result = await calculator_server.call_tool(tool_name, arguments)
            elif tool_name.startswith("weather_"):
                result = await weather_server.call_tool(tool_name, arguments)
            elif tool_name.startswith("file_"):
                result = await file_server.call_tool(tool_name, arguments)
            else:
                result = {"success": False, "error": f"Unknown tool: {tool_name}"}
            
            return {
                "jsonrpc": "2.0",
                "id": request.get("id", 1),
                "result": result
            }
        
        else:
            return {"error": "Unknown method"}
            
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001) 