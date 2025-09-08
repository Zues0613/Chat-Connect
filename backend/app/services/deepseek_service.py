import openai
import asyncio
from typing import List, Dict, Any, Optional, AsyncGenerator
import json
import os
from dotenv import load_dotenv

load_dotenv()

class InsufficientCreditsError(Exception):
    """Raised when OpenRouter returns a 402 due to insufficient credits or too large max_tokens."""
    pass

class APITimeoutError(Exception):
    """Raised when the LLM call exceeds the configured timeout."""
    pass

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

    async def send_message(self, message: str, tools: List[Dict] = None, timeout_seconds: float = None) -> Dict[str, Any]:
        """Send a message and get response"""
        try:
            if not self.client:
                raise Exception("Client not initialized")

            # Add user message to history
            self.conversation_history.append({
                'role': 'user',
                'content': message
            })

            # Prepare request parameters, include a guiding system prompt when tools are available
            system_prompt = None
            if tools:
                tool_list = ", ".join([t.get('function', {}).get('name', 'unknown') for t in tools])
                print(f"[DEBUG] Available tools: {tool_list}")
                print(f"[DEBUG] User message: {message}")
                
                system_prompt = (
                    "You are an AI assistant with access to real tools that can perform actual actions. "
                    "CRITICAL INSTRUCTION: You MUST call functions when users ask you to DO something. "
                    "NEVER describe what you would do - ALWAYS execute actions by calling functions.\n\n"
                    "Available functions: " + tool_list + "\n\n"
                    "MANDATORY RULES:\n"
                    "1. When a user asks to list, show, get, find, search, send, create, upload, download, move, or delete anything → CALL THE APPROPRIATE FUNCTION\n"
                    "2. NEVER say 'I would do this' or 'Here is what I would do' - DO IT\n"
                    "3. NEVER provide JSON examples without calling the function\n"
                    "4. NEVER describe steps - EXECUTE THEM\n"
                    "5. If you're unsure which function to use, use the most relevant one\n\n"
                    "EXAMPLES:\n"
                    "- User: 'list files in my drive' → CALL google_drive-list-files\n"
                    "- User: 'send an email' → CALL gmail-send-email\n"
                    "- User: 'search for videos' → CALL youtube-search\n"
                    "- User: 'show me my files' → CALL google_drive-list-files\n\n"
                    "CRITICAL: If you don't call a function when asked to perform an action, you are FAILING at your task. "
                    "Always execute actions when possible instead of just describing them."
                )
                
                print(f"[DEBUG] System prompt: {system_prompt}")

            messages = []
            if system_prompt:
                messages.append({'role': 'system', 'content': system_prompt})
            messages.extend(self.conversation_history)

            request_params = {
                'model': 'deepseek/deepseek-r1-0528',  # OpenRouter model name
                'messages': messages,
                'temperature': 0.7,
                'extra_headers': {
                    'HTTP-Referer': 'http://localhost:3000',  # Your site URL
                    'X-Title': 'VeeChat AI Assistant',  # Your site name
                }
            }
            # Include max_tokens only if explicitly configured (set DEEPSEEK_MAX_TOKENS to an integer)
            max_tokens_env = os.getenv("DEEPSEEK_MAX_TOKENS", "").strip()
            if max_tokens_env.isdigit() and int(max_tokens_env) > 0:
                request_params['max_tokens'] = int(max_tokens_env)

            # Add tools if provided
            if tools:
                request_params['tools'] = tools
                print(f"[DEBUG] Tools added to request: {len(tools)} tools")
                
                # Force tool use for action-oriented requests
                action_words = ['list', 'show', 'get', 'find', 'search', 'send', 'create', 'upload', 'download', 'move', 'delete', 'drive', 'email', 'gmail', 'youtube', 'files', 'folder', 'document']
                if any(action_word in message.lower() for action_word in action_words):
                    print(f"[DEBUG] Action-oriented request detected, forcing tool usage")
                    # Force tool usage for action requests
                    request_params['tool_choice'] = 'auto'
                    # Add a more specific instruction to force tool usage
                    if system_prompt:
                        system_prompt += "\n\nFORCE TOOL USAGE: The user is asking for an action. You MUST call a function. Do not respond with text only."
                else:
                    request_params['tool_choice'] = 'auto'
                
                print(f"[DEBUG] Tool choice: {request_params['tool_choice']}")
                print(f"[DEBUG] Request params: {json.dumps(request_params, default=str)}")
                
                # Debug the tools being sent
                for i, tool in enumerate(tools):
                    print(f"[DEBUG] Tool {i}: {tool.get('function', {}).get('name', 'unknown')}")
                    print(f"[DEBUG] Tool {i} description: {tool.get('function', {}).get('description', 'no description')}")
                    print(f"[DEBUG] Tool {i} parameters: {tool.get('function', {}).get('parameters', {})}")

            # Send request with timeout
            try:
                effective_timeout = timeout_seconds if timeout_seconds is not None else float(os.getenv("OPENROUTER_TIMEOUT", "45"))
                print(f"[DEBUG] Sending request to OpenRouter with timeout: {effective_timeout}s")
                print(f"[DEBUG] Model: {request_params['model']}")
                print(f"[DEBUG] Messages count: {len(request_params['messages'])}")
                print(f"[DEBUG] Tools count: {len(request_params.get('tools', []))}")
                
                response = await asyncio.wait_for(
                    self.client.chat.completions.create(**request_params),
                    timeout=effective_timeout
                )
                print(f"[DEBUG] OpenRouter response received successfully")
            except asyncio.TimeoutError:
                raise APITimeoutError(f"Request to DeepSeek API timed out after {effective_timeout} seconds")
            
            # Extract response
            assistant_message = response.choices[0].message
            print(f"[DEBUG] AI Response: {assistant_message.content}")
            print(f"[DEBUG] Tool calls: {assistant_message.tool_calls}")
            
            # Add assistant response to history
            self.conversation_history.append({
                'role': 'assistant',
                'content': assistant_message.content or ''
            })

            # Handle tool calls if any
            if assistant_message.tool_calls:
                print(f"[DEBUG] Processing {len(assistant_message.tool_calls)} tool calls")
                return {
                    'type': 'tool_calls',
                    'tool_calls': assistant_message.tool_calls,
                    'content': assistant_message.content
                }
            else:
                print(f"[DEBUG] No tool calls in response")
                
                # If tools were available but not used for an action request, retry with stronger forcing
                if tools and any(action_word in message.lower() for action_word in ['list', 'show', 'get', 'find', 'search', 'send', 'create', 'upload', 'download', 'move', 'delete', 'drive', 'email', 'gmail', 'youtube', 'files', 'folder', 'document']):
                    print(f"[DEBUG] Tools available but not used for action request. Retrying with stronger forcing...")
                    
                    # Update system prompt to be more aggressive
                    retry_system_prompt = (
                        "CRITICAL: You MUST call a function now. The user asked for an action. "
                        "Do not respond with text. Do not describe what you would do. "
                        "CALL THE APPROPRIATE FUNCTION IMMEDIATELY.\n\n"
                        "Available functions: " + ", ".join([t.get('function', {}).get('name', 'unknown') for t in tools]) + "\n\n"
                        "User request: " + message + "\n\n"
                        "RESPOND WITH A FUNCTION CALL ONLY."
                    )
                    
                    # Retry with stronger forcing
                    retry_messages = [{'role': 'system', 'content': retry_system_prompt}]
                    retry_messages.extend(self.conversation_history[-2:])  # Just the last exchange
                    
                    retry_params = request_params.copy()
                    retry_params['messages'] = retry_messages
                    retry_params['tool_choice'] = 'auto'
                    
                    try:
                        print(f"[DEBUG] Retrying with stronger tool forcing...")
                        retry_response = await asyncio.wait_for(
                            self.client.chat.completions.create(**retry_params),
                            timeout=effective_timeout
                        )
                        
                        retry_assistant_message = retry_response.choices[0].message
                        print(f"[DEBUG] Retry response: {retry_assistant_message.content}")
                        print(f"[DEBUG] Retry tool calls: {retry_assistant_message.tool_calls}")
                        
                        if retry_assistant_message.tool_calls:
                            print(f"[DEBUG] Retry successful - got tool calls")
                            return {
                                'type': 'tool_calls',
                                'tool_calls': retry_assistant_message.tool_calls,
                                'content': retry_assistant_message.content
                            }
                    except Exception as retry_error:
                        print(f"[DEBUG] Retry failed: {retry_error}")
            
            return {
                'type': 'text',
                'content': assistant_message.content
            }

        except Exception as e:
            err_text = str(e)
            print(f"[ERROR] Failed to send message: {err_text}")
            # Detect OpenRouter 402 insufficient credits / token budget errors
            if (
                " 402" in err_text
                or "Error code: 402" in err_text
                or "requires more credits" in err_text
                or "more credits" in err_text
            ):
                # Try a dynamic fallback: retry once without max_tokens to let provider budget dynamically
                try:
                    # Remove explicit max_tokens and retry quickly
                    print("[INFO] Retrying without explicit max_tokens after 402 error")
                    # Rebuild request without max_tokens
                    messages = self.conversation_history
                    response = await self.client.chat.completions.create(
                        model='deepseek/deepseek-r1-0528',
                        messages=messages,
                        temperature=0.7,
                        extra_headers={
                            'HTTP-Referer': 'http://localhost:3000',
                            'X-Title': 'VeeChat AI Assistant',
                        }
                    )
                    assistant_message = response.choices[0].message
                    self.conversation_history.append({
                        'role': 'assistant',
                        'content': assistant_message.content or ''
                    })
                    return {
                        'type': 'text',
                        'content': assistant_message.content
                    }
                except Exception as retry_err:
                    print(f"[INFO] Retry without max_tokens failed: {retry_err}")
                    raise InsufficientCreditsError(
                        "This request requires more credits, or fewer max_tokens. Reduce tokens or add credits at https://openrouter.ai/settings/credits."
                    )
            raise Exception(f"Failed to get response: {err_text}")

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
                'temperature': 0.7,
                'stream': True,
                'extra_headers': {
                    'HTTP-Referer': 'http://localhost:3000',  # Your site URL
                    'X-Title': 'VeeChat AI Assistant',  # Your site name
                }
            }
            max_tokens_env = os.getenv("DEEPSEEK_MAX_TOKENS", "").strip()
            if max_tokens_env.isdigit() and int(max_tokens_env) > 0:
                request_params['max_tokens'] = int(max_tokens_env)

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
            err_text = str(e)
            print(f"[ERROR] Failed to send streaming message: {err_text}")
            if (
                " 402" in err_text
                or "Error code: 402" in err_text
                or "requires more credits" in err_text
                or "more credits" in err_text
            ):
                raise InsufficientCreditsError(
                    "This request requires more credits, or fewer max_tokens. Reduce tokens or add credits at https://openrouter.ai/settings/credits."
                )
            if "timed out" in err_text.lower():
                raise APITimeoutError("Streaming response timed out")
            raise Exception(f"Failed to get streaming response: {err_text}")

    async def send_tool_results(self, tool_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Send tool results back to the model"""
        try:
            if not self.client:
                raise Exception("Client not initialized")

            # Add tool results to conversation
            for tool_result in tool_results:
                self.conversation_history.append({
                    'role': 'tool',
                    'tool_call_id': tool_result['tool_call_id'],
                    'content': json.dumps(tool_result['result'])
                })

            # Send another request to get the final response
            params = {
                'model': 'deepseek/deepseek-r1-0528',
                'messages': self.conversation_history,
                'temperature': 0.7,
                'extra_headers': {
                    'HTTP-Referer': 'http://localhost:3000',
                    'X-Title': 'VeeChat AI Assistant',
                }
            }
            max_tokens_env = os.getenv("DEEPSEEK_MAX_TOKENS", "").strip()
            if max_tokens_env.isdigit() and int(max_tokens_env) > 0:
                params['max_tokens'] = int(max_tokens_env)
            response = await self.client.chat.completions.create(**params)

            assistant_message = response.choices[0].message
            
            # Add assistant response to history
            self.conversation_history.append({
                'role': 'assistant',
                'content': assistant_message.content or ''
            })

            return {
                'content': assistant_message.content,
                'type': 'text'
            }

        except Exception as e:
            print(f"[ERROR] Failed to send tool results: {e}")
            return {
                'error': f"Failed to process tool results: {e}",
                'type': 'error'
            }

    async def send_function_result(self, function_name: str, function_result: Any) -> Dict[str, Any]:
        """Send function result back to the model (legacy method)"""
        return await self.send_tool_results([{
            "tool_call_id": "call_1",
            "name": function_name,
            "result": function_result
        }])

    def get_chat_history(self) -> List[Dict[str, str]]:
        """Get current conversation history"""
        return self.conversation_history.copy()

# Global instance
deepseek_service = DeepSeekService() 