import json
from pathlib import Path
from typing import Any

from app.core.config import settings


DATA_DIR = Path(settings.DATA_DIR)


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _stat_items(payload: dict[str, Any]) -> dict[str, dict[str, float]]:
    return {
        key: value
        for key, value in payload.items()
        if isinstance(value, dict) and "p05" in value and "p95" in value
    }


_security = _load_json(DATA_DIR / "치안리스크" / "meta_security_stats.json")
_flood = _load_json(DATA_DIR / "침수리스크" / "meta_flood_stats.json")
_noise = _load_json(DATA_DIR / "소음리스크" / "meta_noise_stats.json")
_health = _load_json(DATA_DIR / "의료접근성" / "meta_health_stats.json")
_congestion = _load_json(DATA_DIR / "생활혼잡도" / "meta_congestion_stats.json")

META_STATS: dict[str, dict[str, float]] = {
    **_stat_items(_security),
    **_stat_items(_flood),
    **_stat_items(_noise.get("stats", {})),
    **_stat_items(_health.get("stats", {})),
    **_stat_items(_congestion),
}

NOISE_HOURLY_WEIGHTS: dict[str, float] = {
    str(key): float(value)
    for key, value in _noise.get("hourly_weights", {}).items()
    if isinstance(value, (int, float))
}

HEALTH_COLOR_SCALE: dict[str, Any] = (
    _health.get("stats", {})
    .get("ui_rendering", {})
    .get("color_scale", {})
)


def get_stat(key: str) -> dict[str, float] | None:
    return META_STATS.get(key)
