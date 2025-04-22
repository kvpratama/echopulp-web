from sqlalchemy.ext.asyncio import AsyncSession
from podcast.models import PodcastEpisode

async def save_transcription_and_summary_async(
    db: AsyncSession,
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
    await db.merge(episode)
    await db.commit()
