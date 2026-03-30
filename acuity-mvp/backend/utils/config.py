from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_factor_catalog(config_path: str | Path | None = None) -> dict[str, Any]:
    base_path = Path(__file__).resolve().parent.parent
    target = Path(config_path) if config_path else base_path / "config" / "factors.yaml"
    with target.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}
