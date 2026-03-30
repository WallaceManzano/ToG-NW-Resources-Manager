from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from tog_app.app_window import TogCharacterManager
from tog_app.constants import (
    BACKGROUND,
    TEAM_OPTIONS,
    DEFAULT_HEADERS,
    PRIMARY_SOFT,
    BORDER,
    PLACEHOLDER_FILL,
    PRIMARY,
    PRIMARY_DARK,
    SUMMARY_ICON_HEIGHT,
    SUMMARY_ICON_WIDTH,
    SURFACE,
    TEXT,
    TEXT_MUTED,
)
from tog_app.helpers import (
    box_center,
    box_size,
    centered_ratio_box,
    display_character_field_label,
    display_color_value,
    empty_team_map,
    get_color_border,
    get_level_star_color,
    get_star_count,
    inset_box,
    is_url,
)
from tog_app.panels.characters import CharactersPanelMixin
from tog_app.panels.formations import FormationsPanelMixin
from tog_app.panels.packs import PacksPanelMixin
from tog_app.panels.tower_progress import TowerProgressPanelMixin

_ORIGINAL_CHARACTER_ADD_SUMMARY_CARD = CharactersPanelMixin._add_summary_card
_ORIGINAL_CHARACTER_CLEAR_FORM = CharactersPanelMixin.clear_form
_ORIGINAL_CHARACTER_REFRESH_SUMMARY = CharactersPanelMixin.refresh_summary
_ORIGINAL_CHARACTER_RENDER_FORM_FIELDS = CharactersPanelMixin.render_form_fields
_ORIGINAL_CHARACTER_SELECT_ITEM = CharactersPanelMixin.select_item
_ORIGINAL_LOAD_PACK_DATA = PacksPanelMixin.load_pack_data
_ORIGINAL_LOAD_TOWER_PROGRESS_ENTRIES = TowerProgressPanelMixin.load_tower_progress_entries
_ORIGINAL_REFRESH_FORMATIONS_LIST = FormationsPanelMixin.refresh_formations_list
_ORIGINAL_RENDER_FORMATION_EDITOR = FormationsPanelMixin.render_formation_editor
_ORIGINAL_SHOW_FORMATION_EDITOR_SCENE = FormationsPanelMixin.show_formation_editor_scene


def _build_layout_lazy(self: TogCharacterManager) -> None:
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
        text="Tower of God: New World Account Manager",
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

    self.tasks_tab = tk.Frame(self.notebook, bg=BACKGROUND)
    self.characters_tab = tk.Frame(self.notebook, bg=BACKGROUND)
    self.formations_tab = tk.Frame(self.notebook, bg=BACKGROUND)
    self.packs_tab = tk.Frame(self.notebook, bg=BACKGROUND)
    self.gacha_tab = tk.Frame(self.notebook, bg=BACKGROUND)
    self.tower_progress_tab = tk.Frame(self.notebook, bg=BACKGROUND)
    self.notebook.add(self.tasks_tab, text="Goals")
    self.notebook.add(self.characters_tab, text="Characters")
    self.notebook.add(self.formations_tab, text="Formations")
    self.notebook.add(self.packs_tab, text="Packs Value")
    self.notebook.add(self.gacha_tab, text="Gacha Simulation")
    self.notebook.add(self.tower_progress_tab, text="Tower Progress")
    self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

    self._initialized_tabs = {"tasks"}
    self._tab_keys_by_id = {
        str(self.tasks_tab): "tasks",
        str(self.characters_tab): "characters",
        str(self.formations_tab): "formations",
        str(self.packs_tab): "packs",
        str(self.gacha_tab): "gacha",
        str(self.tower_progress_tab): "tower_progress",
    }
    self._summary_card_widgets = {}
    self._build_tasks_tab()

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


def is_tab_initialized(self: TogCharacterManager, tab_key: str) -> bool:
    return tab_key in getattr(self, "_initialized_tabs", set())


def _initialize_tab(self: TogCharacterManager, tab_key: str) -> None:
    if self.is_tab_initialized(tab_key):
        return

    self._initialized_tabs.add(tab_key)
    if tab_key == "characters":
        self._build_characters_tab()
        self.load_rows(select_index=self.selected_index)
    elif tab_key == "formations":
        self._build_formations_tab()
        self.load_formations(select_index=self.selected_formation_index)
    elif tab_key == "packs":
        self._build_packs_tab()
        self.load_pack_data(select_index=self.selected_pack_index)
    elif tab_key == "gacha":
        self._build_gacha_tab()
    elif tab_key == "tower_progress":
        self._build_tower_progress_tab()
        self.load_tower_progress_entries(select_index=self.selected_tower_progress_index)


