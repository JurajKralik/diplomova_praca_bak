from models.testing_speech_recognition import SpeechRecognitionModel
from models.testing_whisper import WhisperModel
from models.testing_wav2vec import Wav2Vec2Model
import json
import os
import time
import argparse
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed

try:
    import tkinter as tk
    from tkinter import filedialog
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False


def save_transcription(
    output_path: str, file_name: str, transcript: str, elapsed_time: float
):
    """Saves transcription output to a JSON file with a unique serial number."""
    if not os.path.exists(output_path):
        with open(output_path, "w", encoding="utf-8") as json_file:
            json.dump({"results": []}, json_file, ensure_ascii=False, indent=4)

    with open(output_path, "r+", encoding="utf-8") as json_file:
        data = json.load(json_file)
        result_entry = {
            "file_name": file_name,
            "transcript": transcript,
            "time_taken": elapsed_time,
        }
        data["results"].append(result_entry)
        json_file.seek(0)
        json.dump(data, json_file, ensure_ascii=False, indent=4)
        json_file.truncate()


def transcribe_file(model_choice, audio_path, file_name):
    try:
        if model_choice == "Google":
            model = SpeechRecognitionModel(model="google")
        elif model_choice == "Whisper":
            model = SpeechRecognitionModel(model="whisper")
        elif model_choice == "Sphinx":
            model = SpeechRecognitionModel(model="sphinx")
        elif model_choice == "Whisper_openai":
            model = WhisperModel()
        elif model_choice == "Wav2Vec_large":
            model = Wav2Vec2Model(model_variant="large")
        elif model_choice == "Wav2Vec_base":
            model = Wav2Vec2Model(model_variant="base")
        else:
            raise ValueError("Invalid model choice.")

        start_time = time.time()
        transcript = model.transcribe(audio_path)
        elapsed_time = time.time() - start_time
        
        if transcript is None:
            print(f"Warning: {file_name} returned None transcript (audio might be unclear or model couldn't process it)")
        
        return {
            "file_name": file_name,
            "transcript": transcript,
            "time_taken": elapsed_time,
        }
    except Exception as e:
        print(f"Error processing {file_name}: {e}")
        import traceback
        traceback.print_exc()
        return {
            "file_name": file_name,
            "transcript": None,
            "time_taken": 0,
            "error": str(e)
        }

def transcribe(audio_folder: str, model_choice: str, parallel_processes: int = 1):
    """
    Transcribe audio files from a folder using the specified model.
    
    Args:
        audio_folder: Path to folder containing audio files
        model_choice: Model to use (Google, Whisper, Sphinx, Whisper_openai, Wav2Vec_base, Wav2Vec_large)
        parallel_processes: Number of parallel processes to use (default: 1)
    """
    if not audio_folder or not os.path.exists(audio_folder):
        print(f"Error: Audio folder '{audio_folder}' does not exist.")
        return

    output_dir = "testing/output/output.json"
    serial_number = 1
    while os.path.exists(output_dir):
        base, ext = os.path.splitext("testing/output/output")
        output_dir = f"{base}_{serial_number}{ext}.json"
        serial_number += 1

    print(f"Output will be saved to: {output_dir}")
    print(f"Model: {model_choice}")
    print(f"Parallel processes: {parallel_processes}")

    output = {
        "model": model_choice,
        "parallel_processes": parallel_processes,
        "results": [],
    }
    with open(output_dir, "w", encoding="utf-8") as json_file:
        json.dump(output, json_file, ensure_ascii=False, indent=4)

    total_time_start = time.time()

    audio_files = [
        file_name
        for file_name in os.listdir(audio_folder)
        if file_name.lower().endswith((".wav", ".mp3", ".flac"))
    ]
    folder_size = len(audio_files)
    
    if folder_size == 0:
        print(f"No audio files found in {audio_folder}")
        return

    print(f"Found {folder_size} audio files to process")

    # Use multiprocessing
    futures = []
    with ProcessPoolExecutor(max_workers=parallel_processes) as executor:
        for file_name in audio_files:
            full_path = os.path.join(audio_folder, file_name)
            futures.append(
                executor.submit(transcribe_file, model_choice, full_path, file_name)
            )

        for idx, future in enumerate(as_completed(futures), 1):
            result_entry = future.result()
            save_transcription(
                output_dir,
                result_entry["file_name"],
                result_entry["transcript"],
                result_entry["time_taken"],
            )
            print(
                f"({idx}/{folder_size}) {result_entry['file_name']} done in {result_entry['time_taken']:.2f}s"
            )

    total_time_taken = time.time() - total_time_start
    with open(output_dir, "r+", encoding="utf-8") as json_file:
        data = json.load(json_file)
        data["total_time_taken"] = total_time_taken
        json_file.seek(0)
        json.dump(data, json_file, ensure_ascii=False, indent=4)
        json_file.truncate()

    print(f"Done! Total time taken: {total_time_taken:.2f} seconds")
    print(f"Results saved to: {output_dir}")
    return output_dir


