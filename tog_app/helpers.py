from __future__ import annotations

import re
from urllib.parse import urlparse

from .constants import (
    BORDER,
    COLOR_BORDER_MAP,
    FORMATION_SLOT_ORDER,
    ICON_RATIO_HEIGHT,
    ICON_RATIO_WIDTH,
    LEVEL_STAR_COLOR_MAP,
    TEAM_OPTIONS,
    TEXT_MUTED,
)


def normalize_team_name(value: str) -> str:
    return " ".join((value or "").strip().split()).casefold()


def normalize_character_name(value: str) -> str:
    return " ".join((value or "").strip().split()).casefold()


def normalize_item_name(value: str) -> str:
    return " ".join((value or "").strip().split()).casefold()


def character_version_key(row: dict[str, str]) -> str:
    return "||".join(
        [
            (row.get("Name", "") or "").strip(),
            (row.get("Rarity", "") or "").strip(),
            (row.get("Color", "") or "").strip(),
            (row.get("Icon", "") or "").strip(),
        ]
    )


def character_display_name(row: dict[str, str] | None) -> str:
    if row is None:
        return ""
    name = (row.get("Name", "") or "").strip() or "Unnamed Character"
    rarity = (row.get("Rarity", "") or "").strip()
    return f"{name} ({rarity})" if rarity else name


def display_character_field_label(value: str) -> str:
    return "Revolution" if (value or "").strip() == "R" else value


def empty_slot_map() -> dict[str, str]:
    return {slot_key: "" for slot_key in FORMATION_SLOT_ORDER}


def empty_team_map() -> dict[str, dict[str, str]]:
    return {team_name: empty_slot_map() for team_name in TEAM_OPTIONS}


def sanitize_filename(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())
    return cleaned.strip("._") or "icon"


def is_url(value: str) -> bool:
    parsed = urlparse(value.strip())
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def get_color_border(value: str) -> str:
    return COLOR_BORDER_MAP.get(value.strip().upper(), BORDER)


def get_level_star_color(value: str) -> str:
    return LEVEL_STAR_COLOR_MAP.get(value.strip().upper(), TEXT_MUTED)


def get_star_count(value: str) -> int:
    try:
        return max(0, int(value.strip()))
    except (TypeError, ValueError, AttributeError):
        return 0


def parse_int(value: str) -> int:
    try:
        return int((value or "").strip())
    except (TypeError, ValueError, AttributeError):
        return 0


def parse_float(value: str) -> float:
    normalized = str(value or "").strip().replace(",", ".")
    try:
        return float(normalized)
    except (TypeError, ValueError):
        return 0.0


def format_decimal(value: float, places: int = 2) -> str:
    rendered = f"{float(value):.{places}f}".rstrip("0").rstrip(".")
    if rendered in {"", "-0"}:
        return "0"
    return rendered


def centered_ratio_box(
    container_width: int,
    container_height: int,
    padding: int,
) -> tuple[int, int, int, int]:
    available_width = max(1, container_width - (padding * 2))
    available_height = max(1, container_height - (padding * 2))

    if available_width * ICON_RATIO_HEIGHT <= available_height * ICON_RATIO_WIDTH:
        box_width = available_width
        box_height = round(box_width * ICON_RATIO_HEIGHT / ICON_RATIO_WIDTH)
    else:
        box_height = available_height
        box_width = round(box_height * ICON_RATIO_WIDTH / ICON_RATIO_HEIGHT)

    x1 = (container_width - box_width) // 2
    y1 = (container_height - box_height) // 2
    return x1, y1, x1 + box_width, y1 + box_height