def on_tab_changed_lazy(self: TogCharacterManager, _event: tk.Event | None = None) -> None:
    selected_tab = self.notebook.select()
    tab_key = getattr(self, "_tab_keys_by_id", {}).get(selected_tab, "")
    if not tab_key:
        return

    self._initialize_tab(tab_key)
    if tab_key == "tasks":
        self.after_idle(self.refresh_tasks_tab_visuals)
    elif tab_key == "characters":
        self.after_idle(self.refresh_characters_tab_visuals)
    elif tab_key == "formations":
        self.after_idle(self.refresh_formation_tab_visuals)
    elif tab_key == "packs":
        self.after_idle(self.refresh_pack_tab_visuals)
    elif tab_key == "gacha":
        self.after_idle(self.refresh_gacha_tab_visuals)
    elif tab_key == "tower_progress":
        self.after_idle(self.refresh_tower_progress_tab_visuals)


def refresh_characters_tab_visuals(self: TogCharacterManager) -> None:
    if not self.is_tab_initialized("characters"):
        return
    self.refresh_summary(select_index=self.selected_index)
    self.update_summary_count()
    self.update_icon_preview()


def refresh_formation_tab_visuals_lazy(self: TogCharacterManager) -> None:
    if not self.is_tab_initialized("formations"):
        return
    if self.formation_scene_var.get() == "list":
        self.refresh_formations_list(select_index=self.selected_formation_index)
    else:
        self.render_formation_editor()


def load_rows_lazy(self: TogCharacterManager, select_index: int | None) -> None:
    try:
        self.rows = self.repository.load()
    except Exception as exc:
        messagebox.showerror("Load failed", f"Unable to load character data:\n{exc}")
        self.status_var.set("Failed to load character data.")
        return

    self.headers = list(self.repository.headers or DEFAULT_HEADERS)
    for header in self.headers:
        self.variables.setdefault(header, tk.StringVar())

    self.apply_current_sort(save=False)
    self.summary_images.clear()

    if self.is_tab_initialized("characters"):
        if (
            getattr(self, "preview_holder", None) is None
            or not self.preview_holder.winfo_exists()
            or getattr(self, "_character_form_rendered_headers", ()) != tuple(self.headers)
        ):
            self.render_form_fields()
        self.refresh_summary(select_index=select_index)
        self.render_character_action_bar()

        if select_index is None or not self.rows:
            self.clear_form(keep_status=True)
        else:
            self.select_item(min(select_index, len(self.rows) - 1))
    else:
        if select_index is None or not self.rows:
            self.selected_index = None
            self.selected_title_var.set("New Character")
        else:
            self.selected_index = min(select_index, len(self.rows) - 1)
            selected_row = self.rows[self.selected_index]
            self.selected_title_var.set(selected_row.get("Name", "") or "Unnamed Character")

    if self.is_tab_initialized("formations"):
        self.refresh_formations_list(select_index=self.selected_formation_index)
        self.render_formation_editor()
    if hasattr(self, "on_character_rows_loaded"):
        self.on_character_rows_loaded()

    self.update_summary_count()
    self.status_var.set(f"Loaded {len(self.rows)} character(s) from {self.characters_path.name}.")


def _reset_formation_editor_state(self: TogCharacterManager) -> None:
    self.selected_formation_index = None
    self.formation_name_var.set("")
    self.team_note_var.set("")
    self.pending_slot_character = None
    self.pending_slot_origin = None
    self.editor_teams = empty_team_map()
    self.load_team_slots_into_editor(TEAM_OPTIONS[0])
    self.formation_title_var.set("New Formation")
    self._formation_editor_dirty = True


def render_formation_editor_guarded(
    self: TogCharacterManager,
    preserve_editor_scroll: bool = False,
    preserve_roster_scroll: bool = False,
    reset_roster_scroll: bool = False,
    **kwargs: object,
) -> None:
    if not self.is_tab_initialized("formations"):
        return
    force_render = bool(kwargs.pop("force_render", False))
    if not force_render and self.formation_scene_var.get() != "editor":
        self._formation_editor_dirty = True
        return
    self._formation_editor_dirty = False
    _ORIGINAL_RENDER_FORMATION_EDITOR(
        self,
        preserve_editor_scroll=preserve_editor_scroll,
        preserve_roster_scroll=preserve_roster_scroll,
        reset_roster_scroll=reset_roster_scroll,
        **kwargs,
    )


def refresh_formations_list_guarded(self: TogCharacterManager, select_index: int | None) -> None:
    if not self.is_tab_initialized("formations"):
        return
    _ORIGINAL_REFRESH_FORMATIONS_LIST(self, select_index)