def start_gui():
    """Start the GUI version of the application"""
    if not GUI_AVAILABLE:
        print("Error: tkinter is not available. Please use CLI mode or install tkinter.")
        return
    
    def select_folder():
        new_path = filedialog.askdirectory()
        if new_path:
            folder_path.set(new_path)
    
    def transcribe_gui():
        audio_folder = folder_path.get()
        if not audio_folder:
            result_text.set("Please select an audio folder.")
            return
        
        model_choice = model_var.get()
        parallel_processes = process_var.get()
        
        result_text.set("Processing...")
        root.update()
        
        try:
            output_file = transcribe(audio_folder, model_choice, parallel_processes)
            result_text.set(f"Done! Results saved to: {output_file}")
        except Exception as e:
            result_text.set(f"Error: {str(e)}")
    
    root = tk.Tk()
    root.title("Speech Recognition GUI")
    root.geometry("400x450")

    folder_path = tk.StringVar()
    model_var = tk.StringVar(value="Google")
    result_text = tk.StringVar()
    padding_x = 25

    # File selection button
    folder_button = tk.Button(root, text="Select Folder", command=select_folder)
    folder_button.pack(pady=10)
    folder_button.config(width=int(padding_x/2))

    folder_label = tk.Label(root, textvariable=folder_path, wraplength=500)
    folder_label.pack(pady=5)
    folder_label.config(width=50)

    # Model selection
    model_frame = tk.LabelFrame(root, text="Select Model")
    model_frame.pack(pady=10)
    model_frame.config(padx=padding_x)

    for model in ["Google", "Whisper", "Sphinx", "Whisper_openai", "Wav2Vec_base", "Wav2Vec_large"]:
        tk.Radiobutton(model_frame, text=model, variable=model_var, value=model).pack(
            anchor="w"
        )

    # Parallel processes selection
    process_frame = tk.LabelFrame(root, text="Parallel")
    process_frame.pack(pady=10)
    process_frame.config(padx=padding_x)

    max_processes = 61
    process_var = tk.IntVar(value=1)
    tk.Scale(
        process_frame,
        from_=1,
        to=max_processes,
        orient="horizontal",
        variable=process_var,
        label="Processes",
    ).pack()
    
    # Transcribe button
    transcribe_button = tk.Button(root, text="Transcribe", command=transcribe_gui)
    transcribe_button.pack(pady=10)
    transcribe_button.config(width=int(padding_x/2))
    
    # Result label
    result_label = tk.Label(root, textvariable=result_text, wraplength=350, fg="blue")
    result_label.pack(pady=10)

    root.mainloop()


if __name__ == "__main__":
    # Check if any command-line arguments were provided
    if len(sys.argv) > 1:
        # CLI mode
        parser = argparse.ArgumentParser(description="Transcribe audio files using various speech recognition models")
        parser.add_argument("--folder", "-f", type=str, required=True, help="Path to folder containing audio files")
        parser.add_argument(
            "--model", "-m", type=str, required=True,
            choices=["Google", "Whisper", "Sphinx", "Whisper_openai", "Wav2Vec_base", "Wav2Vec_large"],
            help="Model to use for transcription"
        )
        parser.add_argument(
            "--processes", "-p", type=int, default=1,
            help="Number of parallel processes (default: 1)"
        )
        
        args = parser.parse_args()
        transcribe(args.folder, args.model, args.processes)
    else:
        # GUI mode
        start_gui()
