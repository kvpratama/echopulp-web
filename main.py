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
import feedparser
from datetime import datetime
from podcast.summary import process_podcast_summary
from pydantic import BaseModel
from podcast.models import PodcastEpisode, get_engine
from sqlalchemy.orm import sessionmaker


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

async def get_latest_episode_date_async(feed_url):
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(feed_url)
            if resp.status_code != 200:
                return None
            content = resp.content
        parsed = feedparser.parse(content)
        entries = parsed.entries
        if not entries:
            return None
        latest = max(
            entries,
            key=lambda e: e.get("published_parsed") or e.get("updated_parsed") or 0
        )
        dt = latest.get("published_parsed") or latest.get("updated_parsed")
        if dt:
            return datetime(*dt[:6])
    except Exception:
        pass
    return None

@app.get("/subscriptions")
async def subscriptions(request: Request, db: AsyncSession = Depends(get_db)):
    user_id = "default"
    result = await db.execute(select(Subscription).where(Subscription.user_id == user_id))
    subs = result.scalars().all()

    # Fetch latest_episode_date for all subscriptions in parallel using asyncio.gather
    async def attach_latest(sub):
        sub.latest_episode_date = await get_latest_episode_date_async(sub.feed_url)
        return sub

    subs = await asyncio.gather(*(attach_latest(sub) for sub in subs))
    subs.sort(key=lambda s: s.latest_episode_date or datetime.min, reverse=True)

    msg = request.query_params.get("msg", None)
    return templates.TemplateResponse(
        "subscriptions.html",
        {"request": request, "subs": subs, "msg": msg}
    )

class PodcastSummaryRequest(BaseModel):
    audio_url: str
    episode_id: str

@app.post("/summarize_podcast")
async def summarize_podcast(req: PodcastSummaryRequest):
    # Try to fetch the summary from the DB first
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    session = Session()
    episode = session.query(PodcastEpisode).filter_by(id=req.episode_id).first()
    summary = episode.summary if episode else None
    transcription = episode.transcription if episode else None
    session.close()
    if summary and transcription:
        return {"status": "success", "summary": summary, "transcription": transcription}
    # If not found, process and then fetch again
    process_podcast_summary(req.audio_url, req.episode_id)
    session = Session()
    episode = session.query(PodcastEpisode).filter_by(id=req.episode_id).first()
    summary = episode.summary if episode else None
    transcription = episode.transcription if episode else None
    session.close()
    if summary and transcription:
        return {"status": "success", "summary": summary, "transcription": transcription}
    elif summary:
        return {"status": "success", "summary": summary}
    elif transcription:
        return {"status": "success", "transcription": transcription}
    else:
        return {"status": "success"}

if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)