def load_formations_lazy(self: TogCharacterManager, select_index: int | None) -> None:
    try:
        self.formations = self.formation_repository.load()
    except Exception as exc:
        messagebox.showerror("Load failed", f"Unable to load formations:\n{exc}")
        self.formations = []
        self.status_var.set("Failed to load formations.")
        return

    self.update_formation_summary()
    if not self.is_tab_initialized("formations"):
        if select_index is None or not self.formations:
            self.selected_formation_index = None
        else:
            self.selected_formation_index = min(select_index, len(self.formations) - 1)
        return

    self.refresh_formations_list(select_index=select_index)
    if self.formation_scene_var.get() != "editor":
        if select_index is None or not self.formations:
            _reset_formation_editor_state(self)
        else:
            self.selected_formation_index = min(select_index, len(self.formations) - 1)
            self._formation_editor_dirty = True
        return

    if select_index is None or not self.formations:
        _reset_formation_editor_state(self)
        self.render_formation_editor(force_render=True)
    else:
        self.select_formation(min(select_index, len(self.formations) - 1))


def show_formation_editor_scene_tracking(self: TogCharacterManager) -> None:
    _ORIGINAL_SHOW_FORMATION_EDITOR_SCENE(self)
    if getattr(self, "_formation_editor_dirty", True):
        self.render_formation_editor(force_render=True)


def load_pack_data_lazy(self: TogCharacterManager, select_index: int | None) -> None:
    if not self.is_tab_initialized("packs"):
        return
    _ORIGINAL_LOAD_PACK_DATA(self, select_index)


def load_tower_progress_entries_lazy(self: TogCharacterManager, select_index: int | None) -> None:
    if not self.is_tab_initialized("tower_progress"):
        return
    _ORIGINAL_LOAD_TOWER_PROGRESS_ENTRIES(self, select_index)


def _collect_descendants(widget: tk.Widget) -> list[tk.Widget]:
    descendants: list[tk.Widget] = []
    for child in widget.winfo_children():
        descendants.append(child)
        descendants.extend(_collect_descendants(child))
    return descendants


def _drain_summary_image_queue(self: TogCharacterManager) -> None:
    current_token = getattr(self, "_summary_refresh_token", 0)
    queue: list[tuple[int, int]] = getattr(self, "_summary_image_queue", [])
    if not queue:
        self._summary_image_after = None
        return

    batch_size = 6
    for _ in range(min(batch_size, len(queue))):
        token, index = queue.pop(0)
        if token != current_token:
            continue

        bundle = getattr(self, "_summary_card_widgets", {}).get(index)
        if bundle is None:
            continue

        icon_shell: tk.Canvas = bundle["icon_shell"]
        if not icon_shell.winfo_exists():
            continue

        row = bundle["row"]
        border = get_color_border(row.get("Color", ""))
        summary_box = centered_ratio_box(SUMMARY_ICON_WIDTH, SUMMARY_ICON_HEIGHT, 4)
        image_box = inset_box(summary_box, 2)
        image_width, image_height = box_size(image_box)
        image_center_x, image_center_y = box_center(image_box)

        icon_shell.delete("all")
        image = self.get_summary_image(row.get("Icon", ""), image_width, image_height)
        if image is not None:
            icon_shell.create_rectangle(*summary_box, outline=border, fill=SURFACE)
            icon_shell.create_image(image_center_x, image_center_y, image=image)
            bundle["summary_image"] = image
        else:
            icon_shell.create_rectangle(*summary_box, outline=border, fill=PLACEHOLDER_FILL, width=1)

    if queue:
        self._summary_image_after = self.after(1, lambda: _drain_summary_image_queue(self))
    else:
        self._summary_image_after = None


def _set_character_summary_card_selected(self: TogCharacterManager, index: int | None, selected: bool) -> None:
    if index is None:
        return
    card_widgets = getattr(self, "_summary_card_widgets", {})
    bundle = card_widgets.get(index)
    if bundle is None:
        return

    row = bundle["row"]
    bg = PRIMARY_SOFT if selected else SURFACE
    border = get_color_border(row.get("Color", ""))
    border_width = 2 if selected else 1
    card = bundle["card"]
    card.configure(bg=bg, highlightbackground=border, highlightthickness=border_width)

    for widget in bundle["widgets"]:
        try:
            widget.configure(bg=bg)
        except tk.TclError:
            pass

    icon_shell = bundle["icon_shell"]
    if icon_shell.winfo_exists():
        icon_shell.configure(bg=bg)


