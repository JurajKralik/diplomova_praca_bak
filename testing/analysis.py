import json
import os
import pandas as pd
import matplotlib.pyplot as plt
from tkinter import filedialog

def load_results(json_path):
    with open(json_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    if "average_WER" in data[-1]:
        data.pop()

    df = pd.DataFrame(data)
    return df

def select_multiple_files():
    print("Select the evaluated JSON files for each model:")
    file_paths = filedialog.askopenfilenames(filetypes=[("JSON files", "*.json")])
    if not file_paths:
        print("No files selected. Exiting.")
        exit()
    return file_paths

def process_file(file_path):
    df = load_results(file_path)
    model_name = os.path.splitext(os.path.basename(file_path))[0]
    return model_name, df

def summarize_model(model_name, df):
    return {
        "model": model_name,
        "average_WER": df["WER"].mean(),
        "average_CER": df["CER"].mean(),
        "average_inference_time": df["inference_time"].mean(),
        "total_files": len(df)
    }

def plot_model_comparison(summary_df, metric):
    plt.figure(figsize=(10, 6))
    plt.bar(summary_df["model"], summary_df[metric])
    plt.xlabel("Model")
    plt.ylabel(metric.replace("_", " ").capitalize())
    plt.title(f"Comparison of {metric.replace('_', ' ').capitalize()} across models")
    plt.xticks(rotation=45)
    plt.grid(axis="y")
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    file_paths = select_multiple_files()

    summaries = []
    for file_path in file_paths:
        model_name, df = process_file(file_path)
        summary = summarize_model(model_name, df)
        summaries.append(summary)

    summary_df = pd.DataFrame(summaries)

    print("\nSummary statistics for all models:")
    print(summary_df)

    output_folder = os.path.join(os.path.dirname(__file__), "analysis_output")
    os.makedirs(output_folder, exist_ok=True)

    summary_csv_path = os.path.join(output_folder, "models_summary.csv")
    summary_df.to_csv(summary_csv_path, index=False)
    print(f"\nSummary saved to {summary_csv_path}")

    plot_model_comparison(summary_df, "average_WER")
    plot_model_comparison(summary_df, "average_CER")
    plot_model_comparison(summary_df, "average_inference_time")
