from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from .models import Subscription

async def is_user_subscribed(db, user_id: str, podcast_id: str):
    sub_result = await db.execute(
        select(Subscription).where((Subscription.user_id == user_id) & (Subscription.podcast_id == podcast_id))
    )
    return sub_result.scalar() is not None

async def subscribe(db, user_id: str, podcast_id: str, podcast_title: str, feed_url: str, artwork_url: str):
    sub = Subscription(user_id=user_id, podcast_id=podcast_id, podcast_title=podcast_title, feed_url=feed_url, artwork_url=artwork_url)
    db.add(sub)
    try:
        await db.commit()
        return True, "Subscribed successfully!"
    except IntegrityError:
        await db.rollback()
        return False, "You are already subscribed to this podcast."
    except Exception:
        await db.rollback()
        return False, "An error occurred while subscribing."

async def unsubscribe(db, user_id: str, podcast_id: str):
    result = await db.execute(
        select(Subscription).where((Subscription.user_id == user_id) & (Subscription.podcast_id == podcast_id))
    )
    sub = result.scalar()
    if sub:
        await db.delete(sub)
        await db.commit()
        return True
    return False
