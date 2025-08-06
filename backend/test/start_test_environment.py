#!/usr/bin/env python3
"""
Startup script for ChatConnect MCP testing environment.

This script helps you start all the necessary components for testing:
1. Simple MCP servers
2. ChatConnect backend (optional)
3. Database connection check

Usage:
    python start_test_environment.py [options]
"""

import asyncio
import subprocess
import sys
import time
import os
from pathlib import Path

def print_banner():
    """Print startup banner"""
    print("""
🔧 ChatConnect MCP Testing Environment
=====================================

This script will help you start the testing environment for ChatConnect MCP functionality.

Components:
- Simple MCP servers (Calculator, Weather, File Operations)
- Database connection check
- Optional: ChatConnect backend startup

    """)

def check_dependencies():
    """Check if required dependencies are installed"""
    print("🔍 Checking dependencies...")
    
    required_packages = [
        "fastapi",
        "uvicorn", 
        "aiohttp",
        "prisma"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package} - MISSING")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        print("Please install them with:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    print("✅ All dependencies are installed")
    return True

async def check_database():
    """Check database connection"""
    print("\n🗄️  Checking database connection...")
    
    try:
        from prisma import Prisma
        
        prisma = Prisma()
        await prisma.connect()
        
        # Try to query users
        users = await prisma.user.find_many(take=1)
        await prisma.disconnect()
        
        print("✅ Database connection successful")
        print(f"   Found {len(users)} user(s) in database")
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("\n💡 Make sure:")
        print("   1. Your database is running")
        print("   2. DATABASE_URL is set in .env file")
        print("   3. Prisma migrations are applied")
        return False

def start_simple_mcp_servers():
    """Start the simple MCP servers"""
    print("\n🚀 Starting simple MCP servers...")
    
    try:
        # Start the servers in the background
        process = subprocess.Popen([
            sys.executable, "-m", "app.services.simple_mcp_servers"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait a moment for startup
        time.sleep(3)
        
        # Check if process is still running
        if process.poll() is None:
            print("✅ Simple MCP servers started successfully")
            print("   URL: http://localhost:8001")
            print("   Process ID:", process.pid)
            return process
        else:
            stdout, stderr = process.communicate()
            print(f"❌ Failed to start MCP servers:")
            print(f"   STDOUT: {stdout.decode()}")
            print(f"   STDERR: {stderr.decode()}")
            return None
            
    except Exception as e:
        print(f"❌ Error starting MCP servers: {e}")
        return None

def test_mcp_servers():
    """Test if MCP servers are responding"""
    print("\n🧪 Testing MCP servers...")
    
    try:
        import aiohttp
        import asyncio
        
        async def test_endpoint():
            async with aiohttp.ClientSession() as session:
                # Test the combined endpoint
                async with session.post(
                    "http://localhost:8001/mcp",
                    json={
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "tools/list"
                    },
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        tools = data.get("result", {}).get("tools", [])
                        print(f"✅ MCP servers responding correctly")
                        print(f"   Found {len(tools)} tools")
                        return True
                    else:
                        print(f"❌ MCP servers returned status {response.status}")
                        return False
        
        # Run the test
        result = asyncio.run(test_endpoint())
        return result
        
    except Exception as e:
        print(f"❌ Error testing MCP servers: {e}")
        return False

def add_test_servers_to_db():
    """Add test MCP servers to database"""
    print("\n📝 Adding test MCP servers to database...")
    
    try:
        result = subprocess.run([
            sys.executable, "add_test_mcp_servers.py", "add"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Test MCP servers added to database")
            print(result.stdout)
        else:
            print("❌ Failed to add test servers:")
            print(result.stderr)
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Error adding test servers: {e}")
        return False

def start_chatconnect_backend():
    """Start ChatConnect backend (optional)"""
    print("\n🤖 Starting ChatConnect backend...")
    
    try:
        # Check if main.py exists
        if not Path("app/main.py").exists():
            print("❌ app/main.py not found")
            print("   Make sure you're in the backend directory")
            return None
        
        # Start the backend
        process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", "app.main:app", 
            "--host", "0.0.0.0", "--port", "8000", "--reload"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for startup
        time.sleep(5)
        
        if process.poll() is None:
            print("✅ ChatConnect backend started successfully")
            print("   URL: http://localhost:8000")
            print("   Process ID:", process.pid)
            return process
        else:
            stdout, stderr = process.communicate()
            print(f"❌ Failed to start backend:")
            print(f"   STDOUT: {stdout.decode()}")
            print(f"   STDERR: {stderr.decode()}")
            return None
            
    except Exception as e:
        print(f"❌ Error starting backend: {e}")
        return None

def print_next_steps():
    """Print next steps for testing"""
    print("""
🎉 Testing Environment Ready!
============================

✅ Simple MCP servers running on http://localhost:8001
✅ Test servers added to database
✅ Database connection verified

🚀 Next Steps:
1. Open ChatConnect in your browser: http://localhost:3000
2. Login with your account
3. Start a new chat
4. Try these test prompts:

   Calculator: "What is 15 + 27?"
   Weather: "What's the weather in Tokyo?"
   Files: "Create a file called test.txt with 'Hello World'"

📋 Available Test Tools:
- calculator_add, calculator_multiply, calculator_divide
- weather_get_current, weather_get_forecast  
- file_write, file_read, file_list

🔧 Management Commands:
- List servers: python add_test_mcp_servers.py list
- Delete servers: python add_test_mcp_servers.py delete
- Test directly: curl http://localhost:8001/mcp

📖 Full testing guide: MCP_TESTING_GUIDE.md
    """)

async def main():
    """Main function"""
    print_banner()
    
    # Check dependencies
    if not check_dependencies():
        return
    
    # Check database
    if not await check_database():
        return
    
    # Add test servers to database
    if not add_test_servers_to_db():
        return
    
    # Start MCP servers
    mcp_process = start_simple_mcp_servers()
    if not mcp_process:
        return
    
    # Test MCP servers
    if not test_mcp_servers():
        print("❌ MCP servers are not responding correctly")
        return
    
    # Ask if user wants to start backend
    print("\n🤖 Do you want to start the ChatConnect backend? (y/n): ", end="")
    try:
        response = input().lower().strip()
        if response in ['y', 'yes']:
            backend_process = start_chatconnect_backend()
            if backend_process:
                print("\n✅ Both MCP servers and ChatConnect backend are running!")
            else:
                print("\n⚠️  MCP servers are running, but backend failed to start")
        else:
            print("\n✅ MCP servers are running! You can start the backend manually.")
    except KeyboardInterrupt:
        print("\n\n⚠️  Skipping backend startup")
    
    # Print next steps
    print_next_steps()
    
    # Keep the script running
    try:
        print("\n🔄 Press Ctrl+C to stop all servers...")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down...")
        
        # Stop MCP servers
        if mcp_process:
            mcp_process.terminate()
            print("✅ MCP servers stopped")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1) 