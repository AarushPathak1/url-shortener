from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from app.cache.redis_client import redis_client
from app.db.postgres import get_connection

app = FastAPI()

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/db-check")
async def db_check():
    conn = await get_connection()
    try:
        row = await conn.fetchrow("SELECT COUNT(*) FROM urls;")
        return {"count": row["count"]}
    finally:
        await conn.close()

@app.get("/{short_code}")
async def redirect_short_url(short_code: str):
    key = f"url:{short_code}"
    long_url = await redis_client.get(key)

    if not long_url:
        raise HTTPException(status_code=404, detail="Short URL not found")

    return RedirectResponse(url=long_url, status_code=302)

