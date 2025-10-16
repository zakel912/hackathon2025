import requests
import pandas as pd
from datetime import datetime, timedelta
import time
import yfinance as yf
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import plotly.express as px



API_KEY = "834f03716cde446aa51357c67ca13ab2"

companies = {
    "AAPL": "Apple",
    "MSFT": "Microsoft",
    "AMZN": "Amazon",
    "GOOGL": "Google OR Alphabet",
    "TSLA": "Tesla",
    "MC.PA": "LVMH OR Moet Hennessy",
    "TTE.PA": "TotalEnergies",
    "SAN.PA": "Sanofi",
    "AIR.PA": "Airbus",
    "SU.PA": "Schneider Electric"
}

end_date = datetime.today()
start_date = end_date - timedelta(days=30)
from_date = start_date.strftime("%Y-%m-%d")
to_date = end_date.strftime("%Y-%m-%d")

print(f"📰 Collecting news from {from_date} to {to_date}...")


all_articles = []

for ticker, name in companies.items():
    query = f"{ticker} OR {name}"
    # query = f'("{ticker}" OR "{name}") AND (stock OR share OR market OR price OR earnings OR profit)'
    url = (
        f"https://newsapi.org/v2/everything?"
        f"q={query}&"
        f"from={from_date}&"
        f"to={to_date}&"
        f"sortBy=publishedAt&"
        f"language=en&"
        f"pageSize=100&"
        f"apiKey={API_KEY}"
    )

    response = requests.get(url)
    if response.status_code != 200:
        print(f"❌ Error fetching {name}: {response.status_code}")
        continue

    data = response.json()
    articles = data.get("articles", [])
    for article in articles:
        title = article.get("title", "")
        desc = article.get("description", "")
        text = f"{title}. {desc}".strip()

        if not text:
            continue

        all_articles.append({
            "Company": name,
            "Text": text,
            "URL": article.get("url"),
            "PublishedAt": article.get("publishedAt")
        })
    time.sleep(1)  # éviter rate limit

df = pd.DataFrame(all_articles)
print(f"✅ {len(df)} articles collected.\n")

if df.empty:
    raise ValueError("No articles collected. Check your API key or query terms.")


print("🔍 Loading FinBERT model...")
MODEL_NAME = "yiyanghkust/finbert-tone"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)


def analyze_sentiment(text):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
    with torch.no_grad():
        outputs = model(**inputs)
        probs = F.softmax(outputs.logits, dim=1)
        sentiment_labels = ["positive", "neutral", "negative"]
        sentiment_idx = torch.argmax(probs, dim=1).item()
        return sentiment_labels[sentiment_idx], probs[0][sentiment_idx].item()

print("🧠 Running sentiment analysis...")
sentiments = [analyze_sentiment(t) for t in df["Text"]]

df["Sentiment"] = [s[0] for s in sentiments]
df["SentimentScore"] = [s[1] for s in sentiments]

df["PublishedAt"] = pd.to_datetime(df["PublishedAt"])
df.to_csv("news_sentiment_raw.csv", index=False)
print("✅ Sentiment analysis completed and saved.\n")


daily_sent = (
    df.groupby(["Company", df["PublishedAt"].dt.date])
    .agg(MeanSentimentScore=("SentimentScore", "mean"))
    .reset_index()
)

print("📊 Downloading market data...")
corr_results = []
merged_data = []

for company in companies:
    try:
        stock = yf.download(company, start=from_date, end=to_date, progress=False)
        if stock.empty:
            continue
        stock["Return"] = stock["Close"].pct_change()
        stock = stock.reset_index()[["Date", "Return"]]

        company_sent = daily_sent[daily_sent["Company"] == company]
        merged = pd.merge(
            company_sent, stock, left_on="PublishedAt", right_on="Date", how="inner"
        )
        merged["Company"] = company

        corr = merged["MeanSentimentScore"].corr(merged["Return"])
        corr_results.append({"Company": company, "Correlation": corr})
        merged_data.append(merged)
    except Exception as e:
        print(f"⚠️ Error with {company}: {e}")

corr_df = pd.DataFrame(corr_results)
print("\n📉 Correlations between sentiment & return:")
print(corr_df)


if merged_data:
    all_merged = pd.concat(merged_data)
    fig = px.scatter(
        all_merged,
        x="MeanSentimentScore",
        y="Return",
        color="Company",
        trendline="ols",
        title="Sentiment vs Daily Return Correlation",
        labels={"MeanSentimentScore": "Mean Sentiment Score", "Return": "Daily Stock Return"},
    )
    fig.show()

    fig2 = px.line(
        all_merged,
        x="PublishedAt",
        y="MeanSentimentScore",
        color="Company",
        title="Daily Sentiment Trend by Company"
    )
    fig2.show()
else:
    print("⚠️ No merged data available for visualization.")

corr_df.to_csv("sentiment_market_correlation.csv", index=False)
print("\n✅ All results saved: news_sentiment_raw.csv & sentiment_market_correlation.csv")