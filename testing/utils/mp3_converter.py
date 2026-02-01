from pydub import AudioSegment
import os
from tkinter import filedialog
import csv

validation_check = True

def convert_mp3_to_wav(input_folder, output_folder):
	os.makedirs(output_folder, exist_ok=True)

	folder_size = len(os.listdir(input_folder))
	current_file = 0
	
	for filename in os.listdir(input_folder):
		current_file += 1
		if filename.endswith('.mp3'):
			if validation_check:
				validated = False
				# Read the validated file paths from the TSV
				with open(validated_tsv.name, 'r', encoding='utf-8') as infile:
					reader = csv.DictReader(infile, delimiter='\t')
					for row in reader:
						if row['path'].strip() == filename:
							validated = True
							break

				if not validated:
					print(f"({current_file}/{folder_size}) File not validated: {filename}")
					continue

			mp3_path = os.path.join(input_folder, filename)
			wav_filename = os.path.splitext(filename)[0] + '.wav'
			wav_path = os.path.join(output_folder, wav_filename)

			# Load and convert
			audio = AudioSegment.from_mp3(mp3_path)
			audio.export(wav_path, format='wav')
			print(f"({current_file}/{folder_size}) Converted: {mp3_path} -> {wav_path} ")

# Prompt user for input and output directories
input_path = filedialog.askdirectory()
if not input_path:
    print("No input directory selected.")
    exit()

output_path = filedialog.askdirectory()
if not output_path:
    print("No output directory selected.")
    exit()

validated_tsv = filedialog.askopenfile()
if not validated_tsv:
	validation_check = False
convert_mp3_to_wav(input_path, output_path)
