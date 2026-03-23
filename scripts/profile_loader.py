from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PROFILE_DIR = Path(__file__).resolve().parent.parent / "vendor_profiles"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if (
            key in merged
            and isinstance(merged[key], dict)
            and isinstance(value, dict)
        ):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def available_profiles() -> list[str]:
    names: list[str] = []
    for path in PROFILE_DIR.glob("*.json"):
        names.append(path.stem)
    return sorted(names)


def load_profile(profile_name: str) -> dict[str, Any]:
    common = load_json(PROFILE_DIR / "common.json")
    if profile_name == "common":
        return common

    profile_path = PROFILE_DIR / f"{profile_name}.json"
    if not profile_path.exists():
        known = ", ".join(available_profiles())
        raise ValueError(
            f"Unknown profile '{profile_name}'. Available profiles: {known}"
        )

    vendor = load_json(profile_path)
    return deep_merge(common, vendor)


def match_profile_from_idn(idn: str) -> str:
    normalized = idn.upper()
    for name in available_profiles():
        if name == "common":
            continue
        profile = load_profile(name)
        for token in profile.get("idn_match", []):
            if token.upper() in normalized:
                return name
    return "common"
