#!/usr/bin/env python3
"""
DeepSeek R1 Service for ChatConnect

This service handles communication with DeepSeek R1 API, including:
- Reasoning extraction from <thinking> tags
- DeepSeek-specific function call parsing
- Optimized system prompts for DeepSeek R1
- Final response generation after tool execution
"""

import asyncio
import json
import logging
import os
import re
from datetime import datetime
from typing import AsyncGenerator, Dict, List, Optional, Any, Union
from dotenv import load_dotenv
import openai

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIResponse:
    """Represents an AI response with reasoning and function calls"""
    
    def __init__(self, content: str, reasoning: str = "", function_calls: List[Dict] = None):
        self.content = content
        self.reasoning = reasoning
        self.function_calls = function_calls or []
    
    def to_dict(self) -> Dict:
        return {
            "content": self.content,
            "reasoning": self.reasoning,
            "function_calls": self.function_calls
        }

class FunctionCall:
    """Represents a function call with parameters"""
    
    def __init__(self, name: str, arguments: Dict[str, Any]):
        self.name = name
        self.arguments = arguments
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "arguments": self.arguments
        }

class DeepSeekR1Service:
    """Service for interacting with DeepSeek R1 API"""
    
    def __init__(self):
        self.client = None
        self.model = None
        self.max_tokens = None
        self.temperature = None
        self.base_url = None
        self.api_key = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the OpenAI client for DeepSeek R1"""
        try:
            # Get API key - try DeepSeek first, then fallback to OpenRouter
            self.api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("DEFAULT_DEEPSEEK_API_KEY")
            if not self.api_key:
                raise ValueError("No DeepSeek API key found in environment variables")
            
            # Determine if using OpenRouter or direct DeepSeek API
            if self.api_key.startswith("sk-or-v1-"):
                # OpenRouter API
                self.base_url = "https://openrouter.ai/api/v1"
                self.model = os.getenv("DEEPSEEK_MODEL", "deepseek/deepseek-chat:6.7b")
                logger.info("Using OpenRouter API for DeepSeek R1")
            else:
                # Direct DeepSeek API
                self.base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
                self.model = os.getenv("DEEPSEEK_MODEL", "deepseek-reasoner")
                logger.info("Using direct DeepSeek API")
            
            self.max_tokens = int(os.getenv("DEEPSEEK_MAX_TOKENS", "4000"))
            self.temperature = float(os.getenv("DEEPSEEK_TEMPERATURE", "0.1"))
            
            # Initialize OpenAI client
            self.client = openai.AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
            
            logger.info(f"DeepSeek R1 service initialized with model: {self.model}")
            
        except Exception as e:
            logger.error(f"Failed to initialize DeepSeek R1 service: {e}")
            raise
    
    def initialize_with_api_key(self, api_key: str) -> bool:
        """Initialize with a specific API key"""
        try:
            self.api_key = api_key
            self._initialize_client()
            return True
        except Exception as e:
            logger.error(f"Failed to initialize DeepSeek R1 with API key: {e}")
            return False
    
    def start_chat_session(self, history: List[Dict[str, str]] = None) -> bool:
        """Initialize chat session with conversation history"""
        try:
            self.conversation_history = []
            
            if history:
                # Convert history to OpenAI format
                for msg in history:
                    if msg.get('role') in ['user', 'assistant', 'tool']:
                        self.conversation_history.append({
                            'role': msg['role'],
                            'content': msg['content']
                        })
            
            logger.info(f"Chat session started with {len(self.conversation_history)} messages")
            return True
        except Exception as e:
            logger.error(f"Failed to start chat session: {e}")
            return False
    
    async def process_message(self, message: str, available_tools: List[Dict] = None) -> AIResponse:
        """Process message with DeepSeek R1 reasoning capabilities"""
        
        if not self.client:
            raise Exception("DeepSeek R1 client not initialized")
        
        try:
            # 1. Create DeepSeek-optimized system prompt
            system_prompt = self._create_deepseek_system_prompt(available_tools)
            
            # 2. Format tools for DeepSeek R1
            tools = self._format_tools_for_deepseek(available_tools) if available_tools else None
            
            # 3. Add user message to history
            self.conversation_history.append({
                'role': 'user',
                'content': message
            })
            
            # 4. Generate response with reasoning
            request_params = {
                'model': self.model,
                'messages': [
                    {"role": "system", "content": system_prompt}
                ] + self.conversation_history,
                'max_tokens': self.max_tokens,
                'temperature': self.temperature
            }
            
            if tools:
                request_params['tools'] = tools
                request_params['tool_choice'] = 'auto'
            
            logger.info(f"Sending message to DeepSeek R1 with {len(tools) if tools else 0} tools")
            
            response = await self.client.chat.completions.create(**request_params)
            
            # 5. Parse DeepSeek R1 response
            ai_response = self._parse_deepseek_response(response)
            
            # 6. Add assistant response to history
            self.conversation_history.append({
                'role': 'assistant',
                'content': ai_response.content
            })
            
            logger.info(f"DeepSeek R1 response processed: {len(ai_response.function_calls)} function calls")
            return ai_response
            
        except Exception as e:
            logger.error(f"Failed to process message with DeepSeek R1: {e}")
            raise Exception(f"Failed to get response: {e}")
    
    def _create_deepseek_system_prompt(self, available_tools: List[Dict] = None) -> str:
        """Create system prompt optimized for DeepSeek R1"""
        
        tools_description = ""
        if available_tools:
            tools_description = "\n".join([
                f"- {tool['function']['name']}: {tool['function']['description']}\n  Parameters: {json.dumps(tool['function']['parameters'], indent=2)}"
                for tool in available_tools
            ])
        
        return f"""You are ChatConnect, an AI assistant powered by DeepSeek R1 that can execute real actions through function calls.

