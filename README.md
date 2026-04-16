# 📈 Real-Time Stock Market Analyzer

A sleek, intelligent web application that analyzes stock trends in real-time using a Moving Average Crossover strategy, enhanced with actionable insights, trend strength evaluation, and email-based reporting.

---

## 🚀 Overview

This application transforms raw stock data into **decision-support insights**.
Instead of just displaying charts, it helps users understand:

* Market direction 📉📈
* Trend strength 📊
* Buy/Sell signals ⚡
* What the trend actually means 🧠

Built with a focus on **clarity, usability, and real-world relevance**.

---

## ✨ Features

* 🔍 Smart stock search with suggestions
* 📊 Real-time stock data visualization
* 📉 Moving Average (20-day & 50-day) analysis
* ⚡ Buy/Sell signal generation
* 📊 Trend Strength indicator (Weak / Moderate / Strong)
* 🧠 Insight-based explanation (not just raw data)
* 📧 One-click email report generation
* 🌙 Clean, modern dark-themed UI

---

## 🧠 How It Works

The application uses a **Moving Average Crossover strategy**, a widely used technical analysis method.

### 📌 Core Logic

* **20-day Moving Average** → short-term trend
* **50-day Moving Average** → long-term trend

### ⚡ Signal Generation

* If 20-day MA crosses **above** 50-day → **BUY signal**
* If 20-day MA crosses **below** 50-day → **SELL signal**

---

### 📊 Trend Strength

Trend strength is determined by the percentage difference between the two moving averages:

* **< 1%** → Weak
* **1% – 3%** → Moderate
* **> 3%** → Strong

---

### 🧠 Insight Layer

The system interprets technical signals into **human-readable insights**, helping users understand:

* Market momentum
* Risk level
* Possible next actions

---

## 🛠️ Tech Stack

* **Python**
* **Streamlit** (UI framework)
* **yFinance** (stock data)
* **SMTP (Gmail)** for email reports
* *(Optional)* Groq API for AI-based explanations

---

## ▶️ Run Locally

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

---

## 🔐 Secrets Configuration (Recommended)

Create a file:

```
.streamlit/secrets.toml
```

### 📧 Email (SMTP)

```toml
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "your_email@gmail.com"
SMTP_PASS = "your_app_password"
SMTP_FROM = "your_email@gmail.com"
```

---

### 🤖 AI (Optional)

```toml
GROQ_API_KEY = "your_api_key"
```

---

## 📌 Use Case

This tool is designed for:

* Beginners learning stock market concepts
* Users who want simplified insights instead of raw data
* Quick analysis without complex trading platforms

---

## ⚠️ Disclaimer

This application is built for **educational purposes only**.
It does not provide financial advice. Always conduct your own research before making investment decisions.

---

## 🌟 What Makes It Different

Unlike basic stock visualizers, this application focuses on:

* ✅ **Interpretation over raw data**
* ✅ **Decision support, not just display**
* ✅ **Clean and intuitive user experience**

---

## 📬 Future Improvements

* AI-powered chatbot for financial concepts
* News-based reasoning for stock movement
* User watchlists and personalization

---



- Data source is `yfinance` (recent market data; not guaranteed tick-by-tick live).
- Signals are educational and not financial advice.

