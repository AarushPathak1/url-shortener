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

    # 1) Try Redis first
    long_url = await redis_client.get(key)
    if long_url:
        return RedirectResponse(url=long_url, status_code=302)

    # 2) Fallback to Postgres
    conn = await get_connection()
    try:
        row = await conn.fetchrow(
            "SELECT long_url FROM urls WHERE short_code = $1;",
            short_code
        )
        if not row:
            raise HTTPException(status_code=404, detail="Short URL not found")

        long_url = row["long_url"]

        # 3) Populate Redis (cache-aside)
        await redis_client.set(key, long_url, ex=60 * 60 * 24)  # 24h TTL

        return RedirectResponse(url=long_url, status_code=302)
    finally:
        await conn.close()
