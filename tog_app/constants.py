from __future__ import annotations

from pathlib import Path

APP_TITLE = "Tower of God: New World Account Manager"
BASE_DIR = Path(__file__).resolve().parent.parent
DB_DIR = BASE_DIR / "db"
DEFAULT_CHARACTERS_PATH = DB_DIR / "characters.json"
DEFAULT_FORMATIONS_PATH = DB_DIR / "formations.json"
DEFAULT_PACKS_PATH = DB_DIR / "packs.json"
DEFAULT_TASKS_PATH = DB_DIR / "tasks.json"
DEFAULT_TOWER_PROGRESS_PATH = DB_DIR / "tower_progress.json"
ICON_DIR = BASE_DIR / "imported_icons"
ASSETS_DIR = BASE_DIR / "assets"
ICON_RATIO_WIDTH = 200
ICON_RATIO_HEIGHT = 262
SUMMARY_ICON_WIDTH = 84
SUMMARY_ICON_HEIGHT = 110
PREVIEW_ICON_WIDTH = 132
PREVIEW_ICON_HEIGHT = 173
DEFAULT_HEADERS = [
    "Icon",
    "Rarity",
    "Color",
    "Name",
    "L",
    "B",
    "R",
    "EE",
    "Rapport",
    "G1",
    "G2",
    "G3",
    "G4",
    "IW Type",
    "IW1",
    "IW2",
    "IW3",
    "IW4",
    "IW5",
    "IW Status Class",
    "IW Status S4",
    "IW Status S5",
]

CHARACTER_FIELD_LABEL_MAP = {
    "R": "Revolution",
    "G1": "Gear Slot 1",
    "G2": "Gear Slot 2",
    "G3": "Gear Slot 3",
    "G4": "Gear Slot 4",
    "IW1": "IW Slot 1",
    "IW2": "IW Slot 2",
    "IW3": "IW Slot 3",
    "IW4": "IW Slot 4",
    "IW5": "IW Slot 5",
    "IW Status S4": "IW Status Slot 4",
    "IW Status S5": "IW Status Slot 5",
}

COLOR_DISPLAY_MAP = {
    "R": "Red",
    "G": "Green",
    "B": "Blue",
    "Y": "Yellow",
    "D": "Dark",
}

L_DISPLAY_MAP = {
    "RB": "Rainbow",
    "O": "Orange",
    "R": "Red",
    "P": "Purple",
    "B": "Blue",
    "G": "Green",
}

