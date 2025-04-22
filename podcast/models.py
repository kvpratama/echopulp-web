# Example using SQLAlchemy
from sqlalchemy import Column, String, Text
from database import Base

class PodcastEpisode(Base):
    __tablename__ = 'podcast_episodes'
    id = Column(String, primary_key=True)
    podcast_id = Column(String)
    episode_title = Column(String)
    episode_description = Column(Text)
    podcast_title = Column(String)
    podcast_image_url = Column(String)
    publish_date = Column(String)
    duration = Column(String)
    audio_url = Column(String)
    transcription = Column(Text)
    summary = Column(Text)

def save_transcription_and_summary(
    episode_id, transcription, summary,
    podcast_id=None, episode_title=None, episode_description=None,
    podcast_title=None, podcast_image_url=None, publish_date=None,
    duration=None, audio_url=None
):
    episode = PodcastEpisode(
        id=episode_id,
        podcast_id=podcast_id,
        episode_title=episode_title,
        episode_description=episode_description,
        podcast_title=podcast_title,
        podcast_image_url=podcast_image_url,
        publish_date=publish_date,
        duration=duration,
        audio_url=audio_url,
        transcription=transcription,
        summary=summary
    )
    # Use async session from database.py here
