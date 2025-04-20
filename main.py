import uvicorn
from fastapi import FastAPI, Request, Form, Depends, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import httpx
import feedparser
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from database import SessionLocal, engine
from models import Base, Subscription
import asyncio

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

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
async def search(request: Request, q: str = ""):
    podcasts = []
    if q:
        url = f"https://itunes.apple.com/search?media=podcast&term={q}"
        async with httpx.AsyncClient() as client:
            resp = await client.get(url)
            data = resp.json()
            podcasts = data.get("results", [])
    return templates.TemplateResponse("search.html", {"request": request, "podcasts": podcasts, "query": q})

@app.get("/podcast/{podcast_id}")
async def podcast_detail(request: Request, podcast_id: str, feed_url: str, title: str = "", artwork: str = ""):
    episodes = []
    if feed_url:
        parsed = feedparser.parse(feed_url)
        episodes = parsed.entries
    return templates.TemplateResponse("details.html", {"request": request, "podcast_id": podcast_id, "feed_url": feed_url, "title": title, "artwork": artwork, "episodes": episodes})

@app.post("/subscribe")
async def subscribe(request: Request, podcast_id: str = Form(...), podcast_title: str = Form(...), feed_url: str = Form(...), artwork_url: str = Form(...), db: AsyncSession = Depends(get_db)):
    user_id = "default"
    sub = Subscription(user_id=user_id, podcast_id=podcast_id, podcast_title=podcast_title, feed_url=feed_url, artwork_url=artwork_url)
    db.add(sub)
    try:
        await db.commit()
        message = "Subscribed successfully!"
    except IntegrityError:
        await db.rollback()
        message = "You are already subscribed to this podcast."
    except Exception:
        await db.rollback()
        message = "An error occurred while subscribing."
    response = RedirectResponse(url=f"/subscriptions?msg={message}", status_code=status.HTTP_302_FOUND)
    return response

@app.get("/subscriptions")
async def subscriptions(request: Request, db: AsyncSession = Depends(get_db)):
    user_id = "default"
    result = await db.execute(select(Subscription).where(Subscription.user_id == user_id))
    subs = result.scalars().all()
    msg = request.query_params.get("msg", None)
    return templates.TemplateResponse("subscriptions.html", {"request": request, "subs": subs, "msg": msg})

if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)
