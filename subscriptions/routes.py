from fastapi import APIRouter, Request, Form, Depends, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database import get_db
from .crud import is_user_subscribed, subscribe, unsubscribe
from .models import Subscription
import asyncio
from datetime import datetime
from podcast.utils import get_latest_episode_date_async
from app_config import templates

router = APIRouter()

@router.get("/subscriptions")
async def subscriptions(request: Request, db: AsyncSession = Depends(get_db)):
    user_id = "default"
    result = await db.execute(select(Subscription).where(Subscription.user_id == user_id))
    subs = result.scalars().all()
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

@router.post("/subscribe")
async def subscribe_endpoint(request: Request, podcast_id: str = Form(...), podcast_title: str = Form(...), feed_url: str = Form(...), artwork_url: str = Form(...), q: str = Form(None), db: AsyncSession = Depends(get_db)):
    user_id = "default"
    success, message = await subscribe(db, user_id, podcast_id, podcast_title, feed_url, artwork_url)
    if q:
        url = f"/search?q={q}&msg={message}"
    else:
        url = f"/podcast/{podcast_id}?feed_url={feed_url}&title={podcast_title}&artwork={artwork_url}&msg={message}"
    return RedirectResponse(url=url, status_code=status.HTTP_302_FOUND)

@router.post("/unsubscribe")
async def unsubscribe_endpoint(request: Request, podcast_id: str = Form(...), feed_url: str = Form(None), title: str = Form(None), artwork: str = Form(None), q: str = Form(None), db: AsyncSession = Depends(get_db)):
    user_id = "default"
    await unsubscribe(db, user_id, podcast_id)
    if q:
        url = f"/search?q={q}"
    elif feed_url and title and artwork:
        url = f"/podcast/{podcast_id}?feed_url={feed_url}&title={title}&artwork={artwork}&msg=Unsubscribed+successfully."
    else:
        url = "/subscriptions?msg=Unsubscribed+successfully."
    return RedirectResponse(url=url, status_code=status.HTTP_302_FOUND)
