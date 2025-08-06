# ChatConnect Backend Server

This is the backend server for ChatConnect, an AI-powered MCP integration platform.

## Quick Start

### Option 1: Using the Batch File (Windows)
```bash
# Double-click or run in command prompt
start_server.bat
```

### Option 2: Manual Start
```bash
# 1. Create virtual environment (if not exists)
python -m venv venv

# 2. Activate virtual environment
# Windows:
venv\Scripts\activate.bat
# macOS/Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start the server
python start_server.py
```

### Option 3: Using uvicorn directly
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

## Server Information

- **URL**: http://127.0.0.1:8000
- **API Documentation**: http://127.0.0.1:8000/docs
- **Health Check**: http://127.0.0.1:8000/health

## Environment Variables

Create a `.env` file in the backend directory with the following variables:

```env
# Server Configuration
HOST=127.0.0.1
PORT=8000
RELOAD=true

# Database
DATABASE_URL="your_database_url_here"

# JWT Secret
JWT_SECRET_KEY="your_jwt_secret_here"

# DeepSeek API
DEFAULT_DEEPSEEK_API_KEY="your_deepseek_api_key_here"

# Google OAuth (for Gmail integration)
GOOGLE_CLIENT_ID="your_google_client_id"
GOOGLE_CLIENT_SECRET="your_google_client_secret"
OAUTH_REDIRECT_URI="http://localhost:3000/oauth/callback"
FRONTEND_URL="http://localhost:3000"

# CORS
CORS_ORIGINS="http://localhost:3000,http://127.0.0.1:3000"
```

## Troubleshooting

### Common Issues

1. **Port already in use**
   - Change the PORT in .env file or kill the process using port 8000

2. **Database connection error**
   - Check your DATABASE_URL in .env file
   - Ensure the database is running

3. **Module not found errors**
   - Make sure you're in the virtual environment
   - Run `pip install -r requirements.txt`

4. **Frontend can't connect**
   - Ensure the backend server is running on http://127.0.0.1:8000
   - Check CORS settings in .env file

### Logs

The server logs will show:
- API requests and responses
- Database operations
- MCP server connections
- Error details

## API Endpoints

- `/auth/*` - Authentication endpoints
- `/chat/*` - Chat functionality
- `/chatconnect/*` - DeepSeek R1 integration
- `/docs` - Interactive API documentation
- `/health` - Health check endpoint 