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

@app.get("/podcast/{podcast_id}")
async def podcast_detail(request: Request, podcast_id: str, feed_url: str, title: str = "", artwork: str = "", msg: str = None, db: AsyncSession = Depends(get_db)):
    user_id = "default"
    # Check if subscribed
    sub_result = await db.execute(select(Subscription).where((Subscription.user_id == user_id) & (Subscription.podcast_id == podcast_id)))
    is_subscribed = sub_result.scalar() is not None
    episodes = []
    if feed_url:
        parsed = feedparser.parse(feed_url)
        episodes = parsed.entries
    return templates.TemplateResponse(
        "details.html",
        {
            "request": request,
            "podcast_id": podcast_id,
            "feed_url": feed_url,
            "title": title,
            "artwork": artwork,
            "episodes": episodes,
            "is_subscribed": is_subscribed,
            "msg": msg
        }
    )

@app.post("/subscribe")
async def subscribe(request: Request, podcast_id: str = Form(...), podcast_title: str = Form(...), feed_url: str = Form(...), artwork_url: str = Form(...), q: str = Form(None), db: AsyncSession = Depends(get_db)):
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
    if q:
        url = f"/search?q={q}&msg={message}"
    else:
        url = f"/podcast/{podcast_id}?feed_url={feed_url}&title={podcast_title}&artwork={artwork_url}&msg={message}"
    response = RedirectResponse(url=url, status_code=status.HTTP_302_FOUND)
    return response

@app.post("/unsubscribe")
async def unsubscribe(
    request: Request,
    podcast_id: str = Form(...),
    feed_url: str = Form(None),
    title: str = Form(None),
    artwork: str = Form(None),
    q: str = Form(None),
    db: AsyncSession = Depends(get_db)
):
    user_id = "default"
    await db.execute(
        Subscription.__table__.delete().where(
            (Subscription.user_id == user_id) & (Subscription.podcast_id == podcast_id)
        )
    )
    await db.commit()
    message = "Unsubscribed successfully."
    if q:
        url = f"/search?q={q}&msg={message}"
    elif feed_url and title and artwork:
        url = f"/podcast/{podcast_id}?feed_url={feed_url}&title={title}&artwork={artwork}&msg={message}"
    else:
        url = f"/subscriptions?msg={message}"
    response = RedirectResponse(url=url, status_code=status.HTTP_302_FOUND)
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
