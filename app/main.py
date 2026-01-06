from fastapi import FastAPI
import redis.asyncio as redis

app = FastAPI()

redis_client = redis.Redis(host="redis", port=6379, decode_responses=True)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/redis-ping")
async def redis_ping():
    pong = await redis_client.ping()
    return {"redis": pong}
