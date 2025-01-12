import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
import requests

# ✅ Initialize Hugging Face API Key
HUGGINGFACE_API_KEY = "Your API key"
API_URL = "https://api-inference.huggingface.co/models/"  # Generic API endpoint
HEADERS = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}

# ✅ Initialize the Tkinter App
app = tk.Tk()
app.title("Hugging Face Sentiment Analysis & Summarization")
app.geometry("600x500")

# Global data variable
data = None

# ✅ Function: Upload CSV
def upload_csv():
    global data
    file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    if file_path:
        data = pd.read_csv(file_path)
        messagebox.showinfo("Success", f"CSV loaded with {len(data)} rows!")
    else:
        messagebox.showerror("Error", "Failed to load CSV")

# ✅ Function: Perform Theme Search
def theme_search():
    global data
    if data is None:
        messagebox.showerror("Error", "Please upload a CSV first!")
        return

    theme = theme_entry.get()
    keywords = keywords_entry.get().split(",")
    keywords = [kw.strip().lower() for kw in keywords]

    data['Theme_Match'] = data['Comment'].apply(lambda x: any(kw in x.lower() for kw in keywords))
    theme_count = data['Theme_Match'].sum()

    messagebox.showinfo("Theme Search", f"{theme}: Found in {theme_count} comments!")

# ✅ Function: Sentiment Analysis (Hugging Face API Call)
def sentiment_analysis(theme_only=False):
    global data
    if data is None:
        messagebox.showerror("Error", "Please upload a CSV first!")
        return

    model = "distilbert-base-uncased-finetuned-sst-2-english"
    comments = data[data['Theme_Match']]['Comment'].tolist() if theme_only else data['Comment'].tolist()
    sentiments = []

    try:
        for comment in comments:
            # ✅ Limit Comment Length to Avoid API Errors
            if len(comment) > 512:
                comment = comment[:512] + "..."  # Truncate long comments

            payload = {"inputs": comment}
            response = requests.post(f"https://api-inference.huggingface.co/models/{model}", headers=HEADERS, json=payload)
            
            # ✅ Handle Error Responses
            if response.status_code != 200:
                messagebox.showerror("Error", f"API Error: {response.status_code}\n{response.json()}")
                return

            # ✅ Validate Response Structure
            result = response.json()
            if isinstance(result, list) and len(result) > 0 and 'label' in result[0][0]:
                sentiment_label = result[0][0]['label']
                sentiments.append(sentiment_label)
            else:
                messagebox.showerror("Error", "Unexpected API response format.")
                return

        if theme_only:
            data.loc[data['Theme_Match'], 'Theme_Sentiment'] = sentiments
        else:
            data['Sentiment'] = sentiments

        sentiment_counts = pd.Series(sentiments).value_counts().to_dict()
        messagebox.showinfo("Sentiment Analysis", f"Results:\n{sentiment_counts}")

    except Exception as e:
        messagebox.showerror("Error", f"Error during sentiment analysis: {str(e)}")

# ✅ Function: Summarize Comments (Hugging Face API Call)
def summarize_comments(theme_only=False):
    global data
    if data is None:
        messagebox.showerror("Error", "Please upload a CSV first!")
        return

    model = "facebook/bart-large-cnn"
    comments = data[data['Theme_Match']]['Comment'].tolist() if theme_only else data['Comment'].tolist()
    combined_text = " ".join(comments)

    try:
        # ✅ Limit Text Length to Avoid API Error
        if len(combined_text) > 1000:
            combined_text = combined_text[:1000] + "..."  # Truncate input

        payload = {
            "inputs": combined_text,
            "parameters": {"max_length": 200, "min_length": 50}
        }
        response = requests.post(f"https://api-inference.huggingface.co/models/{model}", headers=HEADERS, json=payload)
        
        # ✅ Error Handling for API Response
        if response.status_code != 200:
            messagebox.showerror("Error", f"API Error: {response.status_code}\n{response.json()}")
            return

        # ✅ Response Validation
        result = response.json()
        if isinstance(result, list) and 'summary_text' in result[0]:
            summary = result[0]['summary_text']
        else:
            summary = "No summary available."

        # ✅ Store Summary in DataFrame
        if theme_only:
            data.loc[data['Theme_Match'], 'Theme_Summary'] = summary
        else:
            data['Summary'] = summary

        messagebox.showinfo("Summary", f"Summary: {summary}")

    except Exception as e:
        messagebox.showerror("Error", f"Error during summarization: {str(e)}")


