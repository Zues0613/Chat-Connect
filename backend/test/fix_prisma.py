#!/usr/bin/env python3
"""
Script to fix Prisma client and test database connection
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n🔧 {description}")
    print(f"   Command: {command}")
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, cwd=Path(__file__).parent)
        
        if result.returncode == 0:
            print(f"   ✅ Success")
            if result.stdout:
                print(f"   Output: {result.stdout.strip()}")
        else:
            print(f"   ❌ Failed")
            print(f"   Error: {result.stderr.strip()}")
            return False
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return False
    
    return True

def main():
    """Main function to fix Prisma issues"""
    print("🚀 Prisma Fix Script")
    print("=" * 50)
    
    # Check if we're in the backend directory
    backend_dir = Path(__file__).parent
    if not (backend_dir / "prisma" / "schema.prisma").exists():
        print("❌ Error: This script must be run from the backend directory")
        return
    
    print(f"✅ Backend directory: {backend_dir}")
    
    # Step 1: Generate Prisma client
    if not run_command("prisma generate", "Generating Prisma client"):
        print("❌ Failed to generate Prisma client")
        return
    
    # Step 2: Push schema to database (if needed)
    print(f"\n📋 Database Operations")
    print("   Choose an option:")
    print("   1. Push schema (recommended for development)")
    print("   2. Deploy migrations (recommended for production)")
    print("   3. Skip database operations")
    
    choice = input("   Enter choice (1-3): ").strip()
    
    if choice == "1":
        if not run_command("prisma db push", "Pushing schema to database"):
            print("❌ Failed to push schema")
            return
    elif choice == "2":
        if not run_command("prisma migrate deploy", "Deploying migrations"):
            print("❌ Failed to deploy migrations")
            return
    elif choice == "3":
        print("   ⏭️  Skipping database operations")
    else:
        print("   ❌ Invalid choice")
        return
    
    # Step 3: Test database connection
    print(f"\n🧪 Testing Database Connection")
    
    test_script = """
import asyncio
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from dotenv import load_dotenv
load_dotenv()

async def test_db():
    try:
        from prisma import Prisma
        
        prisma = Prisma()
        await prisma.connect()
        print("✅ Database connection successful")
        
        # Test basic operations
        users = await prisma.user.find_many()
        print(f"✅ Found {len(users)} users")
        
        servers = await prisma.mcpserver.find_many()
        print(f"✅ Found {len(servers)} MCP servers")
        
        await prisma.disconnect()
        print("✅ Database test completed successfully")
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(test_db())
"""
    
    # Write test script
    test_file = backend_dir / "temp_db_test.py"
    with open(test_file, "w") as f:
        f.write(test_script)
    
    # Run test
    if not run_command("python temp_db_test.py", "Testing database connection"):
        print("❌ Database test failed")
    else:
        print("✅ Database test passed")
    
    # Clean up
    if test_file.exists():
        test_file.unlink()
    
    print(f"\n🎉 Prisma fix completed!")
    print(f"\n💡 Next steps:")
    print(f"1. Try adding an MCP server again")
    print(f"2. If it still fails, run: python test_db_schema.py")
    print(f"3. Check the backend logs for detailed error messages")

if __name__ == "__main__":
    main() 