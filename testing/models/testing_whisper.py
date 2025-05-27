import whisper
import torch
import logging


class WhisperModel:
    def __init__(self):
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Using device: {device}")
        self.model = whisper.load_model("turbo", device=device)
        logging.getLogger("torch").setLevel(logging.ERROR)

    def transcribe(self, file_name: str) -> str:
        result = self.model.transcribe(file_name)
        return result["text"]