#!/usr/bin/env python3
"""
Simple database connection test
"""

import asyncio
import sys
import os
from prisma import Prisma

# Add the parent directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

async def test_database_connection():
    """Test database connection"""
    try:
        prisma = Prisma()
        await prisma.connect()
        print("✅ Database connection successful")
        
        # Test a simple query
        user_count = await prisma.user.count()
        print(f"✅ Database query successful - Users in database: {user_count}")
        
        await prisma.disconnect()
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_database_connection())
    if success:
        print("🎉 Database is ready for ChatConnect!")
    else:
        print("⚠️ Database needs attention before starting ChatConnect") 