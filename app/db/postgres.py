import asyncpg

DATABASE_URL = "postgresql://postgres:postgres@db:5432/url_shortener"

async def get_connection():
    return await asyncpg.connect(DATABASE_URL)
