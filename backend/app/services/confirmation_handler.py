#!/usr/bin/env python3
"""
Confirmation Handler Service for ChatConnect
Manages user confirmations for MCP server actions
"""

import json
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

@dataclass
class PendingConfirmation:
    """Represents a pending confirmation for MCP action"""
    confirmation_id: str
    user_id: int
    chat_id: int
    intent_type: str
    original_message: str
    mcp_servers: List[str]
    created_at: datetime
    expires_at: datetime
    confirmed: bool = False
    executed: bool = False

class ConfirmationHandler:
    """Handles user confirmations for MCP server actions"""
    
    def __init__(self):
        self.pending_confirmations: Dict[str, PendingConfirmation] = {}
        self.confirmation_timeout = timedelta(minutes=5)  # 5 minute timeout
    
    def create_confirmation(self, user_id: int, chat_id: int, intent_type: str, 
                          original_message: str, mcp_servers: List[str]) -> str:
        """
        Create a new confirmation request
        
        Returns:
            confirmation_id: Unique ID for the confirmation
        """
        import uuid
        
        confirmation_id = str(uuid.uuid4())
        now = datetime.now()
        
        confirmation = PendingConfirmation(
            confirmation_id=confirmation_id,
            user_id=user_id,
            chat_id=chat_id,
            intent_type=intent_type,
            original_message=original_message,
            mcp_servers=mcp_servers,
            created_at=now,
            expires_at=now + self.confirmation_timeout
        )
        
        self.pending_confirmations[confirmation_id] = confirmation
        
        # Clean up expired confirmations
        self._cleanup_expired()
        
        return confirmation_id
    
    def get_confirmation(self, confirmation_id: str) -> Optional[PendingConfirmation]:
        """Get a confirmation by ID"""
        self._cleanup_expired()
        return self.pending_confirmations.get(confirmation_id)
    
    def confirm_action(self, confirmation_id: str) -> Optional[PendingConfirmation]:
        """
        Mark a confirmation as confirmed
        
        Returns:
            PendingConfirmation if found and not expired, None otherwise
        """
        confirmation = self.get_confirmation(confirmation_id)
        if confirmation and not self._is_expired(confirmation):
            confirmation.confirmed = True
            return confirmation
        return None
    
    def execute_confirmed_action(self, confirmation_id: str) -> Optional[PendingConfirmation]:
        """
        Mark a confirmed action as executed
        
        Returns:
            PendingConfirmation if found and confirmed, None otherwise
        """
        confirmation = self.get_confirmation(confirmation_id)
        if confirmation and confirmation.confirmed and not self._is_expired(confirmation):
            confirmation.executed = True
            return confirmation
        return None
    
    def cancel_confirmation(self, confirmation_id: str) -> bool:
        """Cancel a confirmation"""
        if confirmation_id in self.pending_confirmations:
            del self.pending_confirmations[confirmation_id]
            return True
        return False
    
    def get_user_confirmations(self, user_id: int) -> List[PendingConfirmation]:
        """Get all confirmations for a user"""
        self._cleanup_expired()
        return [
            conf for conf in self.pending_confirmations.values()
            if conf.user_id == user_id
        ]
    
    def get_chat_confirmations(self, chat_id: int) -> List[PendingConfirmation]:
        """Get all confirmations for a chat"""
        self._cleanup_expired()
        return [
            conf for conf in self.pending_confirmations.values()
            if conf.chat_id == chat_id
        ]
    
    def _is_expired(self, confirmation: PendingConfirmation) -> bool:
        """Check if a confirmation has expired"""
        return datetime.now() > confirmation.expires_at
    
    def _cleanup_expired(self):
        """Remove expired confirmations"""
        expired_ids = [
            conf_id for conf_id, conf in self.pending_confirmations.items()
            if self._is_expired(conf)
        ]
        
        for conf_id in expired_ids:
            del self.pending_confirmations[conf_id]
    
    def generate_confirmation_message(self, confirmation: PendingConfirmation) -> str:
        """Generate a confirmation message with action buttons"""
        return f"""🔐 **Action Confirmation Required**

**Action:** {confirmation.intent_type.replace('_', ' ').title()}
**Message:** "{confirmation.original_message[:100]}{'...' if len(confirmation.original_message) > 100 else ''}"
**MCP Servers:** {', '.join(confirmation.mcp_servers)}

**Confirmation ID:** `{confirmation.confirmation_id}`

**To proceed, please respond with:**
- `confirm {confirmation.confirmation_id}` - to execute the action
- `cancel {confirmation.confirmation_id}` - to cancel the action

**⏰ This confirmation expires in 5 minutes.**"""
    
    def generate_execution_message(self, confirmation: PendingConfirmation) -> str:
        """Generate a message when action is being executed"""
        return f"""🚀 **Executing Action**

**Action:** {confirmation.intent_type.replace('_', ' ').title()}
**MCP Servers:** {', '.join(confirmation.mcp_servers)}

Processing your request... This may take a few moments."""
    
    def generate_cancellation_message(self, confirmation: PendingConfirmation) -> str:
        """Generate a message when action is cancelled"""
        return f"""❌ **Action Cancelled**

**Action:** {confirmation.intent_type.replace('_', ' ').title()}

The action has been cancelled. You can try again anytime."""
    
    def generate_expired_message(self, confirmation: PendingConfirmation) -> str:
        """Generate a message when confirmation has expired"""
        return f"""⏰ **Confirmation Expired**

**Action:** {confirmation.intent_type.replace('_', ' ').title()}

The confirmation has expired. Please make your request again to get a new confirmation."""

# Global instance
confirmation_handler = ConfirmationHandler() 