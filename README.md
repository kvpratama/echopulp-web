# EchoPulp Web

A FastAPI web app to search, subscribe, and play podcasts using the iTunes API.

## Features
- Search podcasts via iTunes API
- View podcast details and episodes
- Subscribe to podcasts (PostgreSQL)
- Play episodes in browser

## Tech Stack
- FastAPI, Jinja2, SQLAlchemy, PostgreSQL, httpx, feedparser

## Running Locally
1. Install dependencies: `pip install -r requirements.txt`
2. Set up PostgreSQL and configure `.env` (see example below)
3. Start the app: `uvicorn main:app --reload`

### .env Example
```
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/echopulp
```
