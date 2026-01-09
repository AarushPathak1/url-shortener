# Scalable URL Shortener

A production-style URL shortening backend designed for low-latency, high-throughput redirects. Built with FastAPI, Redis, and PostgreSQL to demonstrate cache-aside patterns, rate limiting, 
analytics, and scalable system design.

This project mirrors classic system design problems (Bitly / TinyURL) and focuses on **correct architectural tradeoffs**, not just CRUD functionality.

---

## Key Goals

- Optimize **read-heavy traffic** with a cache-first design
- Ensure correctness under **concurrent writes**
- Keep API servers **stateless and horizontally scalable**
- Protect write endpoints with **rate limiting**
- Track analytics **without impacting redirect latency**
- Be fully **reproducible locally** using Docker Compose

---

## Architecture Overview

### High-Level System Diagram

```text
Client
  |
  v
Nginx (Load Balancer)
  |
  v
FastAPI (Stateless API Replicas)
  |
  +-------------------+
  |                   |
  v                   v
Redis             PostgreSQL
(Cache, Rate       (Source of
 Limiting,          Truth)
 Analytics)

```
---

## Core Components

- FastAPI — async, stateless API layer
- Redis
- Cache for redirects
- Rate limiting counters
- Click analytics counters
- PostgreSQL — persistent source of truth for URL mappings
- Nginx — load balancer distributing traffic across API replicas
- Docker Compose — local production-like orchestration

---

## End-to-End Data Flow

### URL Creation/Write Path
```text
POST /api/v1/urls
  |
  v
Rate Limit Check (Redis)
  |
  v
INSERT long_url into PostgreSQL
  |
  v
DB generates unique ID
  |
  v
ID → Base62 short_code
  |
  v
UPDATE row with short_code
  |
  v
Warm Redis cache
  |
  v
Return short URL

```
### Redirect(Read Path/Hot Path)
```text
GET /r/{short_code}
  |
  v
Redis GET url:{short_code}
  |
  +-- HIT --> Redirect immediately (302)
  |
  +-- MISS --> PostgreSQL lookup
                |
                v
              Cache result in Redis
                |
                v
              Redirect (302)
```

### Analytics (non-blocking)

```text
Redirect Response
  |
  v
Redis INCR clicks:{short_code}

```
---

## Core Features

### URL Creation

- Endpoint: POST /api/v1/urls
- Database-generated IDs encoded using Base62
- Guaranteed uniqueness under concurrency
- Redis cache warming on write
- Redis-based rate limiting (5 requests/min per IP)

### Redirects

- Endpoint: GET /r/{short_code}
- Cache-first lookup (Redis)
- Database fallback (cache-aside)
- Sub-10ms latency on cache hits
- Stateless and horizontally scalable

### Analytics

- Endpoint: GET /api/v1/analytics/{short_code}
- Aggregated click counters stored in Redis
- Zero impact on redirect latency

---

## Rate-Limiting Design

- Fixed-window rate limiting using Redis
- Key format:
  ```text
  rate:create:{ip}
  ```
- Algorithm:
  - INCR counter
  - Set EXPIRE on first request
  - Reject if count exceeds limit
- Load balancer safe
- Protects write-heavy endpoints

---

