import openai
import asyncio
from typing import List, Dict, Any, Optional, AsyncGenerator
import json
import os
from dotenv import load_dotenv

load_dotenv()

class DeepSeekService:
    def __init__(self):
        self.api_key = None
        self.client = None
        self.conversation_history = []

    def initialize_with_api_key(self, api_key: str) -> bool:
        try:
            self.api_key = api_key
            # Use OpenRouter API instead of direct DeepSeek API
            self.client = openai.AsyncOpenAI(
                api_key=api_key,
                base_url="https://openrouter.ai/api/v1"
            )
            return True
        except Exception as e:
            print(f"[ERROR] Failed to initialize DeepSeek via OpenRouter: {e}")
            return False

    def start_chat_session(self, history: List[Dict[str, str]] = None) -> bool:
        """Initialize chat session with conversation history"""
        try:
            self.conversation_history = []
            
            if history:
                # Convert history to OpenAI format
                for msg in history:
                    if msg.get('role') in ['user', 'assistant']:
                        self.conversation_history.append({
                            'role': msg['role'],
                            'content': msg['content']
                        })
            
            return True
        except Exception as e:
            print(f"[ERROR] Failed to start chat session: {e}")
            return False

    async def send_message(self, message: str, tools: List[Dict] = None) -> Dict[str, Any]:
        """Send a message and get response"""
        try:
            if not self.client:
                raise Exception("Client not initialized")

            # Add user message to history
            self.conversation_history.append({
                'role': 'user',
                'content': message
            })

            # Prepare request parameters
            request_params = {
                'model': 'deepseek/deepseek-r1-0528',  # OpenRouter model name
                'messages': self.conversation_history,
                'max_tokens': 4000,
                'temperature': 0.7,
                'extra_headers': {
                    'HTTP-Referer': 'http://localhost:3000',  # Your site URL
                    'X-Title': 'VeeChat AI Assistant',  # Your site name
                }
            }

            # Add tools if provided
            if tools:
                request_params['tools'] = tools
                request_params['tool_choice'] = 'auto'

            # Send request
            response = await self.client.chat.completions.create(**request_params)
            
            # Extract response
            assistant_message = response.choices[0].message
            
            # Add assistant response to history
            self.conversation_history.append({
                'role': 'assistant',
                'content': assistant_message.content or ''
            })

            # Handle tool calls if any
            if assistant_message.tool_calls:
                return {
                    'type': 'tool_calls',
                    'tool_calls': assistant_message.tool_calls,
                    'content': assistant_message.content
                }
            
            return {
                'type': 'text',
                'content': assistant_message.content
            }

        except Exception as e:
            print(f"[ERROR] Failed to send message: {e}")
            raise Exception(f"Failed to get response: {e}")

    async def send_message_stream(self, message: str, tools: List[Dict] = None) -> AsyncGenerator[str, None]:
        """Send a message and get streaming response"""
        try:
            if not self.client:
                raise Exception("Client not initialized")

            # Add user message to history
            self.conversation_history.append({
                'role': 'user',
                'content': message
            })

            # Prepare request parameters
            request_params = {
                'model': 'deepseek/deepseek-r1-0528',  # OpenRouter model name
                'messages': self.conversation_history,
                'max_tokens': 4000,
                'temperature': 0.7,
                'stream': True,
                'extra_headers': {
                    'HTTP-Referer': 'http://localhost:3000',  # Your site URL
                    'X-Title': 'VeeChat AI Assistant',  # Your site name
                }
            }

            # Add tools if provided
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
            print(f"[ERROR] Failed to send streaming message: {e}")
            raise Exception(f"Failed to get streaming response: {e}")

    def send_function_result(self, function_name: str, function_result: Any) -> Dict[str, Any]:
        """Send function result back to the model"""
        try:
            if not self.client:
                raise Exception("Client not initialized")

            # Add function result to conversation
            self.conversation_history.append({
                'role': 'function',
                'name': function_name,
                'content': json.dumps(function_result)
            })

            return {
                'type': 'function_result',
                'function_name': function_name,
                'result': function_result
            }

        except Exception as e:
            print(f"[ERROR] Failed to send function result: {e}")
            raise Exception(f"Failed to send function result: {e}")

    def get_chat_history(self) -> List[Dict[str, str]]:
        """Get current conversation history"""
        return self.conversation_history.copy()

# Global instance
deepseek_service = DeepSeekService() 