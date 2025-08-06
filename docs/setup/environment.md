# Database Configuration
DATABASE_URL="postgresql://username:password@localhost:5432/chatconnect"

# JWT Configuration
JWT_SECRET_KEY="your-secret-key-here"
JWT_ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Email Configuration (for OTP)
SMTP_SERVER="smtp.gmail.com"
SMTP_PORT=587
SMTP_USERNAME="your-email@gmail.com"
SMTP_PASSWORD="your-app-password"

# Google OAuth Configuration
GOOGLE_CLIENT_ID="your-google-client-id"
GOOGLE_CLIENT_SECRET="your-google-client-secret"
OAUTH_REDIRECT_URI="http://localhost:3000/oauth/callback"
FRONTEND_URL="http://localhost:3000"

# CORS Configuration
CORS_ORIGINS="http://localhost:3000,http://127.0.0.1:3000"

# App Configuration
CHATCONNECT_APP_NAME="ChatConnect"
CHATCONNECT_VERSION="1.0.0"
CHATCONNECT_DESCRIPTION="AI-Powered MCP Integration Platform with DeepSeek R1"

# API Keys (for default functionality)
DEEPSEEK_API_KEY="your-deepseek-api-key"
OPENAI_API_KEY="your-openai-api-key"
ANTHROPIC_API_KEY="your-anthropic-api-key"

# DeepSeek R1 Configuration (ChatConnect)
# Get your API key from: https://platform.deepseek.com/
DEEPSEEK_API_KEY="your-deepseek-api-key-here"
DEEPSEEK_MODEL="deepseek-reasoner"
DEEPSEEK_BASE_URL="https://api.deepseek.com"
DEEPSEEK_MAX_TOKENS=4000
DEEPSEEK_TEMPERATURE=0.1

# Default DeepSeek API Key (fallback for users without personal keys)
# Get your API key from: https://openrouter.ai/
DEFAULT_DEEPSEEK_API_KEY="your-openrouter-api-key-here"

# Development/Production Mode
ENVIRONMENT="development"

# ChatConnect Configuration
CHATCONNECT_APP_NAME="ChatConnect"
CHATCONNECT_VERSION="1.0.0"
CHATCONNECT_DESCRIPTION="AI-Powered MCP Integration Platform with DeepSeek R1"

# Logging Configuration
LOG_LEVEL="INFO"
LOG_FILE="chatconnect.log"

# Pipedream Timeout Configuration (Pipedream Timeout Fix)
# Increased timeouts to prevent 120-second timeout issues
MCP_TIMEOUT=300
PIPEDREAM_TIMEOUT=300

# SMTP Fallback Configuration (for when Pipedream fails)
SMTP_SERVER="smtp.gmail.com"
SMTP_PORT=587
SMTP_USERNAME="your-email@gmail.com"
SMTP_PASSWORD="your-app-password"

# Pipedream Health Check Configuration
PIPEDREAM_HEALTH_CHECK_ENABLED=true
PIPEDREAM_HEALTH_CHECK_INTERVAL=300 