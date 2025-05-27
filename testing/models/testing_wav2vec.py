import librosa
import torch
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor
import logging


class Wav2Vec2Model:
    def __init__(self, model_variant: str = "large"):
        logging.getLogger("torch").setLevel(logging.ERROR)
        if model_variant == "large":
            model_name = "facebook/wav2vec2-large-960h-lv60-self"
        elif model_variant == "base":
            model_name = "facebook/wav2vec2-base-960h"
        else:
            raise ValueError("Unknown model variant. Use 'large' or 'base'.")

        self.processor = Wav2Vec2Processor.from_pretrained(model_name)
        self.model = Wav2Vec2ForCTC.from_pretrained(model_name)

    def transcribe(self, file: str) -> str:
        # Check if file exists
        try:
            with open(file):
                pass
        except FileNotFoundError:
            return None

        input_audio, _ = librosa.load(file, sr=16000)
        input_values = self.processor(input_audio, sampling_rate=16000, return_tensors="pt").input_values
        logits = self.model(input_values).logits
        predicted_ids = torch.argmax(logits, dim=-1)
        text: str = self.processor.batch_decode(predicted_ids)[0]
        text = text.lower()

        return text