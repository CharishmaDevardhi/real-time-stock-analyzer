from __future__ import annotations

from dataclasses import dataclass


# Keep this list curated and beginner-friendly. Users can still type any ticker directly.
POPULAR_STOCKS: dict[str, str] = {
    # India (NSE)
    "Reliance Industries": "RELIANCE.NS",
    "Tata Consultancy Services (TCS)": "TCS.NS",
    "HDFC Bank": "HDFCBANK.NS",
    "Infosys": "INFY.NS",
    "ICICI Bank": "ICICIBANK.NS",
    "State Bank of India (SBI)": "SBIN.NS",
    "ITC": "ITC.NS",
    "Bharti Airtel": "BHARTIARTL.NS",
    "Larsen & Toubro (L&T)": "LT.NS",
    # US
    "Apple": "AAPL",
    "Microsoft": "MSFT",
    "NVIDIA": "NVDA",
    "Amazon": "AMZN",
    "Alphabet (Google) - Class A": "GOOGL",
    "Meta (Facebook)": "META",
    "Tesla": "TSLA",
    "Berkshire Hathaway - Class B": "BRK-B",
    # ETFs
    "S&P 500 ETF (SPY)": "SPY",
    "Nasdaq 100 ETF (QQQ)": "QQQ",
}


@dataclass(frozen=True)
class TickerChoice:
    label: str
    ticker: str

    def display(self) -> str:
        return f"{self.label} — {self.ticker}"


def build_choices() -> list[TickerChoice]:
    return [TickerChoice(label=k, ticker=v) for k, v in POPULAR_STOCKS.items()]


def infer_ticker_from_free_text(text: str) -> str | None:
    """
    Best-effort mapping:
    - Exact match by company label (case-insensitive)
    - Exact match by ticker (case-insensitive)
    - If input already looks like a ticker, return it as-is (uppercased)
    """
    raw = (text or "").strip()
    if not raw:
        return None

    lowered = raw.lower()

    for name, ticker in POPULAR_STOCKS.items():
        if lowered == name.lower():
            return ticker

    for _, ticker in POPULAR_STOCKS.items():
        if lowered == ticker.lower():
            return ticker.upper()

    # Heuristic: treat input as ticker if it is mostly ticker-ish.
    # Allows: letters, digits, '.', '-', '=' (some tickers use '=' on Yahoo Finance)
    allowed = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-=")
    candidate = raw.upper()
    if all(ch in allowed for ch in candidate) and any(ch.isalpha() for ch in candidate):
        return candidate

    return None

