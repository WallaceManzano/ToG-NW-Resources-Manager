from __future__ import annotations

import csv
import hashlib
import re
import tkinter as tk
from pathlib import Path
from tkinter import font, messagebox, ttk
from urllib.parse import unquote, urlparse
from urllib.request import Request, urlopen

try:
    from PIL import Image, ImageTk  # type: ignore
except ImportError:
    Image = None
    ImageTk = None


APP_TITLE = "ToG Character Manager"
BASE_DIR = Path(__file__).resolve().parent
DEFAULT_CSV_PATH = BASE_DIR / "characters.csv"
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
    "Type",
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


class CsvRepository:
    def __init__(self, csv_path: Path) -> None:
        self.csv_path = csv_path
        self.headers = list(DEFAULT_HEADERS)

    def ensure_file(self) -> None:
        if self.csv_path.exists():
            return
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)
        with self.csv_path.open("w", newline="", encoding="utf-8-sig") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=self.headers)
            writer.writeheader()

    def load(self) -> list[dict[str, str]]:
        self.ensure_file()
        with self.csv_path.open("r", newline="", encoding="utf-8-sig") as csv_file:
            reader = csv.DictReader(csv_file)
            file_headers = reader.fieldnames or []
            if file_headers:
                self.headers = file_headers

            rows: list[dict[str, str]] = []
            for row in reader:
                normalized = {
                    header: (row.get(header, "") or "").strip()
                    for header in self.headers
                }
                if any(normalized.values()):
                    rows.append(normalized)
        return rows

    def save(self, rows: list[dict[str, str]]) -> None:
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)
        with self.csv_path.open("w", newline="", encoding="utf-8-sig") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=self.headers)
            writer.writeheader()
            for row in rows:
                writer.writerow({header: row.get(header, "") for header in self.headers})