def _add_summary_card_tracking(
    self: TogCharacterManager,
    index: int,
    row: dict[str, str],
    selected: bool,
) -> None:
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
    icon_shell.create_rectangle(*summary_box, outline=border, fill=PLACEHOLDER_FILL, width=1)

    name = row.get("Name", "") or "Unnamed Character"
    rarity = row.get("Rarity", "")
    color_value = row.get("Color", "")
    color_display = display_color_value(color_value)
    iw_type = row.get("IW Type", "")
    iw_status_class = row.get("IW Status Class", "")
    iw_status_s4 = row.get("IW Status S4", "")
    iw_status_s5 = row.get("IW Status S5", "")
    iw_text = "" if iw_status_class == "" else f"{iw_status_class} {iw_status_s4}/{iw_status_s5}"

    color_icon = self.get_color_icon_image(color_value, 16)
    star_count = get_star_count(row.get("B", ""))
    star_image = self.get_level_star_image(row.get("L", ""))
    star_fallback = "\u2605" * star_count
    stats = "  ".join(
        f"{label}: {value}"
        for label, value in [
            (display_character_field_label("R"), row.get("R", "")),
            ("EE", row.get("EE", "")),
            ("Rapport", row.get("Rapport", "")),
        ]
        if value
    )

    name_label = tk.Label(card, text=name, bg=bg, fg=TEXT, font=self.card_title_font, anchor="w")
    name_label.grid(row=0, column=1, sticky="ew", padx=(14, 0))

    meta_row = tk.Frame(card, bg=bg)
    meta_row.grid(row=1, column=1, sticky="w", padx=(14, 0), pady=(4, 0))
    meta_widgets: list[tk.Widget] = [meta_row]
    has_meta = False

    def add_meta_separator() -> None:
        separator = tk.Label(
            meta_row,
            text=" | ",
            bg=bg,
            fg=TEXT_MUTED,
            font=self.card_meta_font,
        )
        separator.pack(side="left")
        meta_widgets.append(separator)

    def add_meta_text(text: str) -> None:
        nonlocal has_meta
        if not text:
            return
        if has_meta:
            add_meta_separator()
        label = tk.Label(
            meta_row,
            text=text,
            bg=bg,
            fg=TEXT_MUTED,
            font=self.card_meta_font,
            anchor="w",
        )
        label.pack(side="left")
        meta_widgets.append(label)
        has_meta = True

    def add_meta_color_icon() -> None:
        nonlocal has_meta
        if color_icon is None and not color_value:
            return
        if has_meta:
            add_meta_separator()
        if color_icon is not None:
            label = tk.Label(
                meta_row,
                image=color_icon,
                bg=bg,
                fg=TEXT_MUTED,
                font=self.card_meta_font,
                compound="left",
                anchor="w",
            )
            label.image = color_icon  # type: ignore[attr-defined]
        else:
            label = tk.Label(
                meta_row,
                text=color_display or color_value,
                bg=bg,
                fg=TEXT_MUTED,
                font=self.card_meta_font,
                anchor="w",
            )
        label.pack(side="left")
        meta_widgets.append(label)
        has_meta = True

    add_meta_text(rarity)
    add_meta_color_icon()
    add_meta_text(f"{iw_type} {iw_text}")

    if not has_meta:
        meta_label = tk.Label(
            meta_row,
            text="No metadata",
            bg=bg,
            fg=TEXT_MUTED,
            font=self.card_meta_font,
            anchor="w",
        )
        meta_label.pack(side="left")
        meta_widgets.append(meta_label)

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
        *meta_widgets,
        star_canvas,
        stats_label,
    )

    for widget in (card, icon_shell, name_label, *meta_widgets, star_canvas, stats_label):
        widget.bind("<Button-1>", lambda _event, idx=index: self.select_item(idx))

    self._summary_card_widgets[index] = {
        "card": card,
        "row": row.copy(),
        "widgets": _collect_descendants(card),
        "icon_shell": icon_shell,
    }
    self._summary_image_queue.append((self._summary_refresh_token, index))


def render_form_fields_tracking(self: TogCharacterManager) -> None:
    _ORIGINAL_CHARACTER_RENDER_FORM_FIELDS(self)
    self._character_form_rendered_headers = tuple(self.headers)


def refresh_summary_tracking(self: TogCharacterManager, select_index: int | None) -> None:
    pending_after = getattr(self, "_summary_image_after", None)
    if pending_after is not None:
        try:
            self.after_cancel(pending_after)
        except tk.TclError:
            pass
    self._summary_image_after = None
    self._summary_refresh_token = getattr(self, "_summary_refresh_token", 0) + 1
    self._summary_image_queue = []
    self._summary_card_widgets = {}
    _ORIGINAL_CHARACTER_REFRESH_SUMMARY(self, select_index)
    if self._summary_image_queue:
        self._summary_image_after = self.after(1, lambda: _drain_summary_image_queue(self))


