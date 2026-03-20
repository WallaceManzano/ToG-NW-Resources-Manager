from __future__ import annotations

from pathlib import Path

APP_TITLE = "ToG Resources Manager"
BASE_DIR = Path(__file__).resolve().parent.parent
DB_DIR = BASE_DIR / "db"
DEFAULT_CHARACTERS_PATH = DB_DIR / "characters.json"
DEFAULT_FORMATIONS_PATH = DB_DIR / "formations.json"
DEFAULT_PACKS_PATH = DB_DIR / "packs.json"
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
]

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
L_ORDER = {"RB": 0, "O": 1, "P": 2, "R": 3, "B": 4, "G": 5, "-": 6, "": 6}
RARITY_ORDER = {"Ex": 0, "SSR+": 1, "XSR+": 2, "SSR": 3}
COLOR_ORDER = {"D": 0, "Y": 1, "R": 2, "G": 3, "B": 4}
SORT_OPTIONS = ("Sort by LB", "Sort by Rarity", "Sort by Color")
FORMATION_SLOT_ORDER = ("front_1", "front_2", "front_3", "back_1", "back_2")
TEAM_OPTIONS = tuple(f"Team {index}" for index in range(1, 6))
BRL_TO_USD_RATE = 6.25
FORMATION_SLOT_LABELS = {
    "front_1": "Front 1",
    "front_2": "Front 2",
    "front_3": "Front 3",
    "back_1": "Back 1",
    "back_2": "Back 2",
}