PRIMARY = "#1565C0"
PRIMARY_DARK = "#0D47A1"
PRIMARY_SOFT = "#E3F2FD"
BACKGROUND = "#EEF2F7"
SURFACE = "#FFFFFF"
SURFACE_MUTED = "#F8FAFC"
TEXT = "#1F2937"
TEXT_MUTED = "#6B7280"
BORDER = "#D6DEE8"
PLACEHOLDER_FILL = "#E5EAF1"
PLACEHOLDER_BORDER = "#CBD5E1"
DANGER = "#C62828"
COLOR_BORDER_MAP = {
    "R": "#D32F2F",
    "G": "#2E7D32",
    "B": "#1565C0",
    "Y": "#F9A825",
    "D": "#4A148C",
}
LEVEL_STAR_COLOR_MAP = {
    "RB": "#ffcfc9",
    "O": "#e98904",
    "P": "#5a3286",
    "R": "#b10202",
    "B": "#0a53a8",
    "G": "#11734b",
}
STAR_ASSET_PATHS = {
    "RB": ASSETS_DIR / "star_RB.png",
    "O": ASSETS_DIR / "star_O.png",
    "P": ASSETS_DIR / "star_P.png",
    "R": ASSETS_DIR / "star_R.png",
    "B": ASSETS_DIR / "star_B.png",
    "G": ASSETS_DIR / "star_G.png",
}
COLOR_ICON_ASSET_PATHS = {
    "R": ASSETS_DIR / "color_R.png",
    "G": ASSETS_DIR / "color_G.png",
    "B": ASSETS_DIR / "color_B.png",
    "Y": ASSETS_DIR / "color_Y.png",
    "D": ASSETS_DIR / "color_D.png",
}
CHARACTER_RARITY_OPTIONS = ("EX", "SSR+", "XSR+", "SSR")
CHARACTER_COLOR_OPTIONS = tuple(COLOR_DISPLAY_MAP[code] for code in ("R", "G", "B", "Y", "D"))
CHARACTER_L_OPTIONS = tuple(L_DISPLAY_MAP.get(code, code) for code in ("RB", "O", "R", "P", "B", "G")) + ("",)
CHARACTER_SUMMARY_RARITY_FILTER_OPTIONS = ("All Rarities", *CHARACTER_RARITY_OPTIONS)
CHARACTER_SUMMARY_COLOR_FILTER_OPTIONS = ("All Colors", *CHARACTER_COLOR_OPTIONS)
CHARACTER_SUMMARY_L_FILTER_OPTIONS = (
    "All L Values",
    *(L_DISPLAY_MAP.get(code, code) for code in ("RB", "O", "R", "P", "B", "G")),
    "None",
)
CHARACTER_SUMMARY_R_FILTER_OPTIONS = ("All R Values", "0", "1", "2", "3", "4", "5", "6", "7", "8")
CHARACTER_IW_TYPE_OPTIONS = (
    "Bari",
    "Runda",
    "Rafflesia",
    "Doris",
    "Ei",
    "Abgrund",
    "Sundance",
    "Alocasia",
    "Myeongwoi",
    "Idea",
    "Mago",
    "Raihanna",
    "Sela",
    "Bergamot",
)
L_ORDER = {"RB": 0, "O": 1, "R": 2, "P": 3, "B": 4, "G": 5, "-": 6, "": 6}
RARITY_ORDER = {"EX": 0, "SSR+": 1, "XSR+": 2, "SSR": 3}
COLOR_ORDER = {"D": 0, "Y": 1, "R": 2, "G": 3, "B": 4}
SORT_OPTIONS = ("Sort by LB", "Sort by Rarity", "Sort by Color")
FORMATION_SLOT_ORDER = ("front_1", "front_2", "front_3", "back_1", "back_2")
TEAM_OPTIONS = tuple(f"Team {index}" for index in range(1, 6))
BRL_TO_USD_RATE = 6.25
RED_SUSPENDIUM_PER_BRL = 24.4
TASK_TYPE_OPTIONS = ("Goal",)
TASK_FILTER_ALL = "All Goals"
TASK_FILTER_OPTIONS = (TASK_FILTER_ALL,)
TASK_URGENCY_URGENT = "Urgent"
TASK_URGENCY_NOT_URGENT = "Not Urgent"
TASK_URGENCY_COMPLETED = "Completed"
TASK_URGENCY_OPTIONS = (
    TASK_URGENCY_URGENT,
    TASK_URGENCY_NOT_URGENT,
    TASK_URGENCY_COMPLETED,
)
TASK_URGENCY_ORDER = {
    TASK_URGENCY_URGENT: 0,
    TASK_URGENCY_NOT_URGENT: 1,
    TASK_URGENCY_COMPLETED: 2,
}
TASK_URGENCY_ACCENTS = {
    TASK_URGENCY_URGENT: "#C62828",
    TASK_URGENCY_NOT_URGENT: "#F9A825",
    TASK_URGENCY_COMPLETED: "#2E7D32",
}
TASK_URGENCY_BACKGROUNDS = {
    TASK_URGENCY_URGENT: "#FDECEC",
    TASK_URGENCY_NOT_URGENT: "#FFF8E1",
    TASK_URGENCY_COMPLETED: "#EAF7ED",
}
FORMATION_SLOT_LABELS = {
    "front_1": "Front 1",
    "front_2": "Front 2",
    "front_3": "Front 3",
    "back_1": "Back 1",
    "back_2": "Back 2",
}
TOWER_FILTER_ALL = "All Towers"
TOWER_TRACKED_MODES = (
    {"key": "adventure", "label": "Adventure", "accent": PRIMARY},
    {"key": "hard_adventure", "label": "Hard Adventure", "accent": DANGER},
)
TOWER_MODE_KEYS = tuple(mode["key"] for mode in TOWER_TRACKED_MODES)
TOWER_MODE_LABELS = {mode["key"]: mode["label"] for mode in TOWER_TRACKED_MODES}
TOWER_MODE_ACCENTS = {mode["key"]: mode["accent"] for mode in TOWER_TRACKED_MODES}
TOWER_MODE_FILTER_OPTIONS = (TOWER_FILTER_ALL, *(mode["label"] for mode in TOWER_TRACKED_MODES))
