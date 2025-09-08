import google.generativeai as genai
import asyncio
from typing import List, Dict, Any, Optional, AsyncGenerator
import json
import os
from dotenv import load_dotenv

load_dotenv()

class GeminiService:
    def __init__(self):
        self.api_key = None
        self.model = None
        self.chat_session = None
    
    def initialize_with_api_key(self, api_key: str) -> bool:
        """Initialize Gemini with user's API key"""
        try:
            genai.configure(api_key=api_key)
            self.api_key = api_key
            
            # Initialize the model with function calling capabilities
            self.model = genai.GenerativeModel(
                model_name="gemini-1.5-pro",
                generation_config={
                    "temperature": 0.7,
                    "top_p": 0.8,
                    "top_k": 40,
                    "max_output_tokens": 4096,
                }
            )
            return True
        except Exception as e:
            print(f"[ERROR] Failed to initialize Gemini: {e}")
            return False
    
    def start_chat_session(self, history: List[Dict[str, str]] = None) -> bool:
        """Start a new chat session with optional history"""
        try:
            if not self.model:
                return False
            
            # Convert history to Gemini format if provided
            gemini_history = []
            if history:
                for msg in history:
                    role = "user" if msg["role"] == "user" else "model"
                    gemini_history.append({
                        "role": role,
                        "parts": [msg["content"]]
                    })
            
            self.chat_session = self.model.start_chat(history=gemini_history)
            return True
        except Exception as e:
            print(f"[ERROR] Failed to start chat session: {e}")
            return False
    
    async def send_message(self, message: str, tools: List[Dict] = None) -> Dict[str, Any]:
        """Send a message and get response from Gemini"""
        try:
            if not self.chat_session:
                return {"error": "Chat session not initialized"}
            
            # Send message to Gemini
            response = self.chat_session.send_message(message)
            
            # Check if Gemini wants to call a function/tool
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                    for part in candidate.content.parts:
                        if hasattr(part, 'function_call'):
                            # Gemini wants to call a function
                            function_call = part.function_call
                            return {
                                "type": "function_call",
                                "function_name": function_call.name,
                                "function_args": dict(function_call.args),
                                "message_id": getattr(response, 'message_id', None)
                            }
            
            # Regular text response
            response_text = response.text if hasattr(response, 'text') else str(response)
            return {
                "type": "text",
                "content": response_text,
                "message_id": getattr(response, 'message_id', None)
            }
            
        except Exception as e:
            print(f"[ERROR] Failed to send message to Gemini: {e}")
            return {"error": f"Failed to get response: {str(e)}"}
    
    async def send_message_stream(self, message: str, tools: List[Dict] = None) -> AsyncGenerator[str, None]:
        """Send a message and stream the response from Gemini"""
        try:
            if not self.chat_session:
                yield json.dumps({"error": "Chat session not initialized"})
                return
            
            # Use streaming response
            response = self.chat_session.send_message(message, stream=True)
            
            for chunk in response:
                if hasattr(chunk, 'text') and chunk.text:
                    yield json.dumps({
                        "type": "text_chunk",
                        "content": chunk.text
                    })
                    # Small delay to prevent overwhelming the client
                    await asyncio.sleep(0.01)
            
            # Send completion signal
            yield json.dumps({"type": "complete"})
            
        except Exception as e:
            print(f"[ERROR] Failed to stream message: {e}")
            yield json.dumps({"error": f"Failed to stream response: {str(e)}"})
    
    def send_function_result(self, function_name: str, function_result: Any) -> Dict[str, Any]:
        """Send function result back to Gemini"""
        try:
            if not self.chat_session:
                return {"error": "Chat session not initialized"}
            
            # Format function result for Gemini
            function_response = {
                "name": function_name,
                "response": function_result
            }
            
            # Send the function result back to continue the conversation
            response = self.chat_session.send_message(
                f"Function {function_name} returned: {json.dumps(function_result)}"
            )
            
            response_text = response.text if hasattr(response, 'text') else str(response)
            return {
                "type": "text",
                "content": response_text
            }
            
        except Exception as e:
            print(f"[ERROR] Failed to send function result: {e}")
            return {"error": f"Failed to process function result: {str(e)}"}
    
    def get_chat_history(self) -> List[Dict[str, str]]:
        """Get the current chat history"""
        try:
            if not self.chat_session or not hasattr(self.chat_session, 'history'):
                return []
            
            history = []
            for msg in self.chat_session.history:
                role = "user" if msg.role == "user" else "assistant"
                content = ""
                if hasattr(msg, 'parts'):
                    content = " ".join([part.text for part in msg.parts if hasattr(part, 'text')])
                elif hasattr(msg, 'text'):
                    content = msg.text
                
                if content:
                    history.append({
                        "role": role,
                        "content": content
                    })
            
            return history
        except Exception as e:
            print(f"[ERROR] Failed to get chat history: {e}")
            return []

# Global instance (will be initialized per request with user's API key)
gemini_service = GeminiService() 