class TogCsvManager(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1440x920")
        self.minsize(1180, 760)
        self.configure(bg=BACKGROUND)

        self.csv_path = DEFAULT_CSV_PATH
        self.repository = CsvRepository(self.csv_path)
        self.headers = list(DEFAULT_HEADERS)
        self.rows: list[dict[str, str]] = []
        self.variables = {header: tk.StringVar() for header in self.headers}
        self.status_var = tk.StringVar(value="Loading character data...")
        self.summary_count_var = tk.StringVar(value="0 characters")
        self.selected_title_var = tk.StringVar(value="New Character")
        self.selected_index: int | None = None
        self.preview_image = None
        self.summary_images: dict[str, tk.PhotoImage] = {}
        self.level_star_images: dict[str, tk.PhotoImage] = {}
        self.active_mousewheel_canvas: tk.Canvas | None = None
        self._mousewheel_bound = False

        self._setup_fonts()
        self._setup_styles()
        self._build_layout()
        self.load_rows(select_index=None)

    def _setup_fonts(self) -> None:
        self.title_font = font.Font(family="Segoe UI Semibold", size=22)
        self.subtitle_font = font.Font(family="Segoe UI", size=10)
        self.section_font = font.Font(family="Segoe UI Semibold", size=13)
        self.card_title_font = font.Font(family="Segoe UI Semibold", size=11)
        self.star_font = font.Font(family="Segoe UI Symbol", size=11)
        self.card_meta_font = font.Font(family="Segoe UI", size=9)
        self.body_font = font.Font(family="Segoe UI", size=10)
        self.label_font = font.Font(family="Segoe UI Semibold", size=9)
        self.status_font = font.Font(family="Segoe UI", size=9)

    def _setup_styles(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(
            "Vertical.TScrollbar",
            troughcolor=BACKGROUND,
            background=PRIMARY_SOFT,
            bordercolor=BACKGROUND,
            arrowcolor=PRIMARY_DARK,
        )

    def _build_layout(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        header = tk.Frame(self, bg=PRIMARY, padx=28, pady=24)
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)
        header.columnconfigure(1, weight=1)

        title_wrap = tk.Frame(header, bg=PRIMARY)
        title_wrap.grid(row=0, column=0, sticky="w")
        tk.Label(
            title_wrap,
            text="Tower of God Character Manager",
            bg=PRIMARY,
            fg="white",
            font=self.title_font,
        ).pack(anchor="w")
        tk.Label(
            title_wrap,
            text="Material-inspired CRUD workspace for your CSV roster.",
            bg=PRIMARY,
            fg="#DCEBFF",
            font=self.subtitle_font,
        ).pack(anchor="w", pady=(4, 0))

        content = tk.Frame(self, bg=BACKGROUND, padx=24, pady=24)
        content.grid(row=1, column=0, sticky="nsew")
        content.columnconfigure(0, weight=3)
        content.columnconfigure(1, weight=4)
        content.rowconfigure(0, weight=1)

        self.summary_panel = self._make_panel(content)
        self.summary_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 16))
        self.summary_panel.columnconfigure(0, weight=1)
        self.summary_panel.rowconfigure(1, weight=1)

        summary_header = tk.Frame(self.summary_panel, bg=SURFACE)
        summary_header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 12))
        summary_header.columnconfigure(0, weight=1)

        tk.Label(
            summary_header,
            text="Character Summary",
            bg=SURFACE,
            fg=TEXT,
            font=self.section_font,
        ).grid(row=0, column=0, sticky="w")
        tk.Label(
            summary_header,
            textvariable=self.summary_count_var,
            bg=SURFACE,
            fg=TEXT_MUTED,
            font=self.body_font,
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

        summary_list_wrap = tk.Frame(self.summary_panel, bg=SURFACE)
        summary_list_wrap.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))
        summary_list_wrap.columnconfigure(0, weight=1)
        summary_list_wrap.rowconfigure(0, weight=1)

        self.summary_canvas = tk.Canvas(summary_list_wrap, bg=SURFACE, highlightthickness=0, bd=0)
        self.summary_canvas.grid(row=0, column=0, sticky="nsew")
        summary_scroll = ttk.Scrollbar(
            summary_list_wrap,
            orient="vertical",
            command=self.summary_canvas.yview,
        )
        summary_scroll.grid(row=0, column=1, sticky="ns")
        self.summary_canvas.configure(yscrollcommand=summary_scroll.set)

        self.summary_container = tk.Frame(self.summary_canvas, bg=SURFACE)
        self.summary_window = self.summary_canvas.create_window(
            (0, 0),
            window=self.summary_container,
            anchor="nw",
        )
        self.summary_container.bind(
            "<Configure>",
            lambda _event: self.summary_canvas.configure(
                scrollregion=self.summary_canvas.bbox("all")
            ),
        )
        self.summary_canvas.bind(
            "<Configure>",
            lambda event: self.summary_canvas.itemconfigure(self.summary_window, width=event.width),
        )
        self._bind_mousewheel(self.summary_canvas, self.summary_container)

        self.editor_panel = self._make_panel(content)
        self.editor_panel.grid(row=0, column=1, sticky="nsew")
        self.editor_panel.columnconfigure(0, weight=1)
        self.editor_panel.rowconfigure(2, weight=1)

        editor_header = tk.Frame(self.editor_panel, bg=SURFACE)
        editor_header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 8))
        editor_header.columnconfigure(0, weight=1)

        tk.Label(
            editor_header,
            textvariable=self.selected_title_var,
            bg=SURFACE,
            fg=TEXT,
            font=self.section_font,
        ).grid(row=0, column=0, sticky="w")
        tk.Label(
            editor_header,
            text="Edit fields below, then create a new row or update the selected one.",
            bg=SURFACE,
            fg=TEXT_MUTED,
            font=self.body_font,
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

        action_bar = tk.Frame(self.editor_panel, bg=SURFACE)
        action_bar.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 8))
        for column in range(4):
            action_bar.columnconfigure(column, weight=1)

        self._make_button(action_bar, "New", self.clear_form, filled=False).grid(
            row=0,
            column=0,
            padx=(0, 10),
            sticky="ew",
        )
        self._make_button(action_bar, "Create", self.create_row, filled=True).grid(
            row=0,
            column=1,
            padx=(0, 10),
            sticky="ew",
        )
        self._make_button(action_bar, "Update", self.update_row, filled=True).grid(
            row=0,
            column=2,
            padx=(0, 10),
            sticky="ew",
        )
        self._make_button(
            action_bar,
            "Delete",
            self.delete_row,
            filled=True,
            bg=DANGER,
            active_bg="#B71C1C",
        ).grid(row=0, column=3, sticky="ew")

        editor_scroll_wrap = tk.Frame(self.editor_panel, bg=SURFACE)
        editor_scroll_wrap.grid(row=2, column=0, sticky="nsew", padx=16, pady=(0, 16))
        editor_scroll_wrap.columnconfigure(0, weight=1)
        editor_scroll_wrap.rowconfigure(0, weight=1)

        self.editor_canvas = tk.Canvas(editor_scroll_wrap, bg=SURFACE, highlightthickness=0, bd=0)
        self.editor_canvas.grid(row=0, column=0, sticky="nsew")
        editor_scroll = ttk.Scrollbar(
            editor_scroll_wrap,
            orient="vertical",
            command=self.editor_canvas.yview,
        )
        editor_scroll.grid(row=0, column=1, sticky="ns")
        self.editor_canvas.configure(yscrollcommand=editor_scroll.set)

        self.form_frame = tk.Frame(self.editor_canvas, bg=SURFACE)
        self.form_window = self.editor_canvas.create_window(
            (0, 0),
            window=self.form_frame,
            anchor="nw",
        )
        self.form_frame.bind(
            "<Configure>",
            lambda _event: self.editor_canvas.configure(scrollregion=self.editor_canvas.bbox("all")),
        )
        self.editor_canvas.bind(
            "<Configure>",
            lambda event: self.editor_canvas.itemconfigure(self.form_window, width=event.width),
        )
        self._bind_mousewheel(self.editor_canvas, self.form_frame)

        self.render_form_fields()

        status_wrap = tk.Frame(self, bg=BACKGROUND, padx=24, pady=0)
        status_wrap.grid(row=2, column=0, sticky="ew", pady=(0, 18))
        status_chip = tk.Frame(status_wrap, bg=PRIMARY_SOFT, padx=14, pady=10)
        status_chip.pack(anchor="w")
        tk.Label(
            status_chip,
            textvariable=self.status_var,
            bg=PRIMARY_SOFT,
            fg=PRIMARY_DARK,
            font=self.status_font,
        ).pack(anchor="w")

    def _make_panel(self, parent: tk.Misc) -> tk.Frame:
        return tk.Frame(
            parent,
            bg=SURFACE,
            highlightthickness=1,
            highlightbackground=BORDER,
            bd=0,
        )

    def _bind_mousewheel(self, canvas: tk.Canvas, *widgets: tk.Widget) -> None:
        if not self._mousewheel_bound:
            self.bind_all("<MouseWheel>", self._on_mousewheel, add="+")
            self.bind_all("<Button-4>", lambda event: self._on_linux_scroll(-1, event), add="+")
            self.bind_all("<Button-5>", lambda event: self._on_linux_scroll(1, event), add="+")
            self._mousewheel_bound = True

        def set_active(_event: tk.Event) -> None:
            self.active_mousewheel_canvas = canvas

        def clear_active(_event: tk.Event) -> None:
            if self.active_mousewheel_canvas is canvas:
                self.active_mousewheel_canvas = None

        for widget in (canvas, *widgets):
            widget.bind("<Enter>", set_active, add="+")
            widget.bind("<Leave>", clear_active, add="+")

    def _on_mousewheel(self, event: tk.Event) -> None:
        canvas = self.active_mousewheel_canvas
        if canvas is None:
            return
        delta = getattr(event, "delta", 0)
        if delta == 0:
            return
        step = -int(delta / 120) if abs(delta) >= 120 else (-1 if delta > 0 else 1)
        canvas.yview_scroll(step, "units")

    def _on_linux_scroll(self, direction: int, _event: tk.Event) -> None:
        canvas = self.active_mousewheel_canvas
        if canvas is None:
            return
        canvas.yview_scroll(direction, "units")

    def _make_button(
        self,
        parent: tk.Misc,
        text: str,
        command,
        filled: bool,
        bg: str | None = None,
        active_bg: str | None = None,
    ) -> tk.Button:
        if filled:
            button_bg = bg or PRIMARY
            button_fg = "white"
            hover_bg = active_bg or PRIMARY_DARK
            border = button_bg
        else:
            button_bg = SURFACE
            button_fg = PRIMARY_DARK
            hover_bg = PRIMARY_SOFT
            border = PRIMARY_SOFT

        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=button_bg,
            fg=button_fg,
            activebackground=hover_bg,
            activeforeground=button_fg,
            relief="flat",
            bd=0,
            padx=14,
            pady=10,
            font=self.label_font,
            cursor="hand2",
            highlightthickness=1,
            highlightbackground=border,
            highlightcolor=border,
        )

    def _make_input(
        self,
        parent: tk.Misc,
        label: str,
        variable: tk.StringVar,
        row: int,
        column: int,
        columnspan: int = 1,
    ) -> None:
        field = tk.Frame(parent, bg=SURFACE)
        field.grid(row=row, column=column, columnspan=columnspan, sticky="ew", padx=10, pady=8)
        field.columnconfigure(0, weight=1)

        tk.Label(
            field,
            text=label,
            bg=SURFACE,
            fg=TEXT_MUTED,
            font=self.label_font,
        ).grid(row=0, column=0, sticky="w")
        tk.Entry(
            field,
            textvariable=variable,
            bg=SURFACE_MUTED,
            fg=TEXT,
            relief="flat",
            bd=0,
            insertbackground=TEXT,
            highlightthickness=1,
            highlightbackground=BORDER,
            highlightcolor=PRIMARY,
            font=self.body_font,
        ).grid(row=1, column=0, sticky="ew", pady=(6, 0), ipady=8)

    def render_form_fields(self) -> None:
        for child in self.form_frame.winfo_children():
            child.destroy()

        self.form_frame.configure(padx=10, pady=8)
        for column in range(3):
            self.form_frame.columnconfigure(column, weight=1)
        
        # 200x262
        icon_card = tk.Frame(
            self.form_frame,
            bg=SURFACE_MUTED,
            highlightthickness=1,
            highlightbackground=BORDER,
            bd=0,
            padx=18,
            pady=18,
        )
        icon_card.grid(row=0, column=0, columnspan=3, sticky="ew", padx=10, pady=(6, 12))
        icon_card.columnconfigure(1, weight=1)

        self.preview_holder = tk.Canvas(
            icon_card,
            width=PREVIEW_ICON_WIDTH,
            height=PREVIEW_ICON_HEIGHT,
            bg=SURFACE,
            highlightthickness=1,
            highlightbackground=BORDER,
            bd=0,
        )
        self.preview_holder.grid(row=0, column=0, rowspan=3, sticky="nw")

        tk.Label(
            icon_card,
            text="Character Icon",
            bg=SURFACE_MUTED,
            fg=TEXT,
            font=self.section_font,
        ).grid(row=0, column=1, sticky="w", padx=(16, 0))
        tk.Label(
            icon_card,
            text="Paste a PNG URL and import it, or keep an existing local path.",
            bg=SURFACE_MUTED,
            fg=TEXT_MUTED,
            font=self.body_font,
        ).grid(row=1, column=1, sticky="w", padx=(16, 0), pady=(4, 10))

        icon_row = tk.Frame(icon_card, bg=SURFACE_MUTED)
        icon_row.grid(row=2, column=1, sticky="ew", padx=(16, 0))
        icon_row.columnconfigure(0, weight=1)

        tk.Entry(
            icon_row,
            textvariable=self.variables["Icon"],
            bg=SURFACE,
            fg=TEXT,
            relief="flat",
            bd=0,
            insertbackground=TEXT,
            highlightthickness=1,
            highlightbackground=BORDER,
            highlightcolor=PRIMARY,
            font=self.body_font,
        ).grid(row=0, column=0, sticky="ew", ipady=8)
        self._make_button(icon_row, "Import PNG URL", self.import_icon_from_form, filled=True).grid(
            row=0,
            column=1,
            padx=(10, 0),
        )

        fields = [header for header in self.headers if header != "Icon"]
        for index, header in enumerate(fields):
            row = 1 + (index // 3)
            column = index % 3
            self._make_input(self.form_frame, header, self.variables[header], row, column)

        self.update_icon_preview()

    def load_rows(self, select_index: int | None) -> None:
        try:
            self.rows = self.repository.load()
        except Exception as exc:
            messagebox.showerror("Load failed", f"Unable to load CSV:\n{exc}")
            self.status_var.set("Failed to load CSV.")
            return

        self.headers = list(self.repository.headers or DEFAULT_HEADERS)
        for header in self.headers:
            self.variables.setdefault(header, tk.StringVar())

        self.summary_images.clear()
        self.render_form_fields()
        self.refresh_summary(select_index=select_index)

        if select_index is None or not self.rows:
            self.clear_form(keep_status=True)
        else:
            self.select_item(min(select_index, len(self.rows) - 1))

        self.summary_count_var.set(f"{len(self.rows)} character(s)")
        self.status_var.set(f"Loaded {len(self.rows)} character(s) from {self.csv_path.name}.")

    def refresh_summary(self, select_index: int | None) -> None:
        for child in self.summary_container.winfo_children():
            child.destroy()

        if not self.rows:
            empty = tk.Frame(self.summary_container, bg=SURFACE, pady=48)
            empty.pack(fill="x")
            tk.Label(
                empty,
                text="No characters yet",
                bg=SURFACE,
                fg=TEXT,
                font=self.section_font,
            ).pack()
            tk.Label(
                empty,
                text="Use the editor on the right to create your first row.",
                bg=SURFACE,
                fg=TEXT_MUTED,
                font=self.body_font,
            ).pack(pady=(6, 0))
            self.selected_index = None
            return

        if select_index is not None and 0 <= select_index < len(self.rows):
            self.selected_index = select_index
        else:
            self.selected_index = None

        for index, row in enumerate(self.rows):
            self._add_summary_card(index, row, selected=index == self.selected_index)

    def _add_summary_card(self, index: int, row: dict[str, str], selected: bool) -> None:
        bg = PRIMARY_SOFT if selected else SURFACE
        border = get_color_border(row.get("Color", ""))
        border_width = 2 if selected else 1

        card = tk.Frame(
            self.summary_container,
            bg=bg,
            highlightthickness=border_width,
            highlightbackground=border,
            bd=0,
            padx=14,
            pady=12,
            cursor="hand2",
        )
        card.pack(fill="x", padx=4, pady=6)
        card.columnconfigure(1, weight=1)

        icon_shell = tk.Canvas(
            card,
            width=SUMMARY_ICON_WIDTH,
            height=SUMMARY_ICON_HEIGHT,
            bg=bg,
            highlightthickness=0,
            bd=0,
        )
        icon_shell.grid(row=0, column=0, rowspan=3, sticky="nw")

        summary_box = centered_ratio_box(SUMMARY_ICON_WIDTH, SUMMARY_ICON_HEIGHT, 4)
        image = self.get_summary_image(row.get("Icon", ""))
        if image is not None:
            icon_shell.create_rectangle(*summary_box, outline=border, fill=SURFACE)
            icon_shell.create_image(SUMMARY_ICON_WIDTH // 2, SUMMARY_ICON_HEIGHT // 2, image=image)
        else:
            icon_shell.create_rectangle(*summary_box, outline=border, fill=PLACEHOLDER_FILL, width=1)

        name = row.get("Name", "") or "Unnamed Character"
        meta = " • ".join(
            part for part in [row.get("Rarity", ""), row.get("Type", "")] if part
        )
        meta_parts = [row.get("Rarity", ""), row.get("Color", ""), row.get("Type", "")]
        meta = " | ".join(part for part in meta_parts if part)
        star_count = get_star_count(row.get("B", ""))
        star_image = self.get_level_star_image(row.get("L", ""))
        star_fallback = "\u2605" * star_count
        stats = "  ".join(
            f"{label}: {value}"
            for label, value in [
                ("R", row.get("R", "")),
                ("EE", row.get("EE", "")),
                ("Rapport", row.get("Rapport", "")),
            ]
            if value
        )

        name_label = tk.Label(card, text=name, bg=bg, fg=TEXT, font=self.card_title_font, anchor="w")
        name_label.grid(row=0, column=1, sticky="ew", padx=(14, 0))
        meta_label = tk.Label(
            card,
            text=meta or "No metadata",
            bg=bg,
            fg=TEXT_MUTED,
            font=self.card_meta_font,
            anchor="w",
        )
        meta_label.grid(row=1, column=1, sticky="ew", padx=(14, 0), pady=(4, 0))
        star_canvas = tk.Canvas(
            card,
            width=120,
            height=20,
            bg=bg,
            highlightthickness=0,
            bd=0,
        )
        star_canvas.grid(row=2, column=1, sticky="w", padx=(14, 0), pady=(6, 0))
        if star_count > 0 and star_image is not None:
            for star_index in range(star_count):
                star_canvas.create_image(10 + (star_index * 18), 10, image=star_image)
        elif star_fallback:
            star_canvas.create_text(
                0,
                10,
                anchor="w",
                text=star_fallback,
                fill=get_level_star_color(row.get("L", "")),
                font=self.star_font,
            )
        else:
            star_canvas.create_text(
                0,
                10,
                anchor="w",
                text="No stars",
                fill=TEXT_MUTED,
                font=self.card_meta_font,
            )
        stats_label = tk.Label(
            card,
            text=stats or "No summary stats",
            bg=bg,
            fg=TEXT_MUTED,
            font=self.card_meta_font,
            anchor="w",
        )
        stats_label.grid(row=3, column=1, sticky="ew", padx=(14, 0), pady=(6, 0))

        self._bind_mousewheel(
            self.summary_canvas,
            card,
            icon_shell,
            name_label,
            meta_label,
            star_canvas,
            stats_label,
        )

        for widget in (card, icon_shell, name_label, meta_label, star_canvas, stats_label):
            widget.bind("<Button-1>", lambda _event, idx=index: self.select_item(idx))

    def get_summary_image(self, icon_value: str) -> tk.PhotoImage | None:
        if not icon_value or is_url(icon_value):
            return None

        icon_path = Path(icon_value)
        if not icon_path.is_absolute():
            icon_path = BASE_DIR / icon_path
        if not icon_path.exists():
            return None

        cache_key = str(icon_path.resolve())
        if cache_key in self.summary_images:
            return self.summary_images[cache_key]

        image: tk.PhotoImage | None = None
        if Image is not None and ImageTk is not None:
            try:
                pil_image = Image.open(icon_path)
                pil_image.thumbnail((SUMMARY_ICON_WIDTH - 8, SUMMARY_ICON_HEIGHT - 8))
                image = ImageTk.PhotoImage(pil_image)
            except Exception:
                image = None

        if image is None:
            try:
                tk_image = tk.PhotoImage(file=str(icon_path))
                width_scale = max(1, tk_image.width() // max(1, SUMMARY_ICON_WIDTH - 8))
                height_scale = max(1, tk_image.height() // max(1, SUMMARY_ICON_HEIGHT - 8))
                scale = max(width_scale, height_scale)
                image = tk_image.subsample(scale, scale) if scale > 1 else tk_image
            except tk.TclError:
                image = None

        if image is not None:
            self.summary_images[cache_key] = image
        return image

    def get_level_star_image(self, value: str) -> tk.PhotoImage | None:
        star_key = value.strip().upper()
        if not star_key:
            return None
        if star_key in self.level_star_images:
            return self.level_star_images[star_key]

        asset_path = STAR_ASSET_PATHS.get(star_key)
        if asset_path is None or not asset_path.exists():
            return None

        image: tk.PhotoImage | None = None
        if Image is not None and ImageTk is not None:
            try:
                pil_image = Image.open(asset_path)
                pil_image.thumbnail((14, 14))
                image = ImageTk.PhotoImage(pil_image)
            except Exception:
                image = None

        if image is None:
            try:
                tk_image = tk.PhotoImage(file=str(asset_path))
                scale = max(1, max(tk_image.width(), tk_image.height()) // 14)
                image = tk_image.subsample(scale, scale) if scale > 1 else tk_image
            except tk.TclError:
                image = None

        if image is not None:
            self.level_star_images[star_key] = image
        return image

    def select_item(self, index: int) -> None:
        if not (0 <= index < len(self.rows)):
            return

        self.selected_index = index
        row = self.rows[index]
        for header in self.headers:
            self.variables[header].set(row.get(header, ""))

        self.selected_title_var.set(row.get("Name", "") or "Unnamed Character")
        self.summary_images.clear()
        self.refresh_summary(select_index=index)
        self.update_icon_preview()
        self.status_var.set(f"Selected character #{index + 1}: {row.get('Name', '(no name)')}")

    def clear_form(self, keep_status: bool = False) -> None:
        self.selected_index = None
        for header in self.headers:
            self.variables[header].set("")

        self.selected_title_var.set("New Character")
        self.summary_images.clear()
        self.refresh_summary(select_index=None)
        self.update_icon_preview()
        if not keep_status:
            self.status_var.set("Editor cleared. Ready for a new character.")

    def collect_form_data(self) -> dict[str, str]:
        return {header: self.variables[header].get().strip() for header in self.headers}

    def create_row(self) -> None:
        row: dict[str, str] | None = None
        try:
            row = self.prepare_row_for_save()
            self.rows.append(row)
            self.repository.save(self.rows)
        except Exception as exc:
            if row is not None and self.rows and self.rows[-1] == row:
                self.rows.pop()
            messagebox.showerror("Create failed", str(exc))
            self.status_var.set("Unable to create character.")
            return

        new_index = len(self.rows) - 1
        self.summary_count_var.set(f"{len(self.rows)} character(s)")
        self.select_item(new_index)
        self.status_var.set(f"Created character: {row.get('Name', '(no name)')}")

    def update_row(self) -> None:
        if self.selected_index is None:
            messagebox.showwarning("No selection", "Select a character from the summary list first.")
            return

        index = self.selected_index
        previous_row = self.rows[index].copy()
        try:
            row = self.prepare_row_for_save()
            self.rows[index] = row
            self.repository.save(self.rows)
        except Exception as exc:
            self.rows[index] = previous_row
            messagebox.showerror("Update failed", str(exc))
            self.status_var.set("Unable to update character.")
            return

        self.select_item(index)
        self.status_var.set(f"Updated character: {row.get('Name', '(no name)')}")

    def delete_row(self) -> None:
        if self.selected_index is None:
            messagebox.showwarning("No selection", "Select a character from the summary list first.")
            return

        index = self.selected_index
        row = self.rows[index]
        item_name = row.get("Name", "(no name)")
        confirmed = messagebox.askyesno("Delete character", f"Delete '{item_name}' from the CSV?")
        if not confirmed:
            return

        deleted_row = self.rows.pop(index)
        try:
            self.repository.save(self.rows)
        except Exception as exc:
            self.rows.insert(index, deleted_row)
            messagebox.showerror("Delete failed", str(exc))
            self.status_var.set("Unable to delete character.")
            return

        self.summary_count_var.set(f"{len(self.rows)} character(s)")
        if self.rows:
            self.select_item(min(index, len(self.rows) - 1))
        else:
            self.clear_form(keep_status=True)
        self.status_var.set(f"Deleted character: {item_name}")

    def prepare_row_for_save(self) -> dict[str, str]:
        row = self.collect_form_data()
        icon_value = row.get("Icon", "")
        if is_url(icon_value):
            row["Icon"] = self.download_icon(icon_value, row.get("Name", ""))
            self.variables["Icon"].set(row["Icon"])
        return row

    def import_icon_from_form(self) -> None:
        icon_value = self.variables["Icon"].get().strip()
        if not icon_value:
            messagebox.showwarning("Missing icon URL", "Paste a PNG image URL into the Icon field first.")
            return

        try:
            if is_url(icon_value):
                saved_path = self.download_icon(icon_value, self.variables["Name"].get().strip())
                self.variables["Icon"].set(saved_path)
                self.status_var.set(f"Imported PNG icon to {saved_path}")
            self.summary_images.clear()
            self.update_icon_preview()
            if self.selected_index is not None:
                self.refresh_summary(select_index=self.selected_index)
        except Exception as exc:
            messagebox.showerror("Icon import failed", str(exc))
            self.status_var.set("Unable to import icon.")

    def download_icon(self, url: str, name_hint: str) -> str:
        ICON_DIR.mkdir(parents=True, exist_ok=True)

        request = Request(url, headers={"User-Agent": "ToG-CSV-Manager/1.0"})
        with urlopen(request, timeout=20) as response:
            content = response.read()
            if not content:
                raise ValueError("The icon URL returned an empty response.")
            content_type = response.info().get_content_type()
            if content_type != "image/png":
                raise ValueError(
                    f"Only PNG icons are supported. Received content type: {content_type}"
                )

        seed = hashlib.sha256(url.encode("utf-8")).hexdigest()[:10]
        basename = sanitize_filename(name_hint or Path(unquote(urlparse(url).path)).stem or "icon")
        filename = f"{basename}_{seed}.png"
        destination = ICON_DIR / filename
        destination.write_bytes(content)
        return destination.relative_to(BASE_DIR).as_posix()

    def update_icon_preview(self) -> None:
        self.preview_holder.delete("all")
        icon_value = self.variables["Icon"].get().strip()
        border = get_color_border(self.variables["Color"].get())
        self.preview_image = None
        self.preview_holder.configure(highlightbackground=border, highlightcolor=border)
        preview_box = centered_ratio_box(PREVIEW_ICON_WIDTH, PREVIEW_ICON_HEIGHT, 8)
        preview_center_x = PREVIEW_ICON_WIDTH // 2
        preview_center_y = PREVIEW_ICON_HEIGHT // 2

        self.preview_holder.create_rectangle(*preview_box, outline=border, fill=PLACEHOLDER_FILL, width=1)

        if not icon_value:
            return

        if is_url(icon_value):
            self.preview_holder.create_text(
                preview_center_x,
                preview_center_y,
                text="PNG URL",
                fill=TEXT_MUTED,
                font=self.body_font,
            )
            return

        icon_path = Path(icon_value)
        if not icon_path.is_absolute():
            icon_path = BASE_DIR / icon_path
        if not icon_path.exists():
            self.preview_holder.create_text(
                preview_center_x,
                preview_center_y,
                text="Missing\nfile",
                fill=TEXT_MUTED,
                font=self.body_font,
                justify="center",
            )
            return

        if Image is not None and ImageTk is not None:
            try:
                image = Image.open(icon_path)
                image.thumbnail((PREVIEW_ICON_WIDTH - 16, PREVIEW_ICON_HEIGHT - 16))
                self.preview_image = ImageTk.PhotoImage(image)
                self.preview_holder.create_image(preview_center_x, preview_center_y, image=self.preview_image)
                return
            except Exception:
                pass

        try:
            tk_image = tk.PhotoImage(file=str(icon_path))
            width_scale = max(1, tk_image.width() // max(1, PREVIEW_ICON_WIDTH - 16))
            height_scale = max(1, tk_image.height() // max(1, PREVIEW_ICON_HEIGHT - 16))
            scale = max(width_scale, height_scale)
            self.preview_image = tk_image.subsample(scale, scale) if scale > 1 else tk_image
            self.preview_holder.create_image(preview_center_x, preview_center_y, image=self.preview_image)
        except tk.TclError:
            self.preview_holder.create_text(
                preview_center_x,
                preview_center_y,
                text="Preview\nunavailable",
                fill=TEXT_MUTED,
                font=self.body_font,
                justify="center",
            )


if __name__ == "__main__":
    app = TogCsvManager()
    app.mainloop()
