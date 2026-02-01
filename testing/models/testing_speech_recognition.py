import speech_recognition

class SpeechRecognitionModel:
    def __init__(self, model:str = "google"):
        self.recognizer = speech_recognition.Recognizer()
        self.model = model
        print(f"Using model: {self.model}")

    def transcribe(self, file: str) -> str:
        with speech_recognition.AudioFile(file) as source:
            audio = self.recognizer.record(source)
            try:
                if self.model == "google":
                    # Try Czech first, then English as fallback
                    try:
                        text: str = self.recognizer.recognize_google(audio, language="cs-CZ", show_all=False)
                    except speech_recognition.UnknownValueError:
                        text: str = self.recognizer.recognize_google(audio, language="en-US", show_all=False)
                elif self.model == "whisper":
                    text: str = self.recognizer.recognize_whisper(audio, language="czech")
                elif self.model == "sphinx":
                    text: str = self.recognizer.recognize_sphinx(audio, show_all=False)
                else:
                    print("Model not supported")
                    return None
                text = text.lower()
            except speech_recognition.UnknownValueError:
                # Cannot understand the audio - too noisy or unclear
                print(f"UnknownValueError: Could not understand audio in file {file}")
                text = None
            except Exception as e:
                print(f"An error occurred: {e}")
                text = None
            
            return text