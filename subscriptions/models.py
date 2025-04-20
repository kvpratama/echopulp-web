from sqlalchemy import Column, Integer, String, DateTime, UniqueConstraint
from database import Base
from datetime import datetime

class Subscription(Base):
    __tablename__ = "subscriptions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    podcast_id = Column(String, index=True)
    podcast_title = Column(String)
    feed_url = Column(String)
    artwork_url = Column(String)
    date_subscribed = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint('user_id', 'podcast_id', name='uq_user_podcast'),)
