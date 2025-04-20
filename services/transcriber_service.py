from transformers import pipeline

class HFTranscriber:
    def __init__(self, model_name="openai/whisper-tiny"):
        self.transcriber = pipeline("automatic-speech-recognition", model=model_name, return_timestamps=True)

    def transcribe(self, audio_path: str) -> str:
        result = self.transcriber(audio_path)
        return result["text"]
