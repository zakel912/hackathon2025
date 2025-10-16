# finance_api/main.py
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Literal
from utils.fetch_data import fetch_stock_data, to_json_format

app = FastAPI(title="Finance Data API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TICKERS = {
    "AAPL": "Apple",
    "MSFT": "Microsoft",
    "AMZN": "Amazon",
    "GOOGL": "Alphabet (Google)",
    "TSLA": "Tesla",
    "MC.PA": "LVMH",
    "TTE.PA": "TotalEnergies",
    "SAN.PA": "Sanofi",
    "AIR.PA": "Airbus",
    "SU.PA": "Schneider Electric"
}

@app.get("/")
def root():
    return {
        "message": "📊 Welcome to the Finance Data API",
        "available_endpoints": {
            "/stocks": "Get stock data by ticker and period",
        },
        "example_usage": "/stocks?ticker=TSLA&period=7d"
    }


@app.get("/stocks")
def get_stock_data(
    ticker: str = Query(...),
    period: Literal["1d", "3d", "7d", "1mo"] = "7d",
    interval: Literal["15m", "1h", "1d"] = "1h"
):
    if ticker not in TICKERS:
        return {"error": f"Ticker '{ticker}' non reconnu."}

    df = fetch_stock_data(ticker, period, interval)
    return to_json_format(ticker, TICKERS[ticker], df)

@app.get("/tickers")
def get_tickers():
    return [{"ticker": t, "name": n} for t, n in TICKERS.items()]