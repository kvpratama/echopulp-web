from pydantic import BaseModel

class PodcastSummaryRequest(BaseModel):
    episode_id: str
    audio_url: str
    podcast_id: str = None
    episode_title: str = None
    episode_description: str = None
    podcast_title: str = None
    podcast_image_url: str = None
    publish_date: str = None
    duration: str = None
