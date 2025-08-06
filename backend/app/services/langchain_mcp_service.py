import asyncio
import json
from typing import List, Dict, Any, Optional
from prisma import Prisma
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.prebuilt import create_react_agent
from langchain_core.runnables import RunnableConfig
import logging

logger = logging.getLogger(__name__)

class LangChainMCPService:
    def __init__(self):
        self.mcp_client = None
        self.agent = None
        self.model = None
        self.tools_config = {}
        self.is_initialized = False
        
    async def initialize_with_user_servers(self, user_id: int, google_api_key: str) -> bool:
        """Initialize MCP client with user's configured servers"""
        try:
            print(f"[DEBUG] Initializing LangChain MCP service for user {user_id}")
            
            # Get user's MCP servers from database
            prisma = Prisma()
            await prisma.connect()
            
            servers = await prisma.mcpserver.find_many(where={"userId": user_id})
            await prisma.disconnect()
            
            print(f"[DEBUG] Found {len(servers)} MCP servers for user {user_id}")
            
            if not servers:
                logger.info(f"No MCP servers found for user {user_id}")
                return False
            
            # Build tools configuration
            self.tools_config = {}
            for server in servers:
                config = server.config
                server_name = server.name.lower().replace(" ", "_")
                
                print(f"[DEBUG] Processing server: {server.name} with config: {config}")
                
                self.tools_config[server_name] = {
                    "url": config.get("uri", ""),
                    "transport": config.get("transport", "streamable_http")
                }
            
            print(f"[DEBUG] Built tools config: {self.tools_config}")
            logger.info(f"Initialized MCP tools config: {self.tools_config}")
            
            # Initialize MCP client
            print(f"[DEBUG] Creating MultiServerMCPClient with config: {self.tools_config}")
            self.mcp_client = MultiServerMCPClient(self.tools_config)
            
            # Get available tools
            print(f"[DEBUG] Getting available tools from MCP client")
            tools = await self.mcp_client.get_tools()
            print(f"[DEBUG] Available MCP tools: {[tool.name for tool in tools]}")
            logger.info(f"Available MCP tools: {[tool.name for tool in tools]}")
            
            # Initialize model
            print(f"[DEBUG] Initializing Gemini model")
            self.model = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash-exp",
                google_api_key=google_api_key
            )
            
            # Create agent with tools
            print(f"[DEBUG] Creating React agent with {len(tools)} tools")
            self.agent = create_react_agent(self.model, tools)
            
            self.is_initialized = True
            print(f"[DEBUG] LangChain MCP service initialization complete")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize LangChain MCP service: {e}")
            return False
    
    async def send_message(self, message: str, conversation_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """Send a message and get response using the agent with MCP tools"""
        try:
            print(f"[DEBUG] LangChain MCP send_message called with: {message[:100]}...")
            
            if not self.is_initialized or not self.agent:
                raise Exception("LangChain MCP service not initialized")
            
            # Convert conversation history to LangChain messages
            messages = []
            if conversation_history:
                print(f"[DEBUG] Converting {len(conversation_history)} history messages")
                for msg in conversation_history:
                    if msg.get('role') == 'user':
                        messages.append(HumanMessage(content=msg.get('content', '')))
                    elif msg.get('role') == 'assistant':
                        messages.append(AIMessage(content=msg.get('content', '')))
            
            # Add current user message
            messages.append(HumanMessage(content=message))
            print(f"[DEBUG] Total messages for agent: {len(messages)}")
            
            # Configure agent run
            config = RunnableConfig(recursion_limit=100)
            
            print(f"[DEBUG] Running agent with {len(messages)} messages")
            # Run the agent
            result = await self.agent.ainvoke(
                {"messages": messages},
                config=config
            )
            
            print(f"[DEBUG] Agent result: {result}")
            
            # Extract the final response
            final_message = result.get("messages", [])[-1] if result.get("messages") else None
            
            if final_message and hasattr(final_message, 'content'):
                print(f"[DEBUG] Final message content: {final_message.content[:200]}...")
                return {
                    'type': 'text',
                    'content': final_message.content
                }
            else:
                print(f"[DEBUG] No final message found in result")
                return {
                    'type': 'text',
                    'content': "I'm sorry, I couldn't generate a response."
                }
                
        except Exception as e:
            logger.error(f"Failed to send message with LangChain MCP: {e}")
            return {
                'type': 'error',
                'error': f"Failed to process message: {str(e)}"
            }
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools"""
        if not self.mcp_client:
            return []
        
        try:
            # This would need to be async, but for now return basic info
            tools_info = []
            for server_name, config in self.tools_config.items():
                tools_info.append({
                    "server": server_name,
                    "url": config.get("url", ""),
                    "transport": config.get("transport", "")
                })
            return tools_info
        except Exception as e:
            logger.error(f"Failed to get available tools: {e}")
            return []
    
    def is_ready(self) -> bool:
        """Check if the service is ready to use"""
        return self.is_initialized and self.agent is not None

# Global instance
langchain_mcp_service = LangChainMCPService() 