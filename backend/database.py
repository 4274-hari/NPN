from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from config import settings


client = AsyncIOMotorClient(settings.mongodb_url)


def get_database() -> AsyncIOMotorDatabase:
    return client[settings.mongodb_database]


async def connect_to_mongo() -> None:
    await client.admin.command("ping")
    print(f"Connected to MongoDB database: {settings.mongodb_database}")


def close_mongo_connection() -> None:
    client.close()
