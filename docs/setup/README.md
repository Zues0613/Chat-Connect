# ChatConnect Setup Guide

## 🚀 **Quick Start**

Get ChatConnect up and running in 5 minutes with this comprehensive setup guide.

## 📋 **Prerequisites**

- **Node.js** 18+ and **npm**
- **Python** 3.9+
- **PostgreSQL** database
- **Git**

## 🛠 **Installation Steps**

### **1. Clone the Repository**

```bash
git clone https://github.com/your-repo/mcp-host.git
cd mcp-host
```

### **2. Backend Setup**

```bash
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies (for Prisma)
npm install

# Set up environment variables
cp env.example .env
# Edit .env with your configuration
```

### **3. Database Setup**

```bash
# Apply database migrations
npx prisma migrate dev --name init

# Generate Prisma client
npx prisma generate
```

### **4. Frontend Setup**

```bash
cd ../frontend

# Install dependencies
npm install

# Set up environment variables
cp .env.example .env.local
# Edit .env.local with your configuration
```

### **5. Start the Application**

```bash
# Terminal 1: Start backend
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Start frontend
cd frontend
npm run dev
```

## ⚙️ **Configuration**

### **Environment Variables**

See [Environment Configuration](./environment.md) for complete details.

**Required Variables:**
```bash
# Database
DATABASE_URL="postgresql://username:password@localhost:5432/chatconnect"

# JWT
JWT_SECRET_KEY="your-secret-key-here"

# OAuth (for Gmail/Google integration)
GOOGLE_CLIENT_ID="your-google-client-id"
GOOGLE_CLIENT_SECRET="your-google-client-secret"
OAUTH_REDIRECT_URI="http://localhost:3000/oauth/callback"
```

### **Google OAuth Setup**

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

## 🔧 **Development Setup**

### **Database Development**

```bash
# Reset database (development only)
npx prisma migrate reset --force

# View database in browser
npx prisma studio

# Generate new migration
npx prisma migrate dev --name your_migration_name
```

### **Testing**

```bash
# Run backend tests
cd backend
python -m pytest

# Run frontend tests
cd frontend
npm test
```

### **Code Quality**

```bash
# Backend linting
cd backend
black .
flake8 .

# Frontend linting
cd frontend
npm run lint
```

## 🐳 **Docker Setup (Optional)**

### **Docker Compose**

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### **Individual Containers**

```bash
# Backend container
docker build -t chatconnect-backend ./backend
docker run -p 8000:8000 chatconnect-backend

# Frontend container
docker build -t chatconnect-frontend ./frontend
docker run -p 3000:3000 chatconnect-frontend
```

## 🔍 **Verification**

### **Backend Health Check**

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "app": "ChatConnect",
  "version": "1.0.0"
}
```

### **Frontend Access**

Open [http://localhost:3000](http://localhost:3000) in your browser.

### **API Documentation**

Visit [http://localhost:8000/docs](http://localhost:8000/docs) for interactive API documentation.

## 🚨 **Troubleshooting**

### **Common Issues**

1. **Database Connection Failed**
   ```bash
   # Check PostgreSQL is running
   sudo systemctl status postgresql
   
   # Verify connection string
   psql "postgresql://username:password@localhost:5432/chatconnect"
   ```

2. **OAuth Not Working**
   - Verify Google OAuth credentials
   - Check redirect URI matches exactly
   - Ensure HTTPS in production

3. **Port Already in Use**
   ```bash
   # Find process using port
   lsof -i :8000
   
   # Kill process
   kill -9 <PID>
   ```

4. **Prisma Migration Issues**
   ```bash
   # Reset database (development only)
   npx prisma migrate reset --force
   
   # Regenerate client
   npx prisma generate
   ```

### **Logs**

```bash
# Backend logs
tail -f backend/logs/app.log

# Frontend logs
npm run dev 2>&1 | tee frontend.log
```

## 📚 **Next Steps**

- [Environment Configuration](./environment.md) - Detailed environment setup
- [Database Setup](./database.md) - Database configuration and management
- [Development Guide](../development/README.md) - Development workflow
- [User Guide](../user-guide/README.md) - Using ChatConnect
- [OAuth Setup](../oauth/README.md) - OAuth configuration

## 🤝 **Support**

- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Documentation**: [Main Documentation](../README.md)
- **Community**: [GitHub Discussions](https://github.com/your-repo/discussions)

---

**Last Updated**: January 2025  
**Version**: 1.0.0 