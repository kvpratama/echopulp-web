from podcast.utils import download_audio, delete_file
from services.transcriber_service import HFTranscriber
from services.summarizer_service import HuggingFaceSummarizer
from podcast.async_db import save_transcription_and_summary_async
from database import get_db
import tempfile
import asyncio

async def process_podcast_summary(
    audio_url: str, episode_id: str, podcast_id=None, episode_title=None, episode_description=None, podcast_title=None, podcast_image_url=None, publish_date=None, duration=None, db=None
):
    """
    Downloads, transcribes, summarizes, saves, and cleans up a podcast episode.
    """
    transcriber = HFTranscriber()
    summarizer = HuggingFaceSummarizer()

    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
        audio_path = tmp.name
    try:
        download_audio(audio_url, audio_path)
        transcript = transcriber.transcribe(audio_path)
        summary = summarizer.summarize(transcript)
        # Use provided db or get a new one
        if db is None:
            from database import SessionLocal
            async with SessionLocal() as session:
                await save_transcription_and_summary_async(
                    session,
                    episode_id, transcript, summary,
                    podcast_id=podcast_id,
                    episode_title=episode_title,
                    episode_description=episode_description,
                    podcast_title=podcast_title,
                    podcast_image_url=podcast_image_url,
                    publish_date=publish_date,
                    duration=duration,
                    audio_url=audio_url
                )
        else:
            await save_transcription_and_summary_async(
                db,
                episode_id, transcript, summary,
                podcast_id=podcast_id,
                episode_title=episode_title,
                episode_description=episode_description,
                podcast_title=podcast_title,
                podcast_image_url=podcast_image_url,
                publish_date=publish_date,
                duration=duration,
                audio_url=audio_url
            )
    finally:
        delete_file(audio_path)
