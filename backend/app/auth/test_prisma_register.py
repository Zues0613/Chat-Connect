import asyncio
from prisma import Prisma

async def test_register():
    prisma = Prisma()
    await prisma.connect()
    # Try to create a user
    user = await prisma.user.create(
        data={
            "name": "Test User",
            "email": "testuser@example.com"
        }
    )
    print("User created:", user)
    # Try to fetch the user
    fetched = await prisma.user.find_unique(where={"email": "testuser@example.com"})
    print("Fetched user:", fetched)
    await prisma.disconnect()

if __name__ == "__main__":
    asyncio.run(test_register())