# ✅ Function: Export Results to Excel
def export_results(theme_only=False):
    global data
    if data is None:
        messagebox.showerror("Error", "No data to export!")
        return

    export_path = filedialog.asksaveasfilename(defaultextension=".xlsx")
    try:
        with pd.ExcelWriter(export_path) as writer:
            if theme_only:
                theme_data = data[data['Theme_Match']]
                theme_data.to_excel(writer, sheet_name="Theme Comments", index=False)
                sentiment_summary = theme_data['Theme_Sentiment'].value_counts().to_frame(name='Count')
                sentiment_summary.to_excel(writer, sheet_name="Theme Sentiment Breakdown")
                theme_summary = theme_data.iloc[0]['Theme_Summary'] if 'Theme_Summary' in theme_data.columns else "No Summary Available"
                pd.DataFrame({"Theme Summary": [theme_summary]}).to_excel(writer, sheet_name="Theme Summary", index=False)
            else:
                data.to_excel(writer, sheet_name="All Comments", index=False)
                sentiment_summary = data['Sentiment'].value_counts().to_frame(name='Count')
                sentiment_summary.to_excel(writer, sheet_name="Sentiment Breakdown")
                summary = data.iloc[0]['Summary'] if 'Summary' in data.columns else "No Summary Available"
                pd.DataFrame({"Overall Summary": [summary]}).to_excel(writer, sheet_name="All Comments Summary", index=False)

        messagebox.showinfo("Export Success", f"Results exported successfully to {export_path}!")
    except Exception as e:
        messagebox.showerror("Error", f"Error exporting results: {str(e)}")

# ✅ Tkinter GUI Layout
upload_button = tk.Button(app, text="Upload CSV", command=upload_csv)
upload_button.pack(pady=10)

theme_label = tk.Label(app, text="Enter Theme:")
theme_label.pack()
theme_entry = tk.Entry(app)
theme_entry.pack(pady=5)

keywords_label = tk.Label(app, text="Enter Keywords (comma-separated):")
keywords_label.pack()
keywords_entry = tk.Entry(app)
keywords_entry.pack(pady=5)

theme_search_button = tk.Button(app, text="Perform Theme Search", command=theme_search)
theme_search_button.pack(pady=10)

theme_sentiment_button = tk.Button(app, text="Theme Sentiment Analysis", command=lambda: sentiment_analysis(theme_only=True))
theme_sentiment_button.pack(pady=10)

theme_summary_button = tk.Button(app, text="Theme Summarization", command=lambda: summarize_comments(theme_only=True))
theme_summary_button.pack(pady=10)

export_theme_button = tk.Button(app, text="Export Theme Results", command=lambda: export_results(theme_only=True))
export_theme_button.pack(pady=10)

sentiment_button = tk.Button(app, text="Sentiment Analysis (All Comments)", command=lambda: sentiment_analysis(theme_only=False))
sentiment_button.pack(pady=10)

summarize_button = tk.Button(app, text="Summarize All Comments", command=lambda: summarize_comments(theme_only=False))
summarize_button.pack(pady=10)

export_button = tk.Button(app, text="Export All Results", command=lambda: export_results(theme_only=False))
export_button.pack(pady=10)

# ✅ Run the Tkinter Event Loop
app.mainloop()