CRITICAL INSTRUCTIONS:
1. When users ask you to DO something, you must EXECUTE the action, not just describe it
2. Think through your approach first, then call the appropriate function
3. Always confirm when actions are completed successfully
4. If authentication is needed, guide users through the process
5. Be helpful, friendly, and professional

REASONING APPROACH:
1. First, think through what the user wants to accomplish
2. Identify which function(s) you need to call
3. Determine the correct parameters
4. Execute the function call
5. Confirm the action was completed

EXECUTION RULES:
- When users ask you to DO something, you must call the appropriate function
- Don't just describe what you would do - actually do it
- If you need authentication, tell the user and provide the auth link
- Always confirm when actions are completed successfully
- If something fails, explain what went wrong and suggest next steps

Available Functions:
{tools_description if tools_description else "No functions available"}

RESPONSE FORMAT:
- Think through your approach (you can show your reasoning)
- Call the function with correct parameters
- Provide a clear confirmation message

Remember: You have the power to actually perform actions, not just discuss them!"""
    
    def _format_tools_for_deepseek(self, available_tools: List[Dict]) -> List[Dict]:
        """Format tools for DeepSeek R1 function calling"""
        formatted_tools = []
        
        for tool in available_tools:
            formatted_tool = {
                "type": "function",
                "function": {
                    "name": tool['function']['name'],
                    "description": tool['function']['description'],
                    "parameters": tool['function']['parameters']
                }
            }
            formatted_tools.append(formatted_tool)
        
        return formatted_tools
    
    def _parse_deepseek_response(self, response) -> AIResponse:
        """Parse DeepSeek R1 response including reasoning"""
        message_content = response.choices[0].message.content or ""
        tool_calls = response.choices[0].message.tool_calls or []
        
        # Extract reasoning if present (DeepSeek R1 specific)
        reasoning = None
        clean_message = message_content
        
        if "<thinking>" in message_content and "</thinking>" in message_content:
            reasoning_start = message_content.find("<thinking>") + 10
            reasoning_end = message_content.find("</thinking>")
            reasoning = message_content[reasoning_start:reasoning_end].strip()
            clean_message = message_content[reasoning_end + 12:].strip()
        
        # Parse function calls
        function_calls = []
        for tool_call in tool_calls:
            try:
                parameters = json.loads(tool_call.function.arguments)
                function_calls.append(FunctionCall(
                    name=tool_call.function.name,
                    arguments=parameters
                ))
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse function arguments: {e}")
                continue
        
        return AIResponse(
            content=clean_message,
            reasoning=reasoning,
            function_calls=function_calls
        )
    
    async def generate_final_response(self, message: str, reasoning: str, execution_results: List[Dict]) -> str:
        """Generate final response after tool execution"""
        
        if not self.client:
            return message
        
        try:
            # Create a summary of execution results
            results_summary = []
            for i, result in enumerate(execution_results):
                if result.get("success"):
                    results_summary.append(f"✅ {result.get('message', 'Action completed successfully')}")
                else:
                    results_summary.append(f"❌ {result.get('error', 'Action failed')}")
            
            results_text = "\n".join(results_summary) if results_summary else "No actions were executed."
            
            # Add tool results to conversation
            for result in execution_results:
                self.conversation_history.append({
                    'role': 'tool',
                    'content': json.dumps(result)
                })
            
            # Generate final response
            final_prompt = f"""Based on the execution results, provide a clear and helpful response to the user.

Original message: {message}
Reasoning: {reasoning}
Execution results:
{results_text}

Provide a natural, helpful response that:
1. Confirms what was accomplished
2. Explains any issues that occurred
3. Offers next steps if needed
4. Maintains a friendly, professional tone"""

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are ChatConnect, a helpful AI assistant. Provide clear, friendly responses."},
                    {"role": "user", "content": final_prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            final_response = response.choices[0].message.content or message
            
            # Add final response to history
            self.conversation_history.append({
                'role': 'assistant',
                'content': final_response
            })
            
            return final_response
            
        except Exception as e:
            logger.error(f"Failed to generate final response: {e}")
            return message
    
    async def send_message_stream(self, message: str, available_tools: List[Dict] = None) -> AsyncGenerator[str, None]:
        """Send a message and get streaming response"""
        
        if not self.client:
            raise Exception("DeepSeek R1 client not initialized")
        
        try:
            # Add user message to history
            self.conversation_history.append({
                'role': 'user',
                'content': message
            })
            
            # Create system prompt and format tools
            system_prompt = self._create_deepseek_system_prompt(available_tools)
            tools = self._format_tools_for_deepseek(available_tools) if available_tools else None
            
            # Prepare request parameters
            request_params = {
                'model': self.model,
                'messages': [
                    {"role": "system", "content": system_prompt}
                ] + self.conversation_history,
                'max_tokens': self.max_tokens,
                'temperature': self.temperature,
                'stream': True
            }
            
            if tools:
                request_params['tools'] = tools
                request_params['tool_choice'] = 'auto'
            
            # Send streaming request
            stream = await self.client.chat.completions.create(**request_params)
            
            full_content = ""
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_content += content
                    yield content
            
            # Add assistant response to history
            if full_content:
                self.conversation_history.append({
                    'role': 'assistant',
                    'content': full_content
                })
            
        except Exception as e:
            logger.error(f"Failed to send streaming message: {e}")
            raise Exception(f"Failed to get streaming response: {e}")
    
    def get_chat_history(self) -> List[Dict[str, str]]:
        """Get current conversation history"""
        return self.conversation_history.copy()

# Global instance
deepseek_r1_service = DeepSeekR1Service() 