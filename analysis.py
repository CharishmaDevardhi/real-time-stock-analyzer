from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class SignalResult:
    signal: str  # "BUY" or "SELL"
    explanation: str


def add_moving_averages(df: pd.DataFrame, *, fast_window: int = 20, slow_window: int = 50) -> pd.DataFrame:
    if df is None or df.empty:
        raise ValueError("Empty dataframe.")
    if "Close" not in df.columns:
        raise ValueError("Dataframe must contain Close column.")

    out = df.copy()
    out[f"SMA{fast_window}"] = out["Close"].rolling(window=fast_window, min_periods=fast_window).mean()
    out[f"SMA{slow_window}"] = out["Close"].rolling(window=slow_window, min_periods=slow_window).mean()
    return out


def detect_crossovers(
    df: pd.DataFrame, *, fast_window: int = 20, slow_window: int = 50
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Returns (buy_points, sell_points) as dataframes with index=timestamp and Close column.
    """
    fast_col = f"SMA{fast_window}"
    slow_col = f"SMA{slow_window}"
    if fast_col not in df.columns or slow_col not in df.columns:
        raise ValueError("Moving averages missing. Call add_moving_averages first.")

    ma = df[[fast_col, slow_col, "Close"]].dropna(subset=[fast_col, slow_col, "Close"]).copy()
    if ma.empty:
        return ma.iloc[0:0], ma.iloc[0:0]

    diff = ma[fast_col] - ma[slow_col]
    prev = diff.shift(1)

    buy_mask = (prev <= 0) & (diff > 0)
    sell_mask = (prev >= 0) & (diff < 0)

    buy_pts = ma.loc[buy_mask, ["Close", fast_col, slow_col]]
    sell_pts = ma.loc[sell_mask, ["Close", fast_col, slow_col]]
    return buy_pts, sell_pts


def current_signal(df: pd.DataFrame, *, fast_window: int = 20, slow_window: int = 50) -> SignalResult:
    fast_col = f"SMA{fast_window}"
    slow_col = f"SMA{slow_window}"
    if fast_col not in df.columns or slow_col not in df.columns:
        raise ValueError("Moving averages missing. Call add_moving_averages first.")

    tail = df[[fast_col, slow_col]].dropna()
    if tail.empty:
        return SignalResult(
            signal="SELL",
            explanation="Not enough data yet to compute moving averages. Try a longer date range.",
        )

    fast = float(tail[fast_col].iloc[-1])
    slow = float(tail[slow_col].iloc[-1])

    if fast > slow:
        return SignalResult(
            signal="BUY",
            explanation=(
                f"Buy signal generated because the {fast_window}-day average is above the {slow_window}-day average, "
                "suggesting the short-term trend is stronger than the long-term trend."
            ),
        )

    return SignalResult(
        signal="SELL",
        explanation=(
            f"Sell signal generated because the {fast_window}-day average is below the {slow_window}-day average, "
            "suggesting the long-term trend is stronger than the short-term trend."
        ),
    )


def build_structured_summary(
    ticker: str,
    df: pd.DataFrame,
    signal: SignalResult,
    *,
    fast_window: int = 20,
    slow_window: int = 50,
) -> dict:
    """
    Create a compact summary for the LLM (JSON-like dict).
    """
    fast_col = f"SMA{fast_window}"
    slow_col = f"SMA{slow_window}"

    closes = df["Close"].dropna()
    last_close = float(closes.iloc[-1])
    prev_close = float(closes.iloc[-2]) if len(closes) >= 2 else last_close
    pct_change = ((last_close - prev_close) / prev_close) * 100.0 if prev_close else 0.0

    buy_pts, sell_pts = detect_crossovers(df, fast_window=fast_window, slow_window=slow_window)
    last_cross = None
    if not buy_pts.empty:
        last_cross = ("BUY", buy_pts.index[-1])
    if not sell_pts.empty:
        if last_cross is None or sell_pts.index[-1] > last_cross[1]:
            last_cross = ("SELL", sell_pts.index[-1])

    last_cross_type = last_cross[0] if last_cross else None
    last_cross_time = last_cross[1].isoformat() if last_cross else None

    fast_val = float(df[fast_col].dropna().iloc[-1]) if fast_col in df.columns and not df[fast_col].dropna().empty else None
    slow_val = float(df[slow_col].dropna().iloc[-1]) if slow_col in df.columns and not df[slow_col].dropna().empty else None

    # Simple volatility proxy: rolling std of returns (last 20)
    returns = closes.pct_change().dropna()
    vol20 = float(returns.tail(20).std() * 100.0) if len(returns) >= 5 else None

    return {
        "ticker": ticker,
        "latest_close": last_close,
        "pct_change_vs_prev_close": pct_change,
        "fast_ma_window": fast_window,
        "slow_ma_window": slow_window,
        "fast_ma_value": fast_val,
        "slow_ma_value": slow_val,
        "signal": signal.signal,
        "baseline_explanation": signal.explanation,
        "last_crossover": {"type": last_cross_type, "time": last_cross_time},
        "volatility_proxy_20": vol20,
        "disclaimer": "Educational only; not financial advice.",
    }

