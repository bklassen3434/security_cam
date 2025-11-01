from __future__ import annotations
from pathlib import Path
import json
from datetime import datetime
import uuid

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
USERS_JSON = DATA / "users.json"
ENROLL_DIR = DATA / "enroll"

def load_users() -> list[dict]:
    if not USERS_JSON.exists():
        return []
    with USERS_JSON.open("r") as f:
        return json.load(f)

def save_users(users: list[dict]) -> None:
    USERS_JSON.parent.mkdir(parents=True, exist_ok=True)
    with USERS_JSON.open("w") as f:
        json.dump(users, f, indent=2)

def create_user(name: str) -> dict:
    users = load_users()
    # simple id
    user_id = "u_" + uuid.uuid4().hex[:8]
    user = {"id": user_id, "name": name, "created_at": datetime.now().isoformat(timespec="seconds")}
    users.append(user)
    save_users(users)
    (ENROLL_DIR / user_id).mkdir(parents=True, exist_ok=True)
    return user

def get_user(user_id: str) -> dict | None:
    for u in load_users():
        if u["id"] == user_id:
            return u
    return None

def user_enroll_path(user_id: str) -> Path:
    return ENROLL_DIR / user_id
