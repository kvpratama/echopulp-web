import uvicorn
import httpx
from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database import SessionLocal, engine, Base
from subscriptions.models import Subscription
from subscriptions.routes import router as subscriptions_router
from podcast.routes import router as podcast_router
from app_config import templates

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(subscriptions_router)
app.include_router(podcast_router)

# Dependency
async def get_db():
    async with SessionLocal() as db:
        yield db

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/search")
async def search(request: Request, q: str = "", db: AsyncSession = Depends(get_db)):
    podcasts = []
    subscribed_ids = set()
    if q:
        url = f"https://itunes.apple.com/search?media=podcast&term={q}"
        async with httpx.AsyncClient() as client:
            resp = await client.get(url)
            data = resp.json()
            podcasts = data.get("results", [])
        # Get user's subscriptions
        user_id = "default"
        result = await db.execute(select(Subscription.podcast_id).where(Subscription.user_id == user_id))
        subscribed_ids = set(row[0] for row in result.all())
    return templates.TemplateResponse(
        "search.html",
        {"request": request, "podcasts": podcasts, "query": q, "subscribed_ids": subscribed_ids}
    )

if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)
