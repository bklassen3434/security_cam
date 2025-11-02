import yaml
from pathlib import Path

def load_config(path: str | Path = "config.yaml") -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)

def update_config(base: dict, override: dict) -> dict:
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            update_config(base[k], v)
        else:
            base[k] = v
    return base
