from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Literal

import pandas as pd
import yfinance as yf


class StockDataError(Exception):
    pass


@dataclass(frozen=True)
class StockSnapshot:
    ticker: str
    as_of: datetime
    current_price: float
    prev_close: float
    pct_change: float
    volume: int | None


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def fetch_history(
    ticker: str,
    *,
    period: str = "6mo",
    interval: Literal["1d", "1h", "30m", "15m", "5m", "1m"] = "1d",
) -> pd.DataFrame:
    """
    Returns OHLCV history indexed by datetime with at least Close and Volume.
    """
    t = (ticker or "").strip()
    if not t:
        raise StockDataError("Ticker is empty.")

    try:
        df = yf.Ticker(t).history(period=period, interval=interval, auto_adjust=False)
    except Exception as e:  # noqa: BLE001
        raise StockDataError(f"Failed to fetch data for {t}.") from e

    if df is None or df.empty:
        raise StockDataError(f"No data returned for {t}.")

    # Normalize index to datetime (yfinance uses pandas Timestamp already)
    df = df.copy()
    if not isinstance(df.index, pd.DatetimeIndex):
        raise StockDataError("Unexpected data format returned by yfinance.")

    # Standardize columns we use
    for required in ("Close", "Volume"):
        if required not in df.columns:
            raise StockDataError(f"Missing expected column: {required}")

    # Clean up timezone awareness for plotting/consistent formatting
    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC")
    else:
        df.index = df.index.tz_convert("UTC")

    # Ensure numeric
    df["Close"] = pd.to_numeric(df["Close"], errors="coerce")
    df["Volume"] = pd.to_numeric(df["Volume"], errors="coerce")
    df = df.dropna(subset=["Close"])

    if df.empty:
        raise StockDataError(f"Close prices are missing for {t}.")

    return df


def snapshot_from_history(ticker: str, df: pd.DataFrame) -> StockSnapshot:
    """
    Builds a single 'current' snapshot from the last two closes in df.
    """
    if df is None or df.empty:
        raise StockDataError("No data available to compute metrics.")

    closes = df["Close"].dropna()
    if len(closes) < 2:
        raise StockDataError("Not enough data points to compute change.")

    current_price = float(closes.iloc[-1])
    prev_close = float(closes.iloc[-2])
    pct_change = ((current_price - prev_close) / prev_close) * 100.0 if prev_close else 0.0

    vol = None
    if "Volume" in df.columns and pd.notna(df["Volume"].iloc[-1]):
        try:
            vol = int(df["Volume"].iloc[-1])
        except Exception:  # noqa: BLE001
            vol = None

    as_of = _ensure_utc(df.index[-1].to_pydatetime())

    return StockSnapshot(
        ticker=ticker,
        as_of=as_of,
        current_price=current_price,
        prev_close=prev_close,
        pct_change=pct_change,
        volume=vol,
    )


def default_period_for_interval(interval: str) -> str:
    # Keep enough samples to compute 50-day MA when using daily.
    if interval == "1d":
        return "6mo"
    if interval in {"1h", "30m", "15m"}:
        return "60d"
    if interval in {"5m", "1m"}:
        return "7d"
    return "6mo"


def cache_ttl_seconds_for_interval(interval: str) -> int:
    # A gentle cache that still feels “real-time” in Streamlit.
    if interval in {"1m", "5m"}:
        return 60
    if interval in {"15m", "30m"}:
        return 120
    if interval == "1h":
        return 180
    return 300

