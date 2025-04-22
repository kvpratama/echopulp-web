from fastapi import APIRouter, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app_config import templates
from podcast.utils import fetch_podcast_episodes
from podcast.summary import process_podcast_summary
from subscriptions.crud import is_user_subscribed
from podcast.models import PodcastEpisode
from database import get_db
from podcast.schemas import PodcastSummaryRequest

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

@router.get("/my_summaries")
async def my_summaries(request: Request, db: AsyncSession = Depends(get_db)):
    from sqlalchemy.future import select
    result = await db.execute(select(PodcastEpisode))
    episodes = result.scalars().all()
    # Sort episodes by publish_date descending (newest first)
    def parse_date(episode):
        from datetime import datetime
        # Try to parse publish_date, fallback to min if not available
        date_str = getattr(episode, 'publish_date', None)
        if date_str:
            try:
                # Try ISO, RFC822, or just year-month-day
                for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%a, %d %b %Y %H:%M:%S %z"):
                    try:
                        return datetime.strptime(date_str, fmt)
                    except Exception:
                        continue
            except Exception:
                pass
        return datetime.min
    episodes = sorted(episodes, key=parse_date, reverse=True)
    return templates.TemplateResponse(
        "my_summaries.html",
        {"request": request, "summaries": episodes}
    )


@router.post("/summarize_podcast")
async def summarize_podcast(req: PodcastSummaryRequest, db: AsyncSession = Depends(get_db)):
    from sqlalchemy.future import select
    result = await db.execute(select(PodcastEpisode).where(PodcastEpisode.id == req.episode_id))
    episode = result.scalars().first()
    summary = episode.summary if episode else None
    transcription = episode.transcription if episode else None
    if summary and transcription:
        return {"status": "success", "summary": summary, "transcription": transcription}
    # If not found, process and then fetch again
    await process_podcast_summary(
        req.audio_url, req.episode_id,
        podcast_id=req.podcast_id,
        episode_title=req.episode_title,
        episode_description=req.episode_description,
        podcast_title=req.podcast_title,
        podcast_image_url=req.podcast_image_url,
        publish_date=req.publish_date,
        duration=req.duration,
        db=db
    )
    result = await db.execute(select(PodcastEpisode).where(PodcastEpisode.id == req.episode_id))
    episode = result.scalars().first()
    summary = episode.summary if episode else None
    transcription = episode.transcription if episode else None
    if summary and transcription:
        return {"status": "success", "summary": summary, "transcription": transcription}
    elif summary:
        return {"status": "success", "summary": summary}
    elif transcription:
        return {"status": "success", "transcription": transcription}
    else:
        return {"status": "success"}
