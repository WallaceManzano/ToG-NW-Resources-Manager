from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import font, ttk

try:
    from PIL import Image, ImageTk  # type: ignore
except ImportError:
    Image = None
    ImageTk = None

from .constants import *
from .helpers import *
from .panels import CharactersPanelMixin, FormationsPanelMixin, PacksPanelMixin
from .repositories import CharacterRepository, FormationRepository, PackRepository


class TogCharacterManager(CharactersPanelMixin, FormationsPanelMixin, PacksPanelMixin, tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1440x920")
        self.minsize(1180, 760)
        self.configure(bg=BACKGROUND)

        self.characters_path = DEFAULT_CHARACTERS_PATH
        self.repository = CharacterRepository(self.characters_path)
        self.formations_path = DEFAULT_FORMATIONS_PATH
        self.formation_repository = FormationRepository(self.formations_path)
        self.packs_path = DEFAULT_PACKS_PATH
        self.pack_repository = PackRepository(self.packs_path)
        self.headers = list(DEFAULT_HEADERS)
        self.rows: list[dict[str, str]] = []
        self.formations: list[dict[str, object]] = []
        self.item_bases: list[dict[str, str]] = []
        self.packs: list[dict[str, object]] = []
        self.variables = {header: tk.StringVar() for header in self.headers}
        self.status_var = tk.StringVar(value="Loading character data...")
        self.summary_count_var = tk.StringVar(value="0 characters")
        self.selected_title_var = tk.StringVar(value="New Character")
        self.sort_mode_var = tk.StringVar(value="Sort by LB")
        self.formation_summary_var = tk.StringVar(value="0 formations across 0 teams")
        self.formation_title_var = tk.StringVar(value="New Formation")
        self.pack_summary_var = tk.StringVar(value="0 packs with 0 catalog items")
        self.pack_title_var = tk.StringVar(value="New Pack")
        self.item_base_title_var = tk.StringVar(value="New Item Base")
        self.item_base_summary_var = tk.StringVar(value="0 catalog items")
        self.team_name_var = tk.StringVar(value=TEAM_OPTIONS[0])
        self.formation_name_var = tk.StringVar()
        self.pack_name_var = tk.StringVar()
        self.pack_price_brl_var = tk.StringVar()
        self.pack_price_usd_var = tk.StringVar(value="US$ 0")
        self.pack_total_value_var = tk.StringVar(value="0")
        self.pack_value_ratio_var = tk.StringVar(value="0")
        self.item_base_name_var = tk.StringVar()
        self.item_base_priority_var = tk.StringVar()
        self.item_base_value_var = tk.StringVar()
        self.item_base_total_var = tk.StringVar(value="0")
        self.formation_color_filter_var = tk.StringVar(value="All Colors")
        self.formation_rarity_filter_var = tk.StringVar(value="All Rarities")
        self.selected_index: int | None = None
        self.selected_formation_index: int | None = None
        self.selected_pack_index: int | None = None
        self.selected_item_base_index: int | None = None
        self.editor_teams: dict[str, dict[str, str]] = empty_team_map()
        self.pack_editor_items: list[dict[str, str]] = []
        self.active_editor_team = TEAM_OPTIONS[0]
        self.preview_image = None
        self.summary_images: dict[str, tk.PhotoImage] = {}
        self.level_star_images: dict[str, tk.PhotoImage] = {}
        self.formation_preview_images: list[tk.PhotoImage] = []
        self.formation_slot_vars = {
            slot_key: tk.StringVar()
            for slot_key in FORMATION_SLOT_ORDER
        }
        self.formation_slot_keys = {slot_key: "" for slot_key in FORMATION_SLOT_ORDER}
        self.formation_slot_frames: dict[str, tk.Frame] = {}
        self.formation_slot_images: dict[str, tk.PhotoImage] = {}
        self.formation_character_cards: list[tk.Widget] = []
        self.drag_payload: dict[str, str] | None = None
        self.drag_window: tk.Toplevel | None = None
        self.drag_label: tk.Label | None = None
        self.pending_slot_character: str | None = None
        self.pending_slot_origin: str | None = None
        self.roster_layout_columns = 0
        self.roster_layout_key: tuple[int, int] = (0, 0)
        self.formation_preview_columns = 0
        self.pack_catalog_layout_key: tuple[int, int] = (0, 0)
        self.formation_scene_var = tk.StringVar(value="list")
        self.pack_scene_var = tk.StringVar(value="list")
        self.active_mousewheel_canvas: tk.Canvas | None = None
        self._mousewheel_bound = False

        self.item_base_priority_var.trace_add("write", self._on_item_base_inputs_changed)
        self.item_base_value_var.trace_add("write", self._on_item_base_inputs_changed)
        self.pack_price_brl_var.trace_add("write", self._on_pack_price_changed)

        self._setup_fonts()
        self._setup_styles()
        self._build_layout()
        self.load_rows(select_index=None)
        self.load_formations(select_index=None)
        self.load_pack_data(select_index=None)

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

        content = tk.Frame(self, bg=BACKGROUND, padx=24, pady=24)
        content.grid(row=1, column=0, sticky="nsew")
        content.columnconfigure(0, weight=1)
        content.rowconfigure(0, weight=1)

        self.notebook = ttk.Notebook(content)
        self.notebook.grid(row=0, column=0, sticky="nsew")

        self.characters_tab = tk.Frame(self.notebook, bg=BACKGROUND)
        self.formations_tab = tk.Frame(self.notebook, bg=BACKGROUND)
        self.packs_tab = tk.Frame(self.notebook, bg=BACKGROUND)
        self.notebook.add(self.characters_tab, text="Characters")
        self.notebook.add(self.formations_tab, text="Formations")
        self.notebook.add(self.packs_tab, text="Packs")
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
        self._build_characters_tab()
        self._build_formations_tab()
        self._build_packs_tab()

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

    def on_tab_changed(self, _event: tk.Event | None = None) -> None:
        selected_tab = self.notebook.select()
        if selected_tab == str(self.formations_tab):
            self.after_idle(self.refresh_formation_tab_visuals)
        elif selected_tab == str(self.packs_tab):
            self.after_idle(self.refresh_pack_tab_visuals)

    def refresh_formation_tab_visuals(self) -> None:
        if self.formation_scene_var.get() == "list":
            self.refresh_formations_list(select_index=self.selected_formation_index)
        else:
            self.render_formation_editor()

    def _on_item_base_inputs_changed(self, *_args: object) -> None:
        self.update_item_base_preview_value()

    def _on_pack_price_changed(self, *_args: object) -> None:
        self.update_pack_metrics()

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

    def get_summary_image(
        self,
        icon_value: str,
        max_width: int | None = None,
        max_height: int | None = None,
    ) -> tk.PhotoImage | None:
        if not icon_value or is_url(icon_value):
            return None

        icon_path = Path(icon_value)
        if not icon_path.is_absolute():
            icon_path = BASE_DIR / icon_path
        if not icon_path.exists():
            return None

        target_width = max(1, max_width or (SUMMARY_ICON_WIDTH - 8))
        target_height = max(1, max_height or (SUMMARY_ICON_HEIGHT - 8))
        cache_key = f"{icon_path.resolve()}|{target_width}x{target_height}"
        if cache_key in self.summary_images:
            return self.summary_images[cache_key]

        image: tk.PhotoImage | None = None
        if Image is not None and ImageTk is not None:
            try:
                pil_image = Image.open(icon_path)
                pil_image.thumbnail((target_width, target_height))
                image = ImageTk.PhotoImage(pil_image)
            except Exception:
                image = None

        if image is None:
            try:
                tk_image = tk.PhotoImage(file=str(icon_path))
                width_scale = max(1, -(-tk_image.width() // target_width))
                height_scale = max(1, -(-tk_image.height() // target_height))
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