def select_item_fast(self: TogCharacterManager, index: int) -> None:
    if not (0 <= index < len(self.rows)):
        return

    previous_index = self.selected_index
    self.selected_index = index
    row = self.rows[index]
    self._load_character_into_form(index)

    if getattr(self, "_summary_card_widgets", None):
        if previous_index != index:
            _set_character_summary_card_selected(self, previous_index, False)
            _set_character_summary_card_selected(self, index, True)
    else:
        _ORIGINAL_CHARACTER_SELECT_ITEM(self, index)
        return

    self.update_summary_count()
    self.render_character_action_bar()
    self.status_var.set(f"Selected character #{index + 1}: {row.get('Name', '(no name)')}")


def clear_form_fast(self: TogCharacterManager, keep_status: bool = False) -> None:
    previous_index = self.selected_index
    self.selected_index = None
    self._reset_character_form_inputs()

    if getattr(self, "_summary_card_widgets", None):
        _set_character_summary_card_selected(self, previous_index, False)
    else:
        _ORIGINAL_CHARACTER_CLEAR_FORM(self, keep_status=keep_status)
        return

    self.update_summary_count()
    self.render_character_action_bar()
    if not keep_status:
        self.status_var.set("Editor cleared. Ready for a new character.")


def update_icon_preview_fast(self: TogCharacterManager) -> None:
    self._refresh_character_color_field_icon()
    preview_holder = getattr(self, "preview_holder", None)
    if preview_holder is None or not preview_holder.winfo_exists():
        return

    preview_holder.delete("all")
    icon_value = self.variables["Icon"].get().strip()
    border = get_color_border(self.variables["Color"].get())
    self.preview_image = None
    preview_holder.configure(highlightbackground=border, highlightcolor=border)
    preview_box = centered_ratio_box(preview_holder.winfo_reqwidth(), preview_holder.winfo_reqheight(), 8)
    image_box = inset_box(preview_box, 2)
    image_width, image_height = box_size(image_box)
    preview_center_x, preview_center_y = box_center(image_box)

    preview_holder.create_rectangle(*preview_box, outline=border, fill=PLACEHOLDER_FILL, width=1)

    if not icon_value:
        return

    if is_url(icon_value):
        preview_holder.create_text(
            preview_center_x,
            preview_center_y,
            text="Image URL",
            fill=TEXT_MUTED,
            font=self.body_font,
        )
        return

    image = self.get_summary_image(icon_value, image_width, image_height)
    if image is not None:
        self.preview_image = image
        preview_holder.create_image(preview_center_x, preview_center_y, image=self.preview_image)
        return

    preview_holder.create_text(
        preview_center_x,
        preview_center_y,
        text="Preview\nunavailable",
        fill=TEXT_MUTED,
        font=self.body_font,
        justify="center",
    )


def apply_startup_perf_patch() -> None:
    TogCharacterManager._build_layout = _build_layout_lazy
    TogCharacterManager.is_tab_initialized = is_tab_initialized
    TogCharacterManager._initialize_tab = _initialize_tab
    TogCharacterManager.on_tab_changed = on_tab_changed_lazy
    TogCharacterManager.refresh_characters_tab_visuals = refresh_characters_tab_visuals
    TogCharacterManager.refresh_formation_tab_visuals = refresh_formation_tab_visuals_lazy

    CharactersPanelMixin.load_rows = load_rows_lazy
    CharactersPanelMixin._add_summary_card = _add_summary_card_tracking
    CharactersPanelMixin.render_form_fields = render_form_fields_tracking
    CharactersPanelMixin.refresh_summary = refresh_summary_tracking
    CharactersPanelMixin.select_item = select_item_fast
    CharactersPanelMixin.clear_form = clear_form_fast
    CharactersPanelMixin.update_icon_preview = update_icon_preview_fast

    FormationsPanelMixin.load_formations = load_formations_lazy
    FormationsPanelMixin.refresh_formations_list = refresh_formations_list_guarded
    FormationsPanelMixin.render_formation_editor = render_formation_editor_guarded
    FormationsPanelMixin.show_formation_editor_scene = show_formation_editor_scene_tracking
    PacksPanelMixin.load_pack_data = load_pack_data_lazy
    TowerProgressPanelMixin.load_tower_progress_entries = load_tower_progress_entries_lazy
