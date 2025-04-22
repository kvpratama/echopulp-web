from fastapi import APIRouter, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app_config import templates
from podcast.utils import fetch_podcast_episodes
from podcast.summary import process_podcast_summary
from subscriptions.crud import is_user_subscribed
from podcast.models import PodcastEpisode, get_engine
from sqlalchemy.orm import sessionmaker
from database import get_db
from pydantic import BaseModel

router = APIRouter()

@router.get("/podcast/{podcast_id}")
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
    episode_id: str
    audio_url: str

@router.post("/summarize_podcast")
async def summarize_podcast(req: PodcastSummaryRequest):
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
