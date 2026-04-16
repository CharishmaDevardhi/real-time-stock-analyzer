# Stock Analyzer (Streamlit)

Single-page web app for real-time(ish) stock visualization and a Moving Average Crossover strategy (20-day vs 50-day), with optional AI explanation (Groq) and an optional one-click email report.

## Run locally

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Secrets (optional but recommended)

Create `.streamlit/secrets.toml` (see template in this repo). The app will still run without Groq and without SMTP configured.

### Groq (AI explanation)

- `GROQ_API_KEY`: your Groq API key

### SMTP (email report)

- `SMTP_HOST`: e.g. `smtp.gmail.com`
- `SMTP_PORT`: e.g. `587`
- `SMTP_USER`: SMTP username/login
- `SMTP_PASS`: SMTP password / app password
- `SMTP_FROM`: From email address (often same as SMTP_USER)

## Notes

- Data source is `yfinance` (recent market data; not guaranteed tick-by-tick live).
- Signals are educational and not financial advice.

