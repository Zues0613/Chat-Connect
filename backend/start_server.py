#!/usr/bin/env python3
"""
Start script for ChatConnect Backend Server
"""

import uvicorn
import os
import sys
from pathlib import Path

def main():
    # Get the directory where this script is located
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Configuration
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "true").lower() == "true"
    
    print(f"🚀 Starting ChatConnect Backend Server...")
    print(f"📍 Host: {host}")
    print(f"🔌 Port: {port}")
    print(f"🔄 Reload: {reload}")
    print(f"📁 Working Directory: {os.getcwd()}")
    print(f"🌐 Server URL: http://{host}:{port}")
    print(f"📚 API Docs: http://{host}:{port}/docs")
    print("-" * 50)
    
    try:
        uvicorn.run(
            "app.main:app",
            host=host,
            port=port,
            reload=reload,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 