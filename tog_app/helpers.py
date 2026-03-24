from __future__ import annotations

import re
from urllib.parse import urlparse

from .constants import (
    BORDER,
    CHARACTER_FIELD_LABEL_MAP,
    COLOR_BORDER_MAP,
    COLOR_DISPLAY_MAP,
    DEFAULT_HEADERS,
    FORMATION_SLOT_ORDER,
    ICON_RATIO_HEIGHT,
    ICON_RATIO_WIDTH,
    LEVEL_STAR_COLOR_MAP,
    L_DISPLAY_MAP,
    TEAM_OPTIONS,
    TEXT_MUTED,
)

CHARACTER_FIELD_LABEL_ALIASES = {
    **{header.casefold(): header for header in DEFAULT_HEADERS},
    **{label.casefold(): header for header, label in CHARACTER_FIELD_LABEL_MAP.items()},
    "type": "IW Type",
}

COLOR_VALUE_ALIASES = {
    **{code.casefold(): code for code in COLOR_DISPLAY_MAP},
    **{label.casefold(): code for code, label in COLOR_DISPLAY_MAP.items()},
}

L_VALUE_ALIASES = {
    **{code.casefold(): code for code in {**L_DISPLAY_MAP, "P": "P"}},
    **{label.casefold(): code for code, label in L_DISPLAY_MAP.items()},
    "empty": "",
    "-": "",
}


def normalize_team_name(value: str) -> str:
    return " ".join((value or "").strip().split()).casefold()


def normalize_character_name(value: str) -> str:
    return " ".join((value or "").strip().split()).casefold()


def normalize_item_name(value: str) -> str:
    return " ".join((value or "").strip().split()).casefold()


def canonical_character_field_label(value: str) -> str:
    cleaned = " ".join(str(value or "").strip().split())
    if not cleaned:
        return ""
    return CHARACTER_FIELD_LABEL_ALIASES.get(cleaned.casefold(), cleaned)


def display_character_field_label(value: str) -> str:
    canonical = canonical_character_field_label(value)
    return CHARACTER_FIELD_LABEL_MAP.get(canonical, canonical)


def canonical_color_value(value: str) -> str:
    cleaned = str(value or "").strip()
    if not cleaned:
        return ""
    return COLOR_VALUE_ALIASES.get(cleaned.casefold(), cleaned.upper())


def display_color_value(value: str) -> str:
    canonical = canonical_color_value(value)
    if not canonical:
        return ""
    return COLOR_DISPLAY_MAP.get(canonical, canonical)


def canonical_l_value(value: str) -> str:
    cleaned = str(value or "").strip()
    if cleaned == 'None':
        return ""
    if not cleaned:
        return ""
    return L_VALUE_ALIASES.get(cleaned.casefold(), cleaned.upper())


def display_l_value(value: str) -> str:
    canonical = canonical_l_value(value)
    if not canonical:
        return ""
    return L_DISPLAY_MAP.get(canonical, canonical)


def canonical_character_field_value(header: str, value: str) -> str:
    canonical_header = canonical_character_field_label(header)
    cleaned = str(value or "").strip()
    if canonical_header == "Rarity":
        return cleaned.upper()
    if canonical_header == "Color":
        return canonical_color_value(cleaned)
    if canonical_header == "L":
        return canonical_l_value(cleaned)
    return cleaned


def display_character_field_value(header: str, value: str) -> str:
    canonical_header = canonical_character_field_label(header)
    cleaned = str(value or "").strip()
    if canonical_header == "Color":
        return display_color_value(cleaned)
    if canonical_header == "L":
        return display_l_value(cleaned)
    if canonical_header == "Rarity":
        return cleaned.upper()
    return cleaned


def storage_character_headers() -> list[str]:
    return [display_character_field_label(header) for header in DEFAULT_HEADERS]


def storage_character_row(row: dict[str, str]) -> dict[str, str]:
    return {
        display_character_field_label(header): display_character_field_value(header, row.get(header, ""))
        for header in DEFAULT_HEADERS
    }


def canonical_character_version_key(value: str) -> str:
    cleaned = str(value or "").strip()
    if not cleaned:
        return ""
    parts = cleaned.split("||")
    if len(parts) != 4:
        return cleaned
    name, rarity, color, icon = (part.strip() for part in parts)
    return "||".join((name, rarity.upper(), canonical_color_value(color), icon))


def storage_character_version_key(value: str) -> str:
    canonical = canonical_character_version_key(value)
    if not canonical:
        return ""
    parts = canonical.split("||")
    if len(parts) != 4:
        return canonical
    name, rarity, color, icon = parts
    return "||".join((name, rarity, display_color_value(color), icon))


def character_version_key(row: dict[str, str]) -> str:
    return "||".join(
        [
            (row.get("Name", "") or "").strip(),
            (row.get("Rarity", "") or "").strip().upper(),
            canonical_color_value(row.get("Color", "")),
            (row.get("Icon", "") or "").strip(),
        ]
    )


def character_display_name(row: dict[str, str] | None) -> str:
    if row is None:
        return ""
    name = (row.get("Name", "") or "").strip() or "Unnamed Character"
    rarity = (row.get("Rarity", "") or "").strip().upper()
    return f"{name} ({rarity})" if rarity else name


def empty_slot_map() -> dict[str, str]:
    return {slot_key: "" for slot_key in FORMATION_SLOT_ORDER}


def empty_team_entry() -> dict[str, str]:
    entry = empty_slot_map()
    entry["Note"] = ""
    return entry


def empty_team_map() -> dict[str, dict[str, str]]:
    return {team_name: empty_team_entry() for team_name in TEAM_OPTIONS}


def normalize_team_entry(value: object) -> dict[str, str]:
    normalized = empty_team_entry()
    if not isinstance(value, dict):
        return normalized

    for slot_key in FORMATION_SLOT_ORDER:
        normalized[slot_key] = canonical_character_version_key(str(value.get(slot_key, "") or "").strip())
    normalized["Note"] = str(value.get("Note", "") or "").strip()
    return normalized


def sanitize_filename(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())
    return cleaned.strip("._") or "icon"


def is_url(value: str) -> bool:
    parsed = urlparse(value.strip())
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def get_color_border(value: str) -> str:
    return COLOR_BORDER_MAP.get(canonical_color_value(value), BORDER)


def get_level_star_color(value: str) -> str:
    return LEVEL_STAR_COLOR_MAP.get(canonical_l_value(value), TEXT_MUTED)


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


def inset_box(box: tuple[int, int, int, int], inset: int) -> tuple[int, int, int, int]:
    x1, y1, x2, y2 = box
    max_inset_x = max(0, (x2 - x1 - 1) // 2)
    max_inset_y = max(0, (y2 - y1 - 1) // 2)
    safe_inset = max(0, min(inset, max_inset_x, max_inset_y))
    return x1 + safe_inset, y1 + safe_inset, x2 - safe_inset, y2 - safe_inset


def box_center(box: tuple[int, int, int, int]) -> tuple[int, int]:
    x1, y1, x2, y2 = box
    return (x1 + x2) // 2, (y1 + y2) // 2


def box_size(box: tuple[int, int, int, int]) -> tuple[int, int]:
    x1, y1, x2, y2 = box
    return max(1, x2 - x1), max(1, y2 - y1)


