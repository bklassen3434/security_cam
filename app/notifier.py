from __future__ import annotations
from datetime import datetime
import os
from typing import Optional
import requests

def notify_telegram(bot_token: str, chat_id: str | int, image_path_or_url: str, caption: str) -> None:
    base = f"https://api.telegram.org/bot{bot_token}"
    try:
        # upload local file
        url = f"{base}/sendPhoto"
        data = {"chat_id": chat_id, "caption": caption}
        with open(image_path_or_url, "rb") as f:
            files = {"photo": f}
            r = requests.post(url, data=data, files=files, timeout=30)
        r.raise_for_status()
        print("[NOTIFY][TG] Sent photo+caption")
    except Exception as e:
        print(f"[NOTIFY][TG] Failed to send photo+caption: {e}")


def render_body(template: str) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        return template.format(time=now)
    except Exception:
        # Safe fallback if template has an error
        return f"Unknown face at {now}"
