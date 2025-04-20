import uvicorn
from fastapi import FastAPI, Request, Form, Depends, status
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from database import SessionLocal, engine, Base
from subscriptions.models import Subscription
from podcast.summary import process_podcast_summary
from pydantic import BaseModel
from podcast.models import PodcastEpisode, get_engine
from sqlalchemy.orm import sessionmaker
from podcast.utils import fetch_podcast_episodes
from subscriptions.routes import router as subscriptions_router
from subscriptions.crud import is_user_subscribed
from app_config import templates

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(subscriptions_router)

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
    is_subscribed = await is_user_subscribed(db, user_id, podcast_id)
    episodes = await fetch_podcast_episodes(feed_url)
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
