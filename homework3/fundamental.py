from flask import Flask, render_template, send_file
import pandas as pd
import os
from textblob import TextBlob

app = Flask(__name__)


def load_company_codes():
    try:
        # Path to the company_data.csv file
        csv_path = "data/company_data.csv"

        # Load the CSV file
        company_data = pd.read_csv(csv_path, low_memory=False)

        # Check if 'Company Code' column exists
        if 'CompanyCode' in company_data.columns:
            # Remove duplicates and clean data
            unique_company_codes = company_data['CompanyCode'].drop_duplicates().str.strip().str.lower().tolist()
            print("Unique Company Codes:", unique_company_codes)  # Debugging: Print unique codes
            return unique_company_codes
        else:
            print("Error: 'CompanyCode' column not found in the CSV file.")
            return []
    except FileNotFoundError:
        print("Error: company_data.csv not found!")
        return []


# Load company codes at startup
company_codes = load_company_codes()


# Load news articles from CSV file
def load_news():
    try:
        news_df = pd.read_csv("static/data/news_articles.csv")
        return news_df
    except FileNotFoundError:
        return pd.DataFrame(columns=["Title", "Link", "Published Date"])


# Perform sentiment analysis on a single article
def analyze_sentiment(text):
    if not isinstance(text, str) or text.strip() == "":
        return "neutral", 0.0

    blob = TextBlob(text)
    polarity = blob.sentiment.polarity

    if polarity > 0:
        return "positive", polarity
    elif polarity < 0:
        return "negative", polarity
    else:
        return "neutral", polarity


# Identify companies in the article (basic keyword matching for simplicity)
def identify_company(text):
    text = text.lower()
    for company in company_codes:
        if company in text:
            print(f"Matched '{company}' in title: {text}")  # Debugging: Log successful matches
            return company.upper()
    print(f"No match found for title: {text}")  # Debugging: Log unmatched titles
    return "Unknown"




# Perform fundamental analysis on news data
def perform_fundamental_analysis(news_df):
    results = []
    for _, row in news_df.iterrows():
        title = row.get("Title", "")
        sentiment, polarity = analyze_sentiment(title)
        company = identify_company(title)
        recommendation = (
            "Buy" if sentiment == "positive" else ("Sell" if sentiment == "negative" else "Hold")
        )

        results.append({
            "Company": company,
            "Title": title,
            "Sentiment": sentiment,
            "Polarity": round(polarity, 2),
            "Recommendation": recommendation,
        })
    return results


@app.route("/")
def news():
    news_df = load_news()
    return render_template("news.html", news=news_df.to_dict(orient="records"))


@app.route("/news_article.csv")
def get_csv():
    # Use an absolute path for reliability during debugging
    csv_path = os.path.join(os.path.dirname(__file__), "news_articles.csv")
    print("Serving CSV from:", csv_path)  # Debugging: Print full path

    try:
        return send_file(csv_path, as_attachment=False)
    except FileNotFoundError:
        print("CSV file not found!")  # Debugging: Log missing file error
        return "File not found", 404


@app.route("/analyze")
def analyze():
    news_df = load_news()
    results = perform_fundamental_analysis(news_df)
    return render_template("results.html", results=results)


if __name__ == "__main__":
    app.run(debug=True)
