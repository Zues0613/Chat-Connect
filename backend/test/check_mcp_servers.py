import asyncio
import sys
import os

# Add the parent directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from prisma import Prisma

async def check_mcp_servers():
    prisma = Prisma()
    await prisma.connect()
    
    try:
        # Get all MCP servers
        servers = await prisma.mcpserver.find_many()
        print(f"Total MCP servers in database: {len(servers)}")
        
        if servers:
            print("\nMCP Servers found:")
            for server in servers:
                print(f"- {server.name} (ID: {server.id}, User ID: {server.userId})")
                print(f"  Description: {server.description}")
                print(f"  Config: {server.config}")
                print(f"  Created: {server.createdAt}")
                print()
        else:
            print("No MCP servers found in database")
        
        # Also check users
        users = await prisma.user.find_many()
        print(f"Total users in database: {len(users)}")
        for user in users:
            print(f"- {user.name} ({user.email}) - ID: {user.id}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await prisma.disconnect()

if __name__ == "__main__":
    asyncio.run(check_mcp_servers()) 