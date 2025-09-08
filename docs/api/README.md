# ChatConnect API Documentation

## 📚 **API Overview**

ChatConnect provides a comprehensive REST API for managing MCP servers, user authentication, OAuth flows, and chat functionality. All endpoints return JSON responses and use standard HTTP status codes.

## 🔐 **Authentication**

Most endpoints require JWT authentication. Include the token in the Authorization header:

```bash
Authorization: Bearer <your-jwt-token>
```

## 📋 **API Endpoints**

### **Authentication & User Management**

#### **User Registration & Login**
- `POST /auth/register` - Register new user
- `POST /auth/send-otp` - Send OTP for authentication
- `POST /auth/verify-otp` - Verify OTP and get JWT token
- `GET /auth/me` - Get current user information

#### **API Key Management**
- `GET /auth/api-keys` - List user's API keys
- `POST /auth/api-keys` - Add new API key
- `DELETE /auth/api-keys/{key_id}` - Delete API key

### **MCP Server Management**

#### **Server Operations**
- `GET /auth/mcp-servers` - List user's MCP servers
- `POST /auth/mcp-servers` - Add new MCP server
- `DELETE /auth/mcp-servers/{server_id}` - Delete MCP server
- `POST /auth/mcp-servers/{server_id}/test` - Test MCP server connection

#### **MCP Tools**
- `GET /chat/mcp/tools` - Get available MCP tools
- `POST /chat/mcp/servers/{server_id}/connect` - Connect to MCP server

### **OAuth Authentication**

#### **OAuth Flow**
- `POST /auth/oauth/authorize` - Initiate OAuth flow
- `GET /auth/oauth/callback` - Handle OAuth callback
- `GET /auth/oauth/status` - Get OAuth status for user
- `DELETE /auth/oauth/tokens/{server_id}` - Revoke OAuth tokens

### **Chat & Messaging**

#### **Chat Sessions**
- `POST /chat/chats` - Create new chat session
- `GET /chat/chats` - List user's chat sessions
- `PUT /chat/chats/{chat_id}/title` - Update chat title
- `DELETE /chat/chats/{chat_id}` - Delete chat session

#### **Messages**
- `GET /chat/chats/{chat_id}/messages` - Get chat messages
- `POST /chat/chats/{chat_id}/messages` - Send message
- `POST /chat/chats/{chat_id}/messages/stream` - Stream chat response

### **ChatConnect (DeepSeek R1)**

#### **Enhanced Chat**
- `POST /chatconnect/chats` - Create ChatConnect chat
- `GET /chatconnect/chats` - List ChatConnect chats
- `GET /chatconnect/chats/{chat_id}/messages` - Get ChatConnect messages
- `POST /chatconnect/chats/{chat_id}/messages` - Send ChatConnect message
- `GET /chatconnect/mcp/tools` - Get available MCP tools

## 📖 **Detailed Endpoint Documentation**

### **Authentication Endpoints**

#### `POST /auth/register`
Register a new user account.

**Request Body:**
```json
{
  "name": "John Doe",
  "email": "john@example.com"
}
```

**Response:**
```json
{
  "message": "Registration successful",
  "user": {
    "id": 1,
    "name": "John Doe",
    "email": "john@example.com"
  }
}
```

#### `POST /auth/verify-otp`
Verify OTP and get JWT token.

**Request Body:**
```json
{
  "email": "john@example.com",
  "otp": "123456"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer"
}
```

### **MCP Server Endpoints**

#### `POST /auth/mcp-servers`
Add a new MCP server.

**Request Body:**
```json
{
  "name": "My Gmail Workflow",
  "description": "Gmail automation via Pipedream",
  "config": {
    "type": "custom",
    "uri": "https://mcp.pipedream.net/6919d1b2-8143-422f-a5ae-6bca936cdbe6/gmail",
    "transport": "http"
  }
}
```

**Response:**
```json
{
  "id": 1,
  "name": "My Gmail Workflow",
  "description": "Gmail automation via Pipedream",
  "config": {
    "type": "custom",
    "uri": "https://mcp.pipedream.net/6919d1b2-8143-422f-a5ae-6bca936cdbe6/gmail",
    "transport": "http"
  },
  "createdAt": "2025-01-15T10:30:00Z"
}
```

#### `POST /auth/mcp-servers/{server_id}/test`
Test connection to an MCP server.

**Response:**
```json
{
  "success": true,
  "tools_count": 3,
  "tools": [
    "mcp_Gmail_gmail-send-email",
    "mcp_Gmail_gmail-find-email",
    "mcp_Gmail_gmail-list-labels"
  ],
  "message": "Successfully connected to Pipedream workflow. Found 3 tools."
}
```

### **OAuth Endpoints**

#### `POST /auth/oauth/authorize`
Initiate OAuth flow for an MCP server.

**Request Body:**
```json
{
  "server_id": 1,
  "provider": "gmail"
}
```

**Response:**
```json
{
  "oauth_url": "https://accounts.google.com/o/oauth2/v2/auth?client_id=...",
  "state": "abc123...",
  "provider": "gmail",
  "server_name": "My Gmail Workflow"
}
```

#### `GET /auth/oauth/status`
Get OAuth status for all user's MCP servers.

**Response:**
```json
[
  {
    "server_id": 1,
    "server_name": "My Gmail Workflow",
    "provider": "gmail",
    "is_valid": true,
    "expires_at": "2025-01-15T10:30:00Z",
    "scope": "https://www.googleapis.com/auth/gmail.send..."
  }
]
```

### **Chat Endpoints**

#### `POST /chat/chats/{chat_id}/messages`
Send a message in a chat session.

**Request Body:**
```json
{
  "content": "Send me an email using Gmail",
  "chatId": 1
}
```

**Response:**
```json
{
  "id": 1,
  "content": "I'll help you send an email using Gmail. Let me use the Gmail integration to send your email.",
  "role": "assistant",
  "createdAt": "2025-01-15T10:30:00Z"
}
```

## 🔧 **Error Handling**

### **Standard Error Response**
```json
{
  "detail": "Error message description"
}
```

### **Common HTTP Status Codes**
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `404` - Not Found
- `422` - Validation Error
- `500` - Internal Server Error

### **OAuth Error Responses**
```json
{
  "error": "OAuth authentication required",
  "oauth_required": true,
  "message": "Please authenticate with Gmail first"
}
```

## 🧪 **Testing the API**

### **Using curl**

```bash
# Register user
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name": "Test User", "email": "test@example.com"}'

# Get OTP
curl -X POST http://localhost:8000/auth/send-otp \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'

# Verify OTP and get token
curl -X POST http://localhost:8000/auth/verify-otp \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "otp": "123456"}'

# Use token for authenticated requests
curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### **Using the Interactive Documentation**

Visit [http://localhost:8000/docs](http://localhost:8000/docs) for interactive API documentation with Swagger UI.

## 📚 **Related Documentation**

- [Authentication Guide](../user-guide/authentication.md) - User authentication workflow
- [MCP Server Management](../user-guide/mcp-servers.md) - Managing MCP servers
- [OAuth Setup](../oauth/README.md) - OAuth configuration
- [Development Guide](../development/README.md) - API development

## 🤝 **Support**

- **API Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Documentation**: [Main Documentation](../README.md)
- **Interactive Docs**: [Swagger UI](http://localhost:8000/docs)

---

**Last Updated**: January 2025  
**API Version**: 1.0.0 