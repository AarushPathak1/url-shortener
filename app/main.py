from fastapi import FastAPI
from app.cache.redis_client import redis_client

app = FastAPI()

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/redis-ping")
async def redis_ping():
    pong = await redis_client.ping()
    return {"redis": pong}
