#!/usr/bin/env python3
"""
Intent Detection Service for ChatConnect
Detects when users want to perform actions and matches with MCP servers
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class IntentMatch:
    """Represents a detected intent and its MCP server match"""
    intent_type: str
    confidence: float
    description: str
    required_mcp_servers: List[str]
    available_mcp_servers: List[str]
    missing_servers: List[str]
    setup_guide: str
    confirmation_message: str

class IntentDetector:
    """Detects user intent and matches with available MCP servers"""
    
    def __init__(self):
        # Define intent patterns and their corresponding MCP servers
        self.intent_patterns = {
            "email": {
                "patterns": [
                    r"\b(send|write|compose|draft|reply to|forward)\s+(?:an?\s+)?(?:email|mail|message)\b",
                    r"\bemail\s+(?:to|for|about)\b",
                    r"\bgmail\b",
                    r"\boutlook\b",
                    r"\bcheck\s+(?:my\s+)?(?:emails?|mail|inbox)\b",
                    r"\bsearch\s+(?:my\s+)?(?:emails?|mail)\b"
                ],
                "mcp_servers": ["gmail", "outlook"],
                "description": "Email operations (send, read, search)",
                "setup_guide": "To use email features, you need to configure Gmail or Outlook MCP servers in your settings.",
                "confirmation_message": "I can help you with email operations. This will require access to your email account. Would you like me to proceed?"
            },
            "file_operations": {
                "patterns": [
                    r"\b(create|write|save|edit|modify|update)\s+(?:a\s+)?(?:file|document|text)\b",
                    r"\b(read|open|view|show|list)\s+(?:my\s+|the\s+)?(?:files?|documents?)\b",
                    r"\bsearch\s+(?:for\s+)?(?:files?|documents?)\b",
                    r"\b(delete|remove|trash)\s+(?:a\s+)?(?:file|document)\b",
                    r"\b(organize|sort|move)\s+(?:files?|documents?)\b",
                    r"\bgoogle\s+drive\b",
                    r"\b(list|show|view)\s+(?:my\s+)?google\s+drive\s+files\b"
                ],
                "mcp_servers": ["filesystem", "google_drive", "dropbox"],
                "description": "File and document operations",
                "setup_guide": "To use file operations, you need to configure Filesystem, Google Drive, or Dropbox MCP servers in your settings.",
                "confirmation_message": "I can help you with file operations. This will require access to your file system. Would you like me to proceed?"
            },
            "calendar": {
                "patterns": [
                    r"\b(create|schedule|book|set up)\s+(?:an?\s+)?(?:meeting|appointment|event)\b",
                    r"\b(check|view|show)\s+(?:my\s+)?(?:calendar|schedule)\b",
                    r"\b(remind|reminder)\b",
                    r"\b(google\s+)?calendar\b"
                ],
                "mcp_servers": ["google_calendar", "outlook_calendar"],
                "description": "Calendar and scheduling operations",
                "setup_guide": "To use calendar features, you need to configure Google Calendar or Outlook Calendar MCP servers in your settings.",
                "confirmation_message": "I can help you with calendar operations. This will require access to your calendar. Would you like me to proceed?"
            },
            "web_search": {
                "patterns": [
                    r"\b(search|find|look up)\s+(?:for\s+)?(?:information|data|news)\b",
                    r"\b(google(?!\s*drive)|bing|search\s+engine)\b",
                    r"\b(latest|current|recent)\s+(?:news|information)\b",
                    r"\b(weather|temperature)\s+(?:in|for)\b"
                ],
                "mcp_servers": ["web_search", "weather"],
                "description": "Web search and information retrieval",
                "setup_guide": "To use web search features, you need to configure Web Search or Weather MCP servers in your settings.",
                "confirmation_message": "I can help you search the web for information. Would you like me to proceed?"
            },
            "code_execution": {
                "patterns": [
                    r"\b(run|execute|test)\s+(?:this\s+)?(?:code|script|program)\b",
                    r"\b(debug|fix|test)\s+(?:my\s+)?(?:code|script)\b",
                    r"\b(terminal|command\s+line|shell)\b",
                    r"\b(install|setup|configure)\s+(?:package|dependency)\b"
                ],
                "mcp_servers": ["terminal", "code_executor"],
                "description": "Code execution and terminal operations",
                "setup_guide": "To use code execution features, you need to configure Terminal or Code Executor MCP servers in your settings.",
                "confirmation_message": "I can help you execute code or run terminal commands. This will run on your system. Would you like me to proceed?"
            },
            "database": {
                "patterns": [
                    r"\b(query|search|find)\s+(?:in\s+)?(?:database|db)\b",
                    r"\b(insert|add|create)\s+(?:record|entry|data)\b",
                    r"\b(update|modify|change)\s+(?:record|entry|data)\b",
                    r"\b(delete|remove)\s+(?:record|entry|data)\b"
                ],
                "mcp_servers": ["database", "sql"],
                "description": "Database operations",
                "setup_guide": "To use database features, you need to configure Database or SQL MCP servers in your settings.",
                "confirmation_message": "I can help you with database operations. This will require access to your database. Would you like me to proceed?"
            }
        }
    
    def detect_intent(self, message: str, available_mcp_servers: List[str]) -> Optional[IntentMatch]:
        """
        Detect user intent and match with available MCP servers
        
        Args:
            message: User's message
            available_mcp_servers: List of available MCP server names
            
        Returns:
            IntentMatch if intent detected, None otherwise
        """
        message_lower = message.lower()
        
        for intent_type, config in self.intent_patterns.items():
            # Check if any pattern matches
            for pattern in config["patterns"]:
                if re.search(pattern, message_lower, re.IGNORECASE):
                    # Calculate confidence based on pattern match
                    confidence = self._calculate_confidence(message_lower, pattern)
                    
                    if confidence > 0.3:  # Minimum confidence threshold
                        # Check MCP server availability
                        required_servers = config["mcp_servers"]
                        available_servers = [s for s in required_servers if s in available_mcp_servers]
                        missing_servers = [s for s in required_servers if s not in available_mcp_servers]
                        
                        return IntentMatch(
                            intent_type=intent_type,
                            confidence=confidence,
                            description=config["description"],
                            required_mcp_servers=required_servers,
                            available_mcp_servers=available_servers,
                            missing_servers=missing_servers,
                            setup_guide=config["setup_guide"],
                            confirmation_message=config["confirmation_message"]
                        )
        
        return None
    
    def _calculate_confidence(self, message: str, pattern: str) -> float:
        """Calculate confidence score for pattern match"""
        matches = re.findall(pattern, message, re.IGNORECASE)
        if not matches:
            return 0.0
        
        # Base confidence from pattern match
        confidence = 0.5
        
        # Boost confidence for exact matches
        if len(matches) > 0:
            confidence += 0.2
        
        # Boost confidence for longer, more specific patterns
        if len(pattern) > 20:
            confidence += 0.1
        
        # Boost confidence for action words
        action_words = ["send", "create", "search", "run", "execute", "check", "view"]
        if any(word in message for word in action_words):
            confidence += 0.2
        
        return min(confidence, 1.0)
    
    def generate_response(self, intent_match: IntentMatch) -> str:
        """Generate appropriate response based on intent match"""
        
        if not intent_match.available_mcp_servers:
            # No MCP servers available - provide setup guide
            return self._generate_setup_guide(intent_match)
        else:
            # MCP servers available - ask for confirmation
            return self._generate_confirmation_request(intent_match)
    
    def _generate_setup_guide(self, intent_match: IntentMatch) -> str:
        """Generate setup guide when MCP servers are not available"""
        return f"""🔧 **{intent_match.description.title()} Setup Required**

{intent_match.setup_guide}

**To get started:**
1. Go to Settings → MCP Servers
2. Add the required server(s): {', '.join(intent_match.required_mcp_servers)}
3. Configure your credentials
4. Try your request again

**Available servers for this action:**
{', '.join(intent_match.required_mcp_servers) if intent_match.required_mcp_servers else 'None configured'}

Would you like me to help you with something else, or would you prefer to set up the MCP servers first?"""
    
    def _generate_confirmation_request(self, intent_match: IntentMatch) -> str:
        """Generate confirmation request when MCP servers are available"""
        return f"""✅ **{intent_match.description.title()} Available**

{intent_match.confirmation_message}

**Available servers:** {', '.join(intent_match.available_mcp_servers)}

**What I can do:** {intent_match.description}

Please confirm if you'd like me to proceed with this action."""

# Global instance
intent_detector = IntentDetector() 