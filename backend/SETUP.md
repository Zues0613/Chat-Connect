# Vee Chatbot Backend Setup

## Quick Start

1. **Install Dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Database Setup**
   ```bash
   # Set up your PostgreSQL database
   npx prisma generate
   npx prisma db push
   ```

3. **Environment Configuration**
   Copy `env.example` to `.env` and configure:
   ```bash
   cp env.example .env
   ```

4. **Required Environment Variables**
   Edit `.env` and set these essential variables:

   ```bash
   # Database (replace with your PostgreSQL URL)
   DATABASE_URL="postgresql://username:password@localhost:5432/vee_chatbot"

   # JWT Secret (generate a secure random string)
   JWT_SECRET="your-super-secret-jwt-key-change-this-in-production"

   # DEFAULT DEEPSEEK API KEY (REQUIRED!)
   DEFAULT_DEEPSEEK_API_KEY="your-deepseek-api-key-here"
   ```

5. **Get Your DeepSeek API Key**
   - Go to [DeepSeek Console](https://platform.deepseek.com/)
   - Create a new API key
   - Copy it to `DEFAULT_DEEPSEEK_API_KEY` in your `.env` file

6. **Start the Server**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

## Important Notes

- **Default API Key**: The `DEFAULT_DEEPSEEK_API_KEY` is used as a fallback for all users who haven't added their own API keys
- **User API Keys**: Users can add their own API keys via the settings page for personalized usage
- **MCP Servers**: Users can configure their own MCP servers in the settings for task automation

## Features Enabled

✅ **DeepSeek AI Chat** - Powered by your default API key  
✅ **MCP Integration** - Tool calling and automation  
✅ **User Management** - OTP-based authentication  
✅ **API Key Management** - Personal API keys per user  
✅ **Session Management** - 2-day inactivity-based sessions  

## Test User

For development, use `test@gmail.com` which bypasses OTP and logs in as "Admin" automatically. 