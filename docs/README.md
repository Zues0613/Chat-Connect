# ChatConnect - MCP Host Platform Documentation

## 📚 **Documentation Index**

Welcome to the comprehensive documentation for ChatConnect, an AI-powered MCP (Model Context Protocol) integration platform. This documentation is organized into logical sections for easy navigation.

## 🚀 **Quick Start**

### **Getting Started**
- [Setup Guide](./setup/README.md) - Complete installation and setup instructions
- [Environment Configuration](./setup/environment.md) - Environment variables and configuration
- [Database Setup](./setup/database.md) - Database configuration and migrations

### **Core Features**
- [MCP Host Architecture](./architecture/README.md) - System architecture and design
- [OAuth Implementation](./oauth/README.md) - Complete OAuth flow documentation
- [API Documentation](./api/README.md) - Backend API endpoints and usage

## 📖 **Documentation Sections**

### **1. Setup & Installation**
- [Setup Guide](./setup/README.md) - Complete setup instructions
- [Environment Configuration](./setup/environment.md) - Environment variables
- [Database Setup](./setup/database.md) - Database configuration
- [Development Setup](./setup/development.md) - Development environment

### **2. Architecture & Design**
- [System Architecture](./architecture/README.md) - High-level system design
- [MCP Integration](./architecture/mcp-integration.md) - MCP protocol integration
- [OAuth Flow](./oauth/README.md) - OAuth authentication system
- [Database Schema](./architecture/database-schema.md) - Database design

### **3. API Documentation**
- [Authentication API](./api/authentication.md) - User authentication endpoints
- [MCP Server API](./api/mcp-servers.md) - MCP server management
- [Chat API](./api/chat.md) - Chat functionality endpoints
- [OAuth API](./api/oauth.md) - OAuth flow endpoints

### **4. User Guides**
- [User Manual](./user-guide/README.md) - End-user documentation
- [MCP Server Management](./user-guide/mcp-servers.md) - Managing MCP servers
- [OAuth Authentication](./user-guide/oauth-authentication.md) - OAuth setup guide
- [Troubleshooting](./user-guide/troubleshooting.md) - Common issues and solutions

### **5. Development**
- [Development Guide](./development/README.md) - Developer documentation
- [Testing Guide](./development/testing.md) - Testing procedures
- [Deployment Guide](./development/deployment.md) - Production deployment
- [Contributing](./development/contributing.md) - Contribution guidelines

### **6. Integration Guides**
- [Pipedream Integration](./integrations/pipedream.md) - Pipedream MCP workflows
- [Gmail Integration](./integrations/gmail.md) - Gmail OAuth setup
- [Custom MCP Servers](./integrations/custom-mcp.md) - Custom MCP server setup

## 🎯 **Key Features**

### **MCP Host Platform**
- **Multi-Protocol Support**: HTTP, WebSocket, stdio, SSE
- **OAuth Integration**: Secure authentication for external services
- **Tool Discovery**: Automatic MCP tool detection and registration
- **User Management**: Multi-user support with isolated workspaces

### **OAuth Authentication**
- **Google OAuth**: Gmail, Google Drive, and other Google services
- **Secure Token Management**: Automatic refresh and secure storage
- **Provider Detection**: Auto-detection of OAuth requirements
- **User-Friendly Flow**: Seamless authentication experience

### **AI Integration**
- **Multiple AI Models**: DeepSeek R1, OpenAI GPT, Anthropic Claude
- **Conversational Interface**: Natural language interaction
- **Tool Execution**: AI-powered tool calling and automation
- **Context Management**: Persistent chat sessions

## 🔧 **Technology Stack**

### **Backend**
- **FastAPI**: Modern Python web framework
- **Prisma**: Type-safe database ORM
- **PostgreSQL**: Primary database
- **JWT**: Stateless authentication

### **Frontend**
- **Next.js 14**: React framework with App Router
- **TypeScript**: Type-safe JavaScript
- **Tailwind CSS**: Utility-first CSS framework
- **React Hook Form**: Form management

### **Infrastructure**
- **Docker**: Containerization
- **OAuth 2.0**: Authentication protocol
- **MCP Protocol**: Model Context Protocol
- **WebSocket**: Real-time communication

## 📋 **Project Structure**

```
mcp-host/
├── docs/                    # 📚 This documentation
├── backend/                 # 🐍 FastAPI backend
│   ├── app/                # Application code
│   ├── prisma/             # Database schema
│   └── test/               # Backend tests
├── frontend/               # ⚛️ Next.js frontend
│   ├── src/                # Source code
│   └── public/             # Static assets
└── README.md               # Project overview
```

## 🚀 **Quick Links**

- [**Setup Guide**](./setup/README.md) - Get started in 5 minutes
- [**OAuth Setup**](./oauth/README.md) - Configure OAuth authentication
- [**API Reference**](./api/README.md) - Complete API documentation
- [**User Guide**](./user-guide/README.md) - End-user documentation
- [**Development Guide**](./development/README.md) - Developer resources

## 🤝 **Support & Community**

- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-repo/discussions)
- **Documentation**: This comprehensive guide
- **Examples**: [Integration Examples](./integrations/README.md)

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.

---

**Last Updated**: January 2025  
**Version**: 1.0.0  
**Maintainer**: ChatConnect Team 