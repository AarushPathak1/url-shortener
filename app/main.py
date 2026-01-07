from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from app.cache.redis_client import redis_client
from app.db.postgres import get_connection
from pydantic import BaseModel, HttpUrl
from app.utils.base62 import encode_base62


app = FastAPI()


class CreateURLRequest(BaseModel):
    long_url: HttpUrl


class CreateURLResponse(BaseModel):
    short_code: str
    short_url: str


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


@app.post("/api/v1/urls", response_model=CreateURLResponse)
async def create_short_url(payload: CreateURLRequest):
    conn = await get_connection()
    try:
        # 1) Insert row to get DB-generated id
        row = await conn.fetchrow(
            "INSERT INTO urls (long_url) VALUES ($1) RETURNING id;",
            str(payload.long_url),
        )
        url_id = row["id"]

        # 2) Generate short code from id
        short_code = encode_base62(url_id)

        # 3) Update row with short_code
        await conn.execute(
            "UPDATE urls SET short_code = $1 WHERE id = $2;",
            short_code,
            url_id,
        )

        # 4) Warm Redis cache
        await redis_client.set(
            f"url:{short_code}",
            str(payload.long_url),
            ex=60 * 60 * 24,
        )

        return CreateURLResponse(
            short_code=short_code,
            short_url=f"http://localhost:8000/{short_code}",
        )
    finally:
        await conn.close()
