from podcast.utils import download_audio, delete_file
from services.transcriber_service import HFTranscriber
from services.summarizer_service import HuggingFaceSummarizer
from podcast.models import save_transcription_and_summary

import tempfile

def process_podcast_summary(audio_url: str, episode_id: str):
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
        save_transcription_and_summary(episode_id, transcript, summary)
    finally:
        delete_file(audio_path)
