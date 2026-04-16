from __future__ import annotations

from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from analysis import add_moving_averages, build_structured_summary, current_signal, detect_crossovers
from ai_explain import AIExplainError, groq_explain, groq_is_configured
from email_report import EmailReportError, format_email_body, send_report, smtp_config_from_env_or_secrets
from stock_data import StockDataError, default_period_for_interval, fetch_history, snapshot_from_history
from tickers import build_choices, infer_ticker_from_free_text


st.set_page_config(page_title="Smart Stock Analyzer", layout="wide")
st.markdown(
    """
    <style>
    .stApp {
        background:
            radial-gradient(1200px 500px at 20% -10%, rgba(37, 99, 235, 0.22), transparent 55%),
            radial-gradient(900px 450px at 90% 0%, rgba(124, 58, 237, 0.20), transparent 55%),
            linear-gradient(145deg, #05070f 0%, #090f1f 40%, #070b16 100%);
        color: #e6ebff;
    }
    [data-testid="stHeader"] {
        background: transparent;
        height: 0;
    }
    [data-testid="stToolbar"] {
        right: 0.5rem;
    }
    .block-container {
        padding-top: 0.25rem;
        padding-bottom: 1.1rem;
        max-width: min(96vw, 1580px);
    }
    h1, h2, h3, p, label, div {
        color: #e6ebff;
    }
    p, label, [data-testid="stCaptionContainer"] {
        font-size: 1.02rem;
    }
    .app-title {
        text-align: center;
        font-size: 2.8rem;
        font-weight: 700;
        letter-spacing: 0.2px;
        margin: 0.2rem 0 0.35rem 0;
    }
    .subtle-text {
        text-align: center;
        color: #98a2c7;
        margin-bottom: 0.95rem;
        font-size: 1.05rem;
    }
    .glass-card {
        background: linear-gradient(145deg, rgba(18, 26, 48, 0.80), rgba(14, 20, 38, 0.72));
        border: 1px solid rgba(122, 146, 255, 0.22);
        box-shadow: 0 0 28px rgba(80, 113, 255, 0.16), inset 0 0 0 1px rgba(255, 255, 255, 0.02);
        border-radius: 18px;
        padding: 0.8rem 1rem;
    }
    [data-testid="stTextInput"] > div > div > input,
    [data-testid="stSelectbox"] > div > div {
        background: rgba(12, 18, 34, 0.78) !important;
        border: 1px solid rgba(99, 122, 255, 0.35) !important;
        border-radius: 14px !important;
        color: #e6ebff !important;
        box-shadow: 0 0 18px rgba(80, 113, 255, 0.18);
    }
    [data-testid="stTextInput"] input::placeholder {
        color: #9aa6d2 !important;
    }
    [data-baseweb="select"] > div,
    [data-baseweb="input"] > div {
        background: rgba(12, 18, 34, 0.78) !important;
        color: #e6ebff !important;
    }
    [data-baseweb="popover"],
    [data-baseweb="menu"],
    div[role="listbox"] {
        background: #0c1222 !important;
        color: #e6ebff !important;
        border: 1px solid rgba(99, 122, 255, 0.35) !important;
        border-radius: 12px !important;
        box-shadow: 0 10px 32px rgba(7, 10, 21, 0.75) !important;
    }
    div[role="option"] {
        background: transparent !important;
        color: #e6ebff !important;
    }
    div[role="option"][aria-selected="true"] {
        background: rgba(65, 93, 255, 0.25) !important;
    }
    .stButton > button {
        border-radius: 12px;
        border: 1px solid rgba(113, 138, 255, 0.55);
        background: linear-gradient(120deg, #2563eb 0%, #7c3aed 100%);
        color: #ffffff;
        font-weight: 600;
        box-shadow: 0 0 24px rgba(87, 116, 255, 0.32);
    }
    [data-testid="stMetric"] {
        background: linear-gradient(145deg, rgba(18, 26, 48, 0.80), rgba(14, 20, 38, 0.72));
        border: 1px solid rgba(122, 146, 255, 0.20);
        border-radius: 16px;
        padding: 0.8rem 1rem;
        box-shadow: 0 0 18px rgba(80, 113, 255, 0.15);
    }
    [data-testid="stMetricLabel"] p {
        font-size: 1rem !important;
        color: #aeb9e6 !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.55rem !important;
        font-weight: 700 !important;
    }
    [data-testid="stPlotlyChart"] > div {
        border-radius: 18px;
        padding: 0.35rem;
        background: linear-gradient(145deg, rgba(18, 26, 48, 0.70), rgba(12, 18, 34, 0.70));
        border: 1px solid rgba(122, 146, 255, 0.16);
        box-shadow: 0 0 24px rgba(80, 113, 255, 0.16);
    }
    @media (max-width: 900px) {
        .block-container {
            max-width: 100vw;
            padding-left: 0.55rem;
            padding-right: 0.55rem;
            padding-top: 0.1rem;
        }
        [data-testid="column"] {
            width: 100% !important;
            flex: 1 1 100% !important;
            min-width: 100% !important;
        }
        .app-title {
            font-size: 2rem;
            margin-top: 0.1rem;
        }
        .subtle-text {
            font-size: 0.92rem;
            margin-bottom: 0.55rem;
        }
        [data-testid="stMetricValue"] {
            font-size: 1.25rem !important;
        }
        .glass-card {
            padding: 0.65rem 0.8rem;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def _format_volume(v: int | None) -> str:
    if v is None:
        return "—"
    return f"{v:,}"


@st.cache_data(show_spinner=False, ttl=300)
def _cached_fetch(ticker: str, period: str, interval: str) -> pd.DataFrame:
    return fetch_history(ticker, period=period, interval=interval)  # type: ignore[arg-type]


@st.cache_data(show_spinner=False, ttl=120)
def _cached_snapshot(ticker: str) -> tuple[float, float]:
    df = fetch_history(ticker, period="5d", interval="1d")
    snap = snapshot_from_history(ticker, df)
    return snap.current_price, snap.pct_change


def _stock_card(name: str, ticker: str) -> None:
    try:
        price, change = _cached_snapshot(ticker)
        color = "#16a34a" if change >= 0 else "#dc2626"
        st.markdown(
            (
                "<div class='glass-card'>"
                f"<div style='font-weight:700;font-size:0.95rem'>{name}</div>"
                f"<div style='color:#9aa6d2;font-size:0.82rem;margin-top:2px'>{ticker}</div>"
                f"<div style='margin-top:8px;font-size:1.15rem;font-weight:700'>{price:.2f}</div>"
                f"<div style='margin-top:4px;color:{color};font-weight:700'>{change:+.2f}%</div>"
                "</div>"
            ),
            unsafe_allow_html=True,
        )
    except Exception:
        st.markdown(
            (
                "<div class='glass-card'>"
                f"<div style='font-weight:700;font-size:0.95rem'>{name}</div>"
                f"<div style='color:#9aa6d2;font-size:0.82rem;margin-top:2px'>{ticker}</div>"
                "<div style='margin-top:8px;color:#9aa6d2'>Data unavailable</div>"
                "</div>"
            ),
            unsafe_allow_html=True,
        )


def _build_figure(
    df: pd.DataFrame,
    *,
    signal_text: str,
    fast_window: int = 20,
    slow_window: int = 50,
) -> go.Figure:
    fast_col = f"SMA{fast_window}"
    slow_col = f"SMA{slow_window}"

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["Close"],
            mode="lines",
            name="Price",
            line=dict(width=2.5, color="#8ab4ff"),
            hovertemplate="Date: %{x}<br>Close: %{y:.2f}<extra></extra>",
        )
    )

    if fast_col in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df[fast_col],
                mode="lines",
                name=f"Fast MA ({fast_window})",
                line=dict(width=2, color="#00d4ff"),
                hovertemplate="Date: %{x}<br>Fast MA: %{y:.2f}<extra></extra>",
            )
        )
    if slow_col in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df[slow_col],
                mode="lines",
                name=f"Slow MA ({slow_window})",
                line=dict(width=2, color="#b892ff"),
                hovertemplate="Date: %{x}<br>Slow MA: %{y:.2f}<extra></extra>",
            )
        )

    buy_pts, sell_pts = detect_crossovers(df, fast_window=fast_window, slow_window=slow_window)
    if not buy_pts.empty:
        fig.add_trace(
            go.Scatter(
                x=buy_pts.index,
                y=buy_pts["Close"],
                mode="markers",
                name="BUY crossover",
                marker=dict(symbol="triangle-up", size=13, color="#22c55e"),
                hovertemplate="BUY crossover<br>Date: %{x}<br>Price: %{y:.2f}<extra></extra>",
            )
        )
    if not sell_pts.empty:
        fig.add_trace(
            go.Scatter(
                x=sell_pts.index,
                y=sell_pts["Close"],
                mode="markers",
                name="SELL crossover",
                marker=dict(symbol="triangle-down", size=13, color="#ef4444"),
                hovertemplate="SELL crossover<br>Date: %{x}<br>Price: %{y:.2f}<extra></extra>",
            )
        )

    fig.update_layout(
        margin=dict(l=12, r=12, t=14, b=10),
        height=650,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        xaxis_title=None,
        yaxis_title="Price",
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(12,18,34,0.76)",
        font=dict(color="#dbe5ff"),
    )
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="rgba(120,140,200,0.16)", zeroline=False)
    sig_color = "#16a34a" if signal_text == "BUY" else "#dc2626"
    fig.add_annotation(
        x=0.965,
        y=0.975,
        xref="paper",
        yref="paper",
        text=f"<b>{signal_text}</b>",
        showarrow=False,
        font=dict(color="white", size=18),
        bgcolor="rgba(14,20,38,0.82)",
        bordercolor=sig_color,
        borderwidth=2,
        borderpad=10,
    )
    return fig


if "query" not in st.session_state:
    st.session_state.query = ""

st.markdown("<div class='app-title'>Real-Time Stock Market Analyzer</div>", unsafe_allow_html=True)
st.markdown(f"<div class='subtle-text'>{datetime.now().strftime('%A, %d %b %Y')}</div>", unsafe_allow_html=True)

choices = build_choices()

header_left, header_right = st.columns([2, 1], vertical_alignment="bottom")
with header_left:
    query = st.text_input(
        "Search",
        value=st.session_state.query,
        placeholder="Search company (e.g., Reliance or RELIANCE.NS)",
        label_visibility="collapsed",
    ).strip()
    st.session_state.query = query
with header_right:
    interval = st.selectbox("Interval", options=["1d", "1h", "30m", "15m"], index=0)

matches = choices
if query:
    q = query.lower()
    matches = [c for c in choices if q in c.label.lower() or q in c.ticker.lower()]
    matches = matches[:12]

match_options = ["Select a suggested stock"] + [m.display() for m in matches]
picked = st.selectbox("Suggested Stocks", options=match_options, index=0)

watch_a, watch_b, watch_c = st.columns(3)
with watch_a:
    _stock_card("Dow Jones", "^DJI")
with watch_b:
    _stock_card("S&P 500", "^GSPC")
with watch_c:
    _stock_card("Apple", "AAPL")

selected_ticker: str | None = None
selected_label: str = ""
if picked != "Select a suggested stock":
    selected_label, selected_ticker = picked.split(" — ", 1)
elif query:
    selected_ticker = infer_ticker_from_free_text(query)
    selected_label = query or "Custom input"

# Dashboard state before stock selection
if not selected_ticker:
    st.info("Select a suggestion or type a valid ticker to start analysis.")
    st.stop()

# Analysis State (after stock selection)
period = default_period_for_interval(interval)

with st.spinner("Fetching stock data…"):
    try:
        df_raw = _cached_fetch(selected_ticker, period, interval)
        snapshot = snapshot_from_history(selected_ticker, df_raw)
    except StockDataError as e:
        st.error(str(e))
        st.stop()

df = add_moving_averages(df_raw, fast_window=20, slow_window=50)
signal = current_signal(df, fast_window=20, slow_window=50)

if df["SMA50"].dropna().empty:
    st.warning("Not enough data points to compute a reliable 50-day moving average yet.")

fig = _build_figure(df, signal_text=signal.signal, fast_window=20, slow_window=50)
st.plotly_chart(fig, use_container_width=True)

metrics = st.columns(3)
metrics[0].metric("Current price", f"{snapshot.current_price:.2f}", help=f"As of {snapshot.as_of.isoformat()}")
metrics[1].metric("% change", f"{snapshot.pct_change:+.2f}%")
metrics[2].metric("Volume", _format_volume(snapshot.volume))

fast_latest = df["SMA20"].dropna()
slow_latest = df["SMA50"].dropna()
if not fast_latest.empty and not slow_latest.empty:
    fast_val = float(fast_latest.iloc[-1])
    slow_val = float(slow_latest.iloc[-1])
    gap_pct = ((fast_val - slow_val) / slow_val * 100.0) if slow_val else 0.0
    direction = "above" if gap_pct >= 0 else "below"
    explanation_sentence = (
        f"{signal.signal} signal: the 20-day moving average is {abs(gap_pct):.2f}% {direction} "
        "the 50-day moving average, indicating the current short-term trend direction."
    )
else:
    explanation_sentence = signal.explanation

st.markdown(f"<div class='glass-card' style='margin-top:0.55rem'>{explanation_sentence}</div>", unsafe_allow_html=True)

structured = build_structured_summary(selected_ticker, df, signal, fast_window=20, slow_window=50)
ai_text: str | None = None
ai_configured = groq_is_configured(st_secrets=getattr(st, "secrets", None))
try:
    ai_text = groq_explain(structured, st_secrets=getattr(st, "secrets", None))
except AIExplainError:
    ai_text = None

if ai_text:
    st.caption(ai_text)
elif ai_configured:
    st.caption("AI explanation is temporarily unavailable.")

st.markdown("<div style='margin-top:0.65rem'></div>", unsafe_allow_html=True)
st.subheader("Email Report")
email = st.text_input("Email", placeholder="name@example.com")
send_btn = st.button("Send Report", type="primary", use_container_width=False)

if send_btn:
    smtp_cfg = smtp_config_from_env_or_secrets(getattr(st, "secrets", None))
    subject = f"Stock report: {selected_ticker} ({signal.signal})"
    body = format_email_body(
        stock_label=selected_label,
        ticker=selected_ticker,
        current_price=snapshot.current_price,
        pct_change=snapshot.pct_change,
        signal=signal.signal,
        explanation=explanation_sentence,
    )

    if not email.strip():
        st.error("Please enter your email address before sending the report.")
    elif smtp_cfg is None:
        st.warning("SMTP is not configured. Add SMTP settings in `.streamlit/secrets.toml`. Report preview:")
        st.code(body)
    else:
        try:
            send_report(to_email=email, subject=subject, body=body, smtp=smtp_cfg)
            st.success("Report sent.")
        except EmailReportError as e:
            st.error(str(e))

st.caption(f"Last refreshed: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")

