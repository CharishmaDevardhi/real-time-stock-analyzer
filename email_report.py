from __future__ import annotations

import os
import re
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage


EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class EmailReportError(Exception):
    pass


@dataclass(frozen=True)
class SmtpConfig:
    host: str
    port: int
    user: str
    password: str
    from_email: str


def smtp_config_from_env_or_secrets(st_secrets: dict | None = None) -> SmtpConfig | None:
    def pick(key: str) -> str | None:
        if st_secrets and st_secrets.get(key) not in (None, ""):
            return str(st_secrets.get(key))
        env = os.getenv(key)
        return env if env not in (None, "") else None

    host = pick("SMTP_HOST")
    port_raw = pick("SMTP_PORT")
    user = pick("SMTP_USER")
    password = pick("SMTP_PASS")
    from_email = pick("SMTP_FROM") or user

    if not (host and port_raw and user and password and from_email):
        return None

    try:
        port = int(port_raw)
    except Exception as e:  # noqa: BLE001
        raise EmailReportError("SMTP_PORT must be an integer.") from e

    return SmtpConfig(host=host, port=port, user=user, password=password, from_email=from_email)


def validate_email_address(email: str) -> bool:
    return bool(EMAIL_RE.match((email or "").strip()))


def send_report(
    *,
    to_email: str,
    subject: str,
    body: str,
    smtp: SmtpConfig,
) -> None:
    if not validate_email_address(to_email):
        raise EmailReportError("Please enter a valid email address.")

    msg = EmailMessage()
    msg["From"] = smtp.from_email
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        with smtplib.SMTP(smtp.host, smtp.port, timeout=20) as server:
            server.ehlo()
            # Start TLS for typical ports like 587
            try:
                server.starttls()
                server.ehlo()
            except Exception:
                # Some SMTP servers may not support starttls on given port; proceed without TLS.
                pass
            server.login(smtp.user, smtp.password)
            server.send_message(msg)
    except Exception as e:  # noqa: BLE001
        raise EmailReportError("Failed to send email. Check SMTP settings and credentials.") from e


def format_email_body(
    *,
    stock_label: str,
    ticker: str,
    current_price: float,
    pct_change: float,
    signal: str,
    explanation: str,
) -> str:
    change = f"{pct_change:+.2f}"
    return (
        "📈 STOCK ANALYSIS REPORT\n\n"
        f"Stock: {stock_label} ({ticker})\n\n"
        "📊 Market Snapshot\n"
        f"- Current Price: ₹{current_price:.2f}\n"
        f"- Change: {change}%\n\n"
        f"📉 Signal: {signal}\n\n"
        "🧠 Insight\n"
        f"{explanation}\n\n"
        "⚠️ Note\n"
        "This is for educational purposes only, not financial advice.\n"
    )

