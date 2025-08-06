import os
import secrets
import json
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from urllib.parse import urlencode, parse_qs, urlparse
from prisma import Prisma
import logging

logger = logging.getLogger(__name__)

class OAuthService:
    def __init__(self):
        self.prisma = Prisma()
        self.oauth_configs = {
            "gmail": {
                "client_id": os.getenv("GOOGLE_CLIENT_ID"),
                "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
                "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
                "token_url": "https://oauth2.googleapis.com/token",
                "scope": "https://www.googleapis.com/auth/gmail.send https://www.googleapis.com/auth/gmail.readonly",
                "redirect_uri": os.getenv("OAUTH_REDIRECT_URI", "http://localhost:3000/oauth/callback")
            },
            "google": {
                "client_id": os.getenv("GOOGLE_CLIENT_ID"),
                "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
                "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
                "token_url": "https://oauth2.googleapis.com/token",
                "scope": "openid email profile",
                "redirect_uri": os.getenv("OAUTH_REDIRECT_URI", "http://localhost:3000/oauth/callback")
            }
        }
    
    async def connect(self):
        """Connect to the database"""
        await self.prisma.connect()
    
    async def disconnect(self):
        """Disconnect from the database"""
        await self.prisma.disconnect()
    
    def generate_oauth_state(self) -> str:
        """Generate a secure OAuth state parameter"""
        return secrets.token_urlsafe(32)
    
    async def create_oauth_state(self, user_id: int, server_id: int, provider: str, redirect_uri: str) -> str:
        """Create an OAuth state record for tracking the flow"""
        state = self.generate_oauth_state()
        expires_at = datetime.utcnow() + timedelta(minutes=10)  # 10 minute expiry
        
        await self.prisma.oauthstate.create(
            data={
                "userId": user_id,
                "serverId": server_id,
                "state": state,
                "provider": provider,
                "redirectUri": redirect_uri,
                "expiresAt": expires_at
            }
        )
        
        return state
    
    async def validate_oauth_state(self, state: str) -> Optional[Dict[str, Any]]:
        """Validate and retrieve OAuth state"""
        oauth_state = await self.prisma.oauthstate.find_unique(
            where={"state": state},
            include={
                "user": True,
                "server": True
            }
        )
        
        if not oauth_state:
            return None
        
        if oauth_state.expiresAt < datetime.utcnow():
            # Clean up expired state
            await self.prisma.oauthstate.delete(where={"id": oauth_state.id})
            return None
        
        return {
            "id": oauth_state.id,
            "userId": oauth_state.userId,
            "serverId": oauth_state.serverId,
            "provider": oauth_state.provider,
            "redirectUri": oauth_state.redirectUri,
            "user": oauth_state.user,
            "server": oauth_state.server
        }
    
    async def cleanup_oauth_state(self, state_id: str):
        """Clean up OAuth state after use"""
        try:
            await self.prisma.oauthstate.delete(where={"id": state_id})
        except Exception as e:
            logger.error(f"Failed to cleanup OAuth state: {e}")
    
    def generate_oauth_url(self, provider: str, state: str, additional_scopes: str = "") -> Optional[str]:
        """Generate OAuth authorization URL"""
        config = self.oauth_configs.get(provider)
        if not config:
            logger.error(f"OAuth provider '{provider}' not configured")
            return None
        
        # Combine default scope with additional scopes
        scope = config["scope"]
        if additional_scopes:
            scope = f"{scope} {additional_scopes}"
        
        params = {
            "client_id": config["client_id"],
            "redirect_uri": config["redirect_uri"],
            "response_type": "code",
            "scope": scope,
            "state": state,
            "access_type": "offline",  # Get refresh token
            "prompt": "consent"  # Always show consent screen
        }
        
        auth_url = f"{config['auth_url']}?{urlencode(params)}"
        return auth_url
    
    async def exchange_code_for_tokens(self, provider: str, code: str) -> Optional[Dict[str, Any]]:
        """Exchange authorization code for access and refresh tokens"""
        config = self.oauth_configs.get(provider)
        if not config:
            logger.error(f"OAuth provider '{provider}' not configured")
            return None
        
        token_data = {
            "client_id": config["client_id"],
            "client_secret": config["client_secret"],
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": config["redirect_uri"]
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    config["token_url"],
                    data=token_data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                ) as response:
                    if response.status == 200:
                        token_response = await response.json()
                        
                        # Calculate expiry time
                        expires_at = None
                        if "expires_in" in token_response:
                            expires_at = datetime.utcnow() + timedelta(seconds=token_response["expires_in"])
                        
                        return {
                            "access_token": token_response.get("access_token"),
                            "refresh_token": token_response.get("refresh_token"),
                            "token_type": token_response.get("token_type", "Bearer"),
                            "expires_at": expires_at,
                            "scope": token_response.get("scope")
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"Token exchange failed: {response.status} - {error_text}")
                        return None
        except Exception as e:
            logger.error(f"Token exchange error: {e}")
            return None
    
    async def store_oauth_tokens(self, user_id: int, server_id: int, provider: str, tokens: Dict[str, Any]):
        """Store OAuth tokens in the database"""
        try:
            # Upsert tokens (update if exists, create if not)
            await self.prisma.oauthtoken.upsert(
                where={
                    "userId_serverId_provider": {
                        "userId": user_id,
                        "serverId": server_id,
                        "provider": provider
                    }
                },
                update={
                    "accessToken": tokens["access_token"],
                    "refreshToken": tokens.get("refresh_token"),
                    "tokenType": tokens.get("token_type", "Bearer"),
                    "expiresAt": tokens.get("expires_at"),
                    "scope": tokens.get("scope"),
                    "updatedAt": datetime.utcnow()
                },
                create={
                    "userId": user_id,
                    "serverId": server_id,
                    "provider": provider,
                    "accessToken": tokens["access_token"],
                    "refreshToken": tokens.get("refresh_token"),
                    "tokenType": tokens.get("token_type", "Bearer"),
                    "expiresAt": tokens.get("expires_at"),
                    "scope": tokens.get("scope")
                }
            )
            logger.info(f"Stored OAuth tokens for user {user_id}, server {server_id}, provider {provider}")
        except Exception as e:
            logger.error(f"Failed to store OAuth tokens: {e}")
            raise
    
    async def get_oauth_tokens(self, user_id: int, server_id: int, provider: str) -> Optional[Dict[str, Any]]:
        """Retrieve OAuth tokens for a user/server/provider combination"""
        try:
            token = await self.prisma.oauthtoken.find_unique(
                where={
                    "userId_serverId_provider": {
                        "userId": user_id,
                        "serverId": server_id,
                        "provider": provider
                    }
                }
            )
            
            if not token:
                return None
            
            # Check if token is expired
            if token.expiresAt and token.expiresAt < datetime.utcnow():
                # Try to refresh the token
                if token.refreshToken:
                    refreshed = await self.refresh_oauth_tokens(user_id, server_id, provider, token.refreshToken)
                    if refreshed:
                        return refreshed
                    else:
                        # Delete expired token
                        await self.prisma.oauthtoken.delete(where={"id": token.id})
                        return None
                else:
                    # Delete expired token
                    await self.prisma.oauthtoken.delete(where={"id": token.id})
                    return None
            
            return {
                "access_token": token.accessToken,
                "refresh_token": token.refreshToken,
                "token_type": token.tokenType,
                "expires_at": token.expiresAt,
                "scope": token.scope
            }
        except Exception as e:
            logger.error(f"Failed to get OAuth tokens: {e}")
            return None
    
    async def refresh_oauth_tokens(self, user_id: int, server_id: int, provider: str, refresh_token: str) -> Optional[Dict[str, Any]]:
        """Refresh OAuth tokens using refresh token"""
        config = self.oauth_configs.get(provider)
        if not config:
            logger.error(f"OAuth provider '{provider}' not configured")
            return None
        
        token_data = {
            "client_id": config["client_id"],
            "client_secret": config["client_secret"],
            "refresh_token": refresh_token,
            "grant_type": "refresh_token"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    config["token_url"],
                    data=token_data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                ) as response:
                    if response.status == 200:
                        token_response = await response.json()
                        
                        # Calculate expiry time
                        expires_at = None
                        if "expires_in" in token_response:
                            expires_at = datetime.utcnow() + timedelta(seconds=token_response["expires_in"])
                        
                        tokens = {
                            "access_token": token_response.get("access_token"),
                            "refresh_token": refresh_token,  # Keep the same refresh token
                            "token_type": token_response.get("token_type", "Bearer"),
                            "expires_at": expires_at,
                            "scope": token_response.get("scope")
                        }
                        
                        # Update stored tokens
                        await self.store_oauth_tokens(user_id, server_id, provider, tokens)
                        return tokens
                    else:
                        error_text = await response.text()
                        logger.error(f"Token refresh failed: {response.status} - {error_text}")
                        return None
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            return None
    
    async def delete_oauth_tokens(self, user_id: int, server_id: int, provider: str):
        """Delete OAuth tokens for a user/server/provider combination"""
        try:
            await self.prisma.oauthtoken.delete_many(
                where={
                    "userId": user_id,
                    "serverId": server_id,
                    "provider": provider
                }
            )
            logger.info(f"Deleted OAuth tokens for user {user_id}, server {server_id}, provider {provider}")
        except Exception as e:
            logger.error(f"Failed to delete OAuth tokens: {e}")
    
    async def get_user_oauth_status(self, user_id: int) -> List[Dict[str, Any]]:
        """Get OAuth status for all servers for a user"""
        try:
            tokens = await self.prisma.oauthtoken.find_many(
                where={"userId": user_id},
                include={
                    "server": True
                }
            )
            
            status_list = []
            for token in tokens:
                is_valid = True
                if token.expiresAt and token.expiresAt < datetime.utcnow():
                    is_valid = False
                
                status_list.append({
                    "server_id": token.serverId,
                    "server_name": token.server.name,
                    "provider": token.provider,
                    "is_valid": is_valid,
                    "expires_at": token.expiresAt,
                    "scope": token.scope
                })
            
            return status_list
        except Exception as e:
            logger.error(f"Failed to get user OAuth status: {e}")
            return []
    
    def detect_oauth_provider_from_url(self, url: str) -> Optional[str]:
        """Detect OAuth provider from MCP server URL"""
        if "pipedream.net" in url:
            if "gmail" in url.lower():
                return "gmail"
            elif "google" in url.lower():
                return "google"
            # Add more providers as needed
        return None

# Global OAuth service instance
oauth_service = OAuthService() 