from __future__ import annotations

import json
import os
from dataclasses import dataclass

import requests


class AIExplainError(Exception):
    pass


@dataclass(frozen=True)
class GroqConfig:
    api_key: str
    model: str = "llama-3.3-70b-versatile"
    base_url: str = "https://api.groq.com/openai/v1"
    timeout_seconds: int = 20


def _get_api_key_from_env_or_secrets(st_secrets: dict | None = None) -> str | None:
    if st_secrets and st_secrets.get("GROQ_API_KEY"):
        return str(st_secrets.get("GROQ_API_KEY")).strip() or None
    env = os.getenv("GROQ_API_KEY")
    return env.strip() if env else None


def groq_is_configured(*, st_secrets: dict | None = None) -> bool:
    return _get_api_key_from_env_or_secrets(st_secrets) is not None


def groq_explain(summary: dict, *, st_secrets: dict | None = None) -> str | None:
    """
    Returns a short beginner-friendly explanation, or None if not configured.
    """
    api_key = _get_api_key_from_env_or_secrets(st_secrets)
    if not api_key:
        return None

    cfg = GroqConfig(api_key=api_key)

    system = (
        "You are a helpful assistant that explains stock charts and moving-average crossover signals "
        "to beginners in plain English. Keep it concise, calm, and non-technical."
    )

    user = (
        "Explain the following stock summary for a beginner.\n\n"
        "Requirements:\n"
        "- Use 4-8 short bullet points.\n"
        "- Explain what the BUY/SELL signal means.\n"
        "- Mention the moving average crossover idea (20 vs 50) in simple terms.\n"
        "- Do NOT give guaranteed predictions.\n"
        "- End with a one-line disclaimer: 'This is educational, not financial advice.'\n\n"
        f"Summary JSON:\n{json.dumps(summary, ensure_ascii=False)}"
    )

    payload = {
        "model": cfg.model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.3,
        "max_tokens": 400,
    }

    try:
        resp = requests.post(
            f"{cfg.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {cfg.api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=cfg.timeout_seconds,
        )
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        return str(content).strip()
    except Exception as e:  # noqa: BLE001
        raise AIExplainError("Groq request failed.") from e

