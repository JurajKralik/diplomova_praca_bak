import csv
import json
import os
from tkinter import filedialog
from jiwer import wer, cer, Compose, ToLowerCase, RemovePunctuation, RemoveMultipleSpaces, Strip

SUBSTITUTIONS = {
	"&": "and",
	"@": "at",
	"#": "number",
	"$": "dollar",
	"%": "percent",
	"€": "euro",
	"£": "pound",
	"¢": "cent",
}

transform = Compose([
    ToLowerCase(),
    RemovePunctuation(),
    RemoveMultipleSpaces(),
    Strip()
])

def get_sentence_for_file(tsv_path, target_filename):
	with open(tsv_path, "r", encoding="utf-8") as infile:
		reader = csv.DictReader(infile, delimiter="\t")
		for row in reader:
			if row["path"].strip() == target_filename:
				return row["sentence"]
	return None

def get_additional_info_for_file(tsv_path, target_filename):
	with open(tsv_path, "r", encoding="utf-8") as infile:
		reader = csv.DictReader(infile, delimiter="\t")
		for row in reader:
			if row["path"].strip() == target_filename:
				return {
					"age": row.get("age", "").strip(),
					"gender": row.get("gender", "").strip(),
					"accents": row.get("accents", "").strip(),
				}
	return {"age": None, "gender": None, "accents": None}

def get_file_paths() -> tuple:
	print("Please select the validated TSV file:")
	validated_tsv = filedialog.askopenfile()
	if not validated_tsv:
		print("No input file selected.")
		exit()

	print("Please select the result JSON file:")
	result_json = filedialog.askopenfile()
	if not result_json:
		print("No output file selected.")
		exit()

	output_folder = os.path.join(os.path.dirname(__file__), "output")
	os.makedirs(output_folder, exist_ok=True)

	result_json_name = os.path.basename(result_json.name)
	output_json_path = os.path.join(output_folder, f"evaluated_{result_json_name}")

	return validated_tsv, result_json, output_json_path

def substitute_symbols(text):
	for symbol, word in SUBSTITUTIONS.items():
		text = text.replace(symbol, f" {word} ")
	return text

def normalize_text(text):
	if text is None:
		return ""
	text = substitute_symbols(text)
	text = transform(text)
	return text

def compare_result(validated_tsv, result) -> dict:
	file_name = result.get("file_name", "")
	mp3_file_name = file_name.replace(".wav", ".mp3")
	sentence = get_sentence_for_file(validated_tsv.name, mp3_file_name)
	transcript = result.get("transcript", "")
	inference_time = result.get("time_taken", None)
	
	if sentence is None or transcript is None:
		print(f"Evaluating file: {file_name} - Missing reference or transcription.")
		return {
			"file_name": file_name,
			"sentence": sentence,
			"transcript": transcript,
			"inference_time": inference_time,
			"WER": None,
			"CER": None
		}
	else:
		ref_norm = normalize_text(sentence)
		hyp_norm = normalize_text(transcript)

		wer_score = wer(ref_norm, hyp_norm)
		cer_score = cer(ref_norm, hyp_norm)

		print(f"Evaluating file: {file_name} - WER: {wer_score:.2%}, CER: {cer_score:.2%}")

		return {
			"file_name": file_name,
			"sentence": sentence,
			"transcript": transcript,
			"inference_time": inference_time,
			"WER": wer_score,
			"CER": cer_score
		}

if __name__ == "__main__":
	validated_tsv, result_json, output_json_path = get_file_paths()

	with open(result_json.name, "r", encoding="utf-8") as full_file:
		full_data = json.load(full_file)

	results = full_data.get("results", [])
	model_name = full_data.get("model", "Unknown")
	parallel_processes = full_data.get("parallel_processes", None)
	total_time_taken = full_data.get("total_time_taken", None)

	evaluation = []

	for result in results:
		evaluated = compare_result(validated_tsv, result)
		mp3_file_name = result["file_name"].replace(".wav", ".mp3")
		additional_info = get_additional_info_for_file(validated_tsv.name, mp3_file_name)
		evaluated.update(additional_info)
		evaluation.append(evaluated)

	# Calculate averages
	wer_scores = [item["WER"] for item in evaluation if item["WER"] is not None]
	cer_scores = [item["CER"] for item in evaluation if item["CER"] is not None]
	average_wer = sum(wer_scores) / len(wer_scores) if wer_scores else 0.0
	average_cer = sum(cer_scores) / len(cer_scores) if cer_scores else 0.0

	# Final output dictionary
	final_output = {
		"evaluation": evaluation,
		"summary": {
			"model": model_name,
			"parallel_processes": parallel_processes,
			"total_time_taken": total_time_taken,
			"average_WER": average_wer,
			"average_CER": average_cer
		}
	}

	with open(output_json_path, "w", encoding="utf-8") as outfile:
		json.dump(final_output, outfile, ensure_ascii=False, indent=4)

	print(f"\nEvaluation + summary saved to {output_json_path}")