import requests
import pandas as pd
from dotenv import load_dotenv
import json
import os, re
import ast


# === CONFIGURATION ===
load_dotenv()

# Récupérer une clé
BEARER_TOKEN = os.getenv("BEARER_TOKEN")
QUERY = "TSLA OR Tesla lang:en -is:retweet"  # requête (mot-clé, langue, exclusion des RT)
MAX_RESULTS = 50  # entre 10 et 100 (limite de l’API gratuite)
N_TWEETS = 200    # total de tweets que tu veux récupérer (l’API renvoie 100 max par page)


def search_tweets(query, bearer_token, n_tweets=N_TWEETS):
    headers = {"Authorization": f"Bearer {bearer_token}"}
    url = "https://api.x.com/2/tweets/search/recent"

    params = {
        "query": query,
        "max_results": MAX_RESULTS,
        "tweet.fields": "id,text,created_at,public_metrics,lang",
    }

    tweets = []
    next_token = None

    while len(tweets) < n_tweets:
        if next_token:
            params["next_token"] = next_token

        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            print("Erreur:", response.status_code, response.text)
            break

        data = response.json()
        tweets.extend(data.get("data", []))

        next_token = data.get("meta", {}).get("next_token")
        if not next_token:
            break

    return tweets[:n_tweets]


tweets = search_tweets(QUERY, BEARER_TOKEN, N_TWEETS)
df = pd.DataFrame(tweets)
print(df.head())

# Sauvegarde CSV pour analyse ultérieure
df.to_csv("tweets_TSLA.csv", index=False)
print(f"{len(df)} tweets enregistrés dans tweets_TSLA.csv ✅")


df = pd.read_csv("tweets_TSLA.csv")
print(df.columns)
print(df.shape)


# Formattage de la date
df["created_at"] = pd.to_datetime(df["created_at"], utc=True)
df["created_at_local"] = df["created_at"].dt.tz_convert("Europe/Paris")
df["date"] = df["created_at_local"].dt.date
df["hour"] = df["created_at_local"].dt.time
df["weekday"] = df["created_at_local"].dt.day_name()

# si regroupement en heure entière
# df["hour_int"] = df["created_at_local"].dt.hour

df = df.drop(["id", "edit_history_tweet_ids", "created_at", "created_at_local"], axis=1)

df.head(3)


print(json.dumps(df["public_metrics"][0], indent=2))
df["metrics"] = df["public_metrics"].apply(ast.literal_eval)


def clean_tweet(text):
    text = re.sub(r"http\S+", "", text)          # liens
    text = re.sub(r"@\w+", "", text)             # mentions
    text = re.sub(r"#", "", text)                # hashtag symbol
    text = re.sub(r"[^\w\s$]", "", text)         # ponctuation sauf $
    text = re.sub(r"\s+", " ", text).strip()     # espaces multiples
    return text

df["clean_text"] = df["text"].astype(str).apply(clean_tweet)
df = df[df["clean_text"].str.len() > 5]  # supprime tweets vides ou trop courts

df[["text", "clean_text"]].head(5)


def extract_metrics(metrics_str):
    try:
        metrics = ast.literal_eval(metrics_str)
        return metrics.get("like_count", 0), metrics.get("retweet_count", 0)
    except:
        return 0, 0

df[["likes", "retweets"]] = df["public_metrics"].apply(lambda x: pd.Series(extract_metrics(str(x))))


from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
analyzer = SentimentIntensityAnalyzer()

df["sentiment_score"] = df["clean_text"].apply(lambda x: analyzer.polarity_scores(x)["compound"])
df["sentiment_label"] = df["sentiment_score"].apply(lambda x: "positive" if x > 0.05 else ("negative" if x < -0.05 else "neutral"))


from transformers import pipeline
# sentiment_model = pipeline("sentiment-analysis", model="cardiffnlp/twitter-roberta-base-sentiment-latest")

df["sentiment"] = df["clean_text"].apply(lambda x: sentiment_model(x[:512])[0]["label"])

df["created_at"] = pd.to_datetime(df["created_at"])
sentiment_daily = df.groupby(df["created_at"].dt.date)["sentiment_score"].mean().reset_index()
print(sentiment_daily.head())
