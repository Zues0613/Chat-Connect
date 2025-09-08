# MCP Host OAuth Implementation Guide

## Overview

This document explains the complete OAuth implementation for the MCP Host platform, which enables secure authentication with external services like Gmail, Google Drive, and other OAuth-enabled MCP servers.

## Architecture

### Database Schema

The OAuth implementation uses three main database models:

1. **OAuthState** - Tracks OAuth flow state for security
2. **OAuthToken** - Stores access and refresh tokens
3. **User/MCPServer** - Extended with OAuth relationships

### Key Components

1. **OAuthService** (`backend/app/services/oauth_service.py`)
   - Manages OAuth flows
   - Handles token storage and refresh
   - Provides provider detection

2. **OAuth Endpoints** (`backend/app/auth/routes.py`)
   - `/auth/oauth/authorize` - Initiates OAuth flow
   - `/auth/oauth/callback` - Handles OAuth callback
   - `/auth/oauth/status` - Gets OAuth status
   - `/auth/oauth/tokens/{server_id}` - Revokes tokens

3. **Frontend Integration** (`frontend/src/app/settings/page.tsx`)
   - OAuth status display
   - Authentication buttons
   - Token management UI

## OAuth Flow

### 1. User Workflow

```
User adds Pipedream MCP server URL
↓
System detects OAuth provider (Gmail/Google)
↓
User clicks "Authenticate Gmail" button
↓
System generates OAuth URL with state parameter
↓
User redirected to Google OAuth consent screen
↓
User authorizes the application
↓
Google redirects back to callback URL
↓
System exchanges code for tokens
↓
Tokens stored securely in database
↓
Future MCP calls include OAuth headers
```

### 2. Technical Flow

#### Step 1: OAuth Initiation
```python
# User clicks authenticate button
POST /auth/oauth/authorize
{
  "server_id": 123,
  "provider": "gmail"  # Optional, auto-detected
}

# Response
{
  "oauth_url": "https://accounts.google.com/o/oauth2/v2/auth?...",
  "state": "abc123...",
  "provider": "gmail",
  "server_name": "My Gmail Workflow"
}
```

#### Step 2: OAuth Callback
```python
# Google redirects to
GET /auth/oauth/callback?code=xyz789&state=abc123

# System processes callback
1. Validates state parameter
2. Exchanges code for tokens
3. Stores tokens in database
4. Redirects to frontend with success message
```

#### Step 3: Token Usage
```python
# When making MCP calls
headers = {
    "Authorization": "Bearer access_token_here",
    "Content-Type": "application/json"
}
```

## Configuration

### Environment Variables

```bash
# Google OAuth
GOOGLE_CLIENT_ID="your-google-client-id"
GOOGLE_CLIENT_SECRET="your-google-client-secret"
OAUTH_REDIRECT_URI="http://localhost:3000/oauth/callback"
FRONTEND_URL="http://localhost:3000"
```

### Google OAuth Setup

1. **Create Google Cloud Project**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create new project or select existing

2. **Enable APIs**
   - Enable Gmail API
   - Enable Google Drive API (if needed)

3. **Create OAuth Credentials**
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth 2.0 Client IDs"
   - Set application type to "Web application"
   - Add authorized redirect URIs:
     - `http://localhost:3000/oauth/callback` (development)
     - `https://yourdomain.com/oauth/callback` (production)

4. **Configure Scopes**
   - Gmail: `https://www.googleapis.com/auth/gmail.send https://www.googleapis.com/auth/gmail.readonly`
   - Google Drive: `https://www.googleapis.com/auth/drive.file`

## Database Migration

Run the following to apply the new OAuth schema:

```bash
cd backend
npx prisma migrate dev --name add_oauth_models
npx prisma generate
```

## Usage Examples

### Adding a Gmail MCP Server

1. **User adds Pipedream URL**
   ```
   https://mcp.pipedream.net/6919d1b2-8143-422f-a5ae-6bca936cdbe6/gmail
   ```

2. **System auto-detects provider**
   ```python
   provider = oauth_service.detect_oauth_provider_from_url(url)
   # Returns "gmail"
   ```

3. **User authenticates**
   - Clicks "🔐 Authenticate GMAIL" button
   - Completes Google OAuth flow
   - Tokens stored securely

4. **Future requests work automatically**
   ```python
   # MCP service automatically includes OAuth headers
   result = await mcp_service.call_tool(
       "mcp_Gmail_gmail-send-email",
       {"instruction": "Send test email"},
       user_id=123
   )
   ```

### Token Management

```python
# Get OAuth status for user
GET /auth/oauth/status

# Response
[
  {
    "server_id": 123,
    "server_name": "My Gmail Workflow",
    "provider": "gmail",
    "is_valid": true,
    "expires_at": "2024-01-15T10:30:00Z",
    "scope": "https://www.googleapis.com/auth/gmail.send..."
  }
]

# Revoke tokens
DELETE /auth/oauth/tokens/123?provider=gmail
```

## Security Features

### 1. State Parameter
- Unique state generated for each OAuth flow
- Prevents CSRF attacks
- 10-minute expiry

### 2. Token Storage
- Access tokens encrypted in database
- Refresh tokens for automatic renewal
- Automatic token expiry handling

### 3. User Isolation
- Tokens tied to specific user/server combinations
- Users can only access their own tokens
- Server ownership verification

### 4. Secure Redirects
- Validated redirect URIs
- HTTPS enforcement in production
- Frontend URL validation

## Error Handling

### Common OAuth Errors

1. **Invalid State**
   ```
   Error: OAuth state expired or invalid
   Solution: Restart OAuth flow
   ```

2. **Token Exchange Failed**
   ```
   Error: Failed to exchange authorization code
   Solution: Check OAuth configuration
   ```

3. **Expired Tokens**
   ```
   Error: OAuth tokens expired
   Solution: Re-authenticate with provider
   ```

### Error Recovery

```python
# Automatic token refresh
if token.expires_at < datetime.utcnow():
    refreshed = await oauth_service.refresh_oauth_tokens(
        user_id, server_id, provider, refresh_token
    )
    if not refreshed:
        # Delete expired token, require re-auth
        await oauth_service.delete_oauth_tokens(user_id, server_id, provider)
```

## Testing

### OAuth Flow Testing

```python
# Test OAuth initiation
async def test_oauth_flow():
    # 1. Create MCP server
    server = await create_mcp_server("test-gmail", gmail_url)
    
    # 2. Initiate OAuth
    oauth_response = await initiate_oauth(server.id, "gmail")
    assert "oauth_url" in oauth_response
    
    # 3. Simulate callback
    tokens = await exchange_code_for_tokens("gmail", "test_code")
    assert "access_token" in tokens
    
    # 4. Test MCP call with OAuth
    result = await mcp_service.call_tool(
        "mcp_Gmail_gmail-send-email",
        {"instruction": "Test email"},
        user_id=user.id
    )
    assert "success" in result
```

### Manual Testing

1. **Add Gmail MCP server**
2. **Click authenticate button**
3. **Complete Google OAuth flow**
4. **Test Gmail functionality**
5. **Verify tokens are stored**
6. **Test token refresh**

## Production Deployment

### 1. Environment Setup
```bash
# Production environment variables
GOOGLE_CLIENT_ID="your-production-client-id"
GOOGLE_CLIENT_SECRET="your-production-client-secret"
OAUTH_REDIRECT_URI="https://yourdomain.com/oauth/callback"
FRONTEND_URL="https://yourdomain.com"
```

### 2. Database Migration
```bash
# Apply migrations
npx prisma migrate deploy
```

### 3. SSL/HTTPS
- Ensure HTTPS for all OAuth redirects
- Update Google OAuth redirect URIs
- Configure secure cookie settings

### 4. Monitoring
- Monitor OAuth success/failure rates
- Track token refresh patterns
- Alert on authentication failures

## Troubleshooting

### Common Issues

1. **"Invalid redirect URI"**
   - Check Google OAuth configuration
   - Verify redirect URI matches exactly

2. **"OAuth provider not configured"**
   - Check environment variables
   - Verify OAuth service initialization

3. **"Token exchange failed"**
   - Check client ID/secret
   - Verify redirect URI consistency

4. **"State parameter invalid"**
   - Check database connection
   - Verify OAuth state cleanup

### Debug Mode

Enable debug logging:

```python
import logging
logging.getLogger("oauth_service").setLevel(logging.DEBUG)
```

## Future Enhancements

### 1. Additional Providers
- GitHub OAuth
- Slack OAuth
- Microsoft Graph OAuth
- Custom OAuth providers

### 2. Advanced Features
- OAuth token sharing between servers
- Granular permission scopes
- OAuth flow customization
- Multi-factor authentication

### 3. Security Improvements
- Token encryption at rest
- Hardware security modules (HSM)
- Audit logging
- Rate limiting

## Conclusion

The OAuth implementation provides a secure, scalable foundation for MCP server authentication. It handles the complete OAuth flow lifecycle while maintaining security best practices and providing a smooth user experience.

For questions or issues, refer to the troubleshooting section or check the application logs for detailed error information. 