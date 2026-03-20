from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import TYPE_CHECKING

from ..constants import *
from ..helpers import *

if TYPE_CHECKING:
    from ..app_window import TogCharacterManager


class FormationsPanelMixin:
    def _build_formations_tab(self) -> None:
        self.formations_tab.columnconfigure(0, weight=1)
        self.formations_tab.rowconfigure(0, weight=1)

        self.formations_list_scene = self._make_panel(self.formations_tab)
        self.formations_list_scene.grid(row=0, column=0, sticky="nsew")
        self.formations_list_scene.columnconfigure(0, weight=1)
        self.formations_list_scene.rowconfigure(1, weight=1)

        formations_header = tk.Frame(self.formations_list_scene, bg=SURFACE)
        formations_header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 12))
        formations_header.columnconfigure(0, weight=1)

        title_wrap = tk.Frame(formations_header, bg=SURFACE)
        title_wrap.grid(row=0, column=0, sticky="w")
        tk.Label(
            title_wrap,
            text="Saved Formations",
            bg=SURFACE,
            fg=TEXT,
            font=self.section_font,
        ).pack(anchor="w")
        tk.Label(
            title_wrap,
            textvariable=self.formation_summary_var,
            bg=SURFACE,
            fg=TEXT_MUTED,
            font=self.body_font,
        ).pack(anchor="w", pady=(4, 0))

        self._make_button(
            formations_header,
            "New Formation",
            self.open_new_formation_scene,
            filled=True,
        ).grid(row=0, column=1, sticky="e")

        formations_list_wrap = tk.Frame(self.formations_list_scene, bg=SURFACE)
        formations_list_wrap.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))
        formations_list_wrap.columnconfigure(0, weight=1)
        formations_list_wrap.rowconfigure(0, weight=1)

        self.formations_list_canvas = tk.Canvas(formations_list_wrap, bg=SURFACE, highlightthickness=0, bd=0)
        self.formations_list_canvas.grid(row=0, column=0, sticky="nsew")
        formations_scroll = ttk.Scrollbar(formations_list_wrap, orient="vertical", command=self.formations_list_canvas.yview)
        formations_scroll.grid(row=0, column=1, sticky="ns")
        self.formations_list_canvas.configure(yscrollcommand=formations_scroll.set)

        self.formations_list_container = tk.Frame(self.formations_list_canvas, bg=SURFACE)
        self.formations_list_window = self.formations_list_canvas.create_window((0, 0), window=self.formations_list_container, anchor="nw")
        self.formations_list_container.bind(
            "<Configure>",
            lambda _event: self.formations_list_canvas.configure(scrollregion=self.formations_list_canvas.bbox("all")),
        )
        self.formations_list_canvas.bind(
            "<Configure>",
            self.on_formations_list_canvas_configure,
        )
        self._bind_mousewheel(self.formations_list_canvas, self.formations_list_container)

        self.formations_editor_scene = self._make_panel(self.formations_tab)
        self.formations_editor_scene.grid(row=0, column=0, sticky="nsew")
        self.formations_editor_scene.columnconfigure(0, weight=1)
        self.formations_editor_scene.rowconfigure(1, weight=1)

        formation_editor_header = tk.Frame(self.formations_editor_scene, bg=SURFACE)
        formation_editor_header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 8))
        formation_editor_header.columnconfigure(1, weight=1)

        self._make_button(
            formation_editor_header,
            "Back",
            self.show_formations_list_scene,
            filled=False,
        ).grid(row=0, column=0, rowspan=2, sticky="w", padx=(0, 12))
        tk.Label(
            formation_editor_header,
            textvariable=self.formation_title_var,
            bg=SURFACE,
            fg=TEXT,
            font=self.section_font,
        ).grid(row=0, column=1, sticky="w")
        tk.Label(
            formation_editor_header,
            text="Choose one of the five teams, then drag characters into the formation board.",
            bg=SURFACE,
            fg=TEXT_MUTED,
            font=self.body_font,
            wraplength=760,
            justify="left",
        ).grid(row=1, column=1, sticky="w", pady=(4, 0))

        self.formations_editor_body = tk.Frame(self.formations_editor_scene, bg=SURFACE)
        self.formations_editor_body.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))
        self.formations_editor_body.columnconfigure(0, weight=1)
        self.formations_editor_body.rowconfigure(2, weight=1)

        self.formations_form_frame = tk.Frame(self.formations_editor_body, bg=SURFACE)
        self.formations_form_frame.grid(row=0, column=0, sticky="ew")
        self.formations_form_frame.columnconfigure(0, weight=1)

        roster_scroll_wrap = tk.Frame(self.formations_editor_body, bg=SURFACE)
        roster_scroll_wrap.grid(row=2, column=0, sticky="nsew", pady=(0, 0))
        roster_scroll_wrap.columnconfigure(0, weight=1)
        roster_scroll_wrap.rowconfigure(0, weight=1)

        self.formations_roster_canvas = tk.Canvas(roster_scroll_wrap, bg=SURFACE, highlightthickness=0, bd=0)
        self.formations_roster_canvas.grid(row=0, column=0, sticky="nsew")
        formations_roster_scroll = ttk.Scrollbar(roster_scroll_wrap, orient="vertical", command=self.formations_roster_canvas.yview)
        formations_roster_scroll.grid(row=0, column=1, sticky="ns")
        self.formations_roster_canvas.configure(yscrollcommand=formations_roster_scroll.set)

        self.formations_roster_frame = tk.Frame(self.formations_roster_canvas, bg=SURFACE)
        self.formations_roster_window = self.formations_roster_canvas.create_window((0, 0), window=self.formations_roster_frame, anchor="nw")
        self.formations_roster_frame.bind(
            "<Configure>",
            lambda _event: self.formations_roster_canvas.configure(scrollregion=self.formations_roster_canvas.bbox("all")),
        )
        self.formations_roster_canvas.bind("<Configure>", self.on_formations_roster_canvas_configure)
        self._bind_mousewheel(self.formations_roster_canvas, self.formations_roster_frame)

        self.show_formations_list_scene()
        self.render_formation_editor()

    def render_formation_editor(self) -> None:
        self.sync_active_team_slots()
        for child in self.formations_form_frame.winfo_children():
            child.destroy()
        for child in self.formations_roster_frame.winfo_children():
            child.destroy()

        self.formation_slot_frames.clear()
        self.formation_character_cards = []
        self.formations_form_frame.configure(padx=10, pady=8)
        self.formations_form_frame.columnconfigure(0, weight=1)
        self.formations_roster_frame.configure(padx=10, pady=0)
        self.formations_roster_frame.columnconfigure(0, weight=1)
        self.formations_roster_frame.rowconfigure(0, weight=1)
        self.formations_roster_frame.rowconfigure(1, weight=0)

        details_card = tk.Frame(self.formations_form_frame, bg=SURFACE_MUTED, highlightthickness=1, highlightbackground=BORDER, bd=0, padx=18, pady=18)
        details_card.grid(row=0, column=0, sticky="ew", padx=10, pady=(6, 12))
        details_card.columnconfigure(0, weight=1)
        details_card.columnconfigure(1, weight=1)

        team_field = tk.Frame(details_card, bg=SURFACE_MUTED)
        team_field.grid(row=0, column=0, sticky="ew", padx=10, pady=8)
        team_field.columnconfigure(0, weight=1)
        tk.Label(
            team_field,
            text="Team",
            bg=SURFACE_MUTED,
            fg=TEXT_MUTED,
            font=self.label_font,
        ).grid(row=0, column=0, sticky="w")
        team_picker = ttk.Combobox(
            team_field,
            textvariable=self.team_name_var,
            values=TEAM_OPTIONS,
            state="readonly",
            width=16,
        )
        team_picker.grid(row=1, column=0, sticky="ew", pady=(6, 0), ipady=4)
        team_picker.bind("<<ComboboxSelected>>", self.on_team_selection_changed)
        self._make_input(details_card, "Formation", self.formation_name_var, 0, 1)

        guidance = tk.Label(
            details_card,
            text="Click a roster card to open the full character sheet. Use the Drag button on each card to place characters into slots.",
            bg=SURFACE_MUTED,
            fg=TEXT_MUTED,
            font=self.body_font,
            justify="left",
        )
        guidance.grid(row=1, column=0, columnspan=2, sticky="w", padx=10, pady=(6, 0))

        details_actions = tk.Frame(details_card, bg=SURFACE_MUTED)
        details_actions.grid(row=2, column=0, columnspan=2, sticky="e", padx=10, pady=(12, 0))
        if self.selected_formation_index is None:
            self._make_button(details_actions, "Create", self.create_formation, filled=True).pack(anchor="e")
        else:
            self._make_button(details_actions, "Update", self.update_formation, filled=True).pack(side="left")
            self._make_button(
                details_actions,
                "Delete",
                self.delete_formation,
                filled=True,
                bg=DANGER,
                active_bg="#B71C1C",
            ).pack(side="left", padx=(8, 0))

        board_card = tk.Frame(
            self.formations_form_frame,
            bg=SURFACE,
            highlightthickness=1,
            highlightbackground=BORDER,
            bd=0,
            padx=18,
            pady=18,
        )
        board_card.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 12))
        for column in range(3):
            board_card.columnconfigure(column, weight=1)

        tk.Label(
            board_card,
            text="Formation Board",
            bg=SURFACE,
            fg=TEXT,
            font=self.section_font,
        ).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 12))

        for column_index, slot_key in enumerate(FORMATION_SLOT_ORDER[:3]):
            self._create_slot_widget(board_card, slot_key, 1, column_index)

        tk.Frame(board_card, bg=SURFACE, height=8).grid(row=2, column=0, columnspan=3)
        back_row = tk.Frame(board_card, bg=SURFACE)
        back_row.grid(row=3, column=0, columnspan=3, sticky="ew")
        back_row.columnconfigure(0, weight=1)
        back_row.columnconfigure(1, weight=1)
        self._create_slot_widget(back_row, "back_1", 0, 0, padx=(0, 6))
        self._create_slot_widget(back_row, "back_2", 0, 1, padx=(6, 0))

        roster_card = tk.Frame(
            self.formations_roster_frame,
            bg=SURFACE_MUTED,
            highlightthickness=1,
            highlightbackground=BORDER,
            bd=0,
            padx=18,
            pady=18,
        )
        roster_card.grid(row=0, column=0, sticky="nsew", padx=10, pady=(0, 12))
        roster_card.columnconfigure(0, weight=1)
        roster_card.rowconfigure(2, weight=1)

        roster_header = tk.Frame(roster_card, bg=SURFACE_MUTED)
        roster_header.grid(row=0, column=0, sticky="ew")
        roster_header.columnconfigure(0, weight=1)
        roster_header.columnconfigure(1, weight=0)
        tk.Label(
            roster_header,
            text="Character Roster",
            bg=SURFACE_MUTED,
            fg=TEXT,
            font=self.section_font,
        ).grid(row=0, column=0, sticky="w")

        roster_filters = tk.Frame(roster_header, bg=SURFACE_MUTED)
        roster_filters.grid(row=0, column=1, sticky="e")
        color_filter = ttk.Combobox(
            roster_filters,
            textvariable=self.formation_color_filter_var,
            values=self.get_roster_color_filter_options(),
            state="readonly",
            width=12,
        )
        color_filter.grid(row=0, column=0, padx=(0, 8))
        color_filter.bind("<<ComboboxSelected>>", self.on_roster_filter_changed)
        rarity_filter = ttk.Combobox(
            roster_filters,
            textvariable=self.formation_rarity_filter_var,
            values=self.get_roster_rarity_filter_options(),
            state="readonly",
            width=12,
        )
        rarity_filter.grid(row=0, column=1)
        rarity_filter.bind("<<ComboboxSelected>>", self.on_roster_filter_changed)
        tk.Label(
            roster_card,
            text="Characters already assigned to another team stay visible but cannot be dropped here.",
            bg=SURFACE_MUTED,
            fg=TEXT_MUTED,
            font=self.body_font,
            justify="left",
        ).grid(row=1, column=0, sticky="w", pady=(4, 12))

        roster_grid = tk.Frame(roster_card, bg=SURFACE_MUTED)
        roster_grid.grid(row=2, column=0, sticky="nsew")
        column_count, card_wraplength, _card_width = self.get_roster_layout_metrics()
        self.roster_layout_columns = column_count
        self.roster_layout_key = self.get_roster_layout_key()
        for column in range(column_count):
            roster_grid.columnconfigure(column, weight=1)

        available_rows = self.get_roster_rows_for_active_team()
        for index, row in enumerate(available_rows):
            name = row.get("Name", "").strip()
            if not name:
                continue
            character_key = character_version_key(row)
            card = tk.Frame(roster_grid, bg=SURFACE, highlightthickness=1, highlightbackground=BORDER, bd=0, padx=12, pady=10)
            card.grid(row=index // column_count, column=index % column_count, sticky="ew", padx=6, pady=6)
            card.columnconfigure(1, weight=1)

            icon_canvas = tk.Canvas(card, width=68, height=88, bg=SURFACE, highlightthickness=0, bd=0)
            icon_canvas.grid(row=0, column=0, rowspan=3, sticky="nw")
            image = self.get_summary_image(row.get("Icon", ""), 60, 80)
            preview_box = centered_ratio_box(68, 88, 4)
            border = get_color_border(row.get("Color", ""))
            if image is not None:
                icon_canvas.create_rectangle(*preview_box, outline=border, fill=SURFACE)
                icon_canvas.create_image(34, 44, image=image)
            else:
                icon_canvas.create_rectangle(*preview_box, outline=border, fill=PLACEHOLDER_FILL, width=1)

            name_label = tk.Label(
                card,
                text=character_display_name(row),
                bg=SURFACE,
                fg=TEXT,
                font=self.card_title_font,
                justify="left",
                anchor="w",
                wraplength=card_wraplength,
            )
            name_label.grid(row=0, column=1, sticky="ew", padx=(12, 0))
            meta_text = f"L: {row.get('L', '-') or '-'}   B: {row.get('B', '-') or '-'}   Rarity: {row.get('Rarity', '-') or '-'}"
            meta_label = tk.Label(
                card,
                text=meta_text,
                bg=SURFACE,
                fg=TEXT_MUTED,
                font=self.card_meta_font,
                justify="left",
                anchor="w",
                wraplength=card_wraplength,
            )
            meta_label.grid(row=1, column=1, sticky="ew", padx=(12, 0), pady=(4, 0))
            info_text = f"R: {row.get('R', '-') or '-'}   IW Type: {row.get('IW Type', '-') or '-'}"
            info_label = tk.Label(
                card,
                text=info_text,
                bg=SURFACE,
                fg=TEXT_MUTED,
                font=self.card_meta_font,
                justify="left",
                anchor="w",
                wraplength=card_wraplength,
            )
            info_label.grid(row=2, column=1, sticky="ew", padx=(12, 0), pady=(4, 0))

            icon_canvas.configure(cursor="hand2")
            icon_canvas.bind("<ButtonPress-1>", lambda event, char_key=character_key: self.start_drag_character(event, char_key))
            icon_canvas.bind("<B1-Motion>", self.on_drag_character)
            icon_canvas.bind("<ButtonRelease-1>", self.end_drag_character)

            for widget in (card, name_label, meta_label, info_label):
                widget.bind("<Button-1>", lambda _event, current=row: self.open_character_popup(current))

            self.formation_character_cards.extend(
                [card, icon_canvas, name_label, meta_label, info_label]
            )
            self._bind_mousewheel(self.formations_roster_canvas, card, icon_canvas, name_label, meta_label, info_label)

        self._render_roster_fill_spacer()

    def get_roster_layout_metrics(self) -> tuple[int, int, int]:
        width = self.formations_roster_canvas.winfo_width()
        if width <= 1:
            width = 720
        usable_width = max(260, width - 56)
        column_count = max(1, min(4, usable_width // 320))
        card_width = max(240, usable_width // column_count)
        card_wraplength = max(120, card_width - 116)
        return column_count, card_wraplength, card_width

    def get_roster_layout_key(self) -> tuple[int, int]:
        column_count, _wraplength, card_width = self.get_roster_layout_metrics()
        width_bucket = card_width // 24
        return column_count, width_bucket

    def on_formations_roster_canvas_configure(self, event: tk.Event) -> None:
        self.formations_roster_canvas.itemconfigure(self.formations_roster_window, width=event.width)
        self._render_roster_fill_spacer()
        new_layout_key = self.get_roster_layout_key()
        if new_layout_key != self.roster_layout_key:
            self.render_formation_editor()

    def _render_roster_fill_spacer(self) -> None:
        existing = getattr(self, "formations_roster_spacer", None)
        if existing is not None and existing.winfo_exists():
            existing.destroy()

        canvas_height = self.formations_roster_canvas.winfo_height()
        content_height = 0
        for child in self.formations_roster_frame.winfo_children():
            if child is existing:
                continue
            content_height += child.winfo_reqheight()

        spacer_height = max(0, canvas_height - content_height - 12)
        self.formations_roster_spacer = tk.Frame(
            self.formations_roster_frame,
            bg=SURFACE,
            height=spacer_height,
        )
        self.formations_roster_spacer.grid(row=1, column=0, sticky="ew")
        self.formations_roster_spacer.grid_propagate(False)
        self.formations_roster_canvas.configure(scrollregion=self.formations_roster_canvas.bbox("all"))

    def show_formations_list_scene(self) -> None:
        self.formation_scene_var.set("list")
        self.formations_editor_scene.grid_remove()
        self.formations_list_scene.grid()

    def show_formation_editor_scene(self) -> None:
        self.formation_scene_var.set("editor")
        self.formations_list_scene.grid_remove()
        self.formations_editor_scene.grid()

    def open_new_formation_scene(self) -> None:
        self.clear_formation_form(keep_status=True, reopen=False)
        self.show_formation_editor_scene()
        self.status_var.set("Creating a new formation.")

    def open_character_popup(self, row: dict[str, str]) -> None:
        popup = tk.Toplevel(self)
        popup.title(row.get("Name", "") or "Character Details")
        popup.configure(bg=BACKGROUND)
        popup.geometry("520x680")
        popup.minsize(420, 520)
        popup.transient(self)

        shell = self._make_panel(popup)
        shell.pack(fill="both", expand=True, padx=20, pady=20)
        shell.columnconfigure(1, weight=1)

        icon_canvas = tk.Canvas(shell, width=132, height=173, bg=SURFACE, highlightthickness=0, bd=0)
        icon_canvas.grid(row=0, column=0, rowspan=2, sticky="nw", padx=18, pady=18)
        border = get_color_border(row.get("Color", ""))
        preview_box = centered_ratio_box(PREVIEW_ICON_WIDTH, PREVIEW_ICON_HEIGHT, 8)
        icon_canvas.create_rectangle(*preview_box, outline=border, fill=PLACEHOLDER_FILL, width=1)
        image = self.get_summary_image(row.get("Icon", ""), PREVIEW_ICON_WIDTH - 16, PREVIEW_ICON_HEIGHT - 16)
        if image is not None:
            icon_canvas.create_image(PREVIEW_ICON_WIDTH // 2, PREVIEW_ICON_HEIGHT // 2, image=image)
            icon_canvas.image = image  # type: ignore[attr-defined]

        tk.Label(shell, text=row.get("Name", "") or "Unnamed Character", bg=SURFACE, fg=TEXT, font=self.section_font).grid(row=0, column=1, sticky="w", padx=(0, 18), pady=(18, 4))
        meta_row = tk.Frame(shell, bg=SURFACE)
        meta_row.grid(row=1, column=1, sticky="nw", padx=(0, 18), pady=(0, 18))
        rarity = row.get("Rarity", "")
        color_value = row.get("Color", "")
        iw_type = row.get("IW Type", "")
        color_icon = self.get_color_icon_image(color_value, 18)
        has_meta = False

        def add_meta_separator() -> None:
            tk.Label(
                meta_row,
                text=" | ",
                bg=SURFACE,
                fg=TEXT_MUTED,
                font=self.body_font,
            ).pack(side="left")

        def add_meta_text(text: str) -> None:
            nonlocal has_meta
            if not text:
                return
            if has_meta:
                add_meta_separator()
            tk.Label(
                meta_row,
                text=text,
                bg=SURFACE,
                fg=TEXT_MUTED,
                font=self.body_font,
            ).pack(side="left")
            has_meta = True

        def add_meta_color_icon() -> None:
            nonlocal has_meta
            if color_icon is None and not color_value:
                return
            if has_meta:
                add_meta_separator()
            if color_icon is not None:
                label = tk.Label(meta_row, image=color_icon, bg=SURFACE)
                label.image = color_icon  # type: ignore[attr-defined]
            else:
                label = tk.Label(meta_row, text=color_value, bg=SURFACE, fg=TEXT_MUTED, font=self.body_font)
            label.pack(side="left")
            has_meta = True

        add_meta_text(rarity)
        add_meta_color_icon()
        add_meta_text(iw_type)

        if not has_meta:
            tk.Label(meta_row, text="No metadata", bg=SURFACE, fg=TEXT_MUTED, font=self.body_font).pack(side="left")

        body = tk.Frame(shell, bg=SURFACE, padx=18, pady=0)
        body.grid(row=2, column=0, columnspan=2, sticky="nsew")
        shell.rowconfigure(2, weight=1)
        for column in range(2):
            body.columnconfigure(column, weight=1)

        detail_headers = [header for header in self.headers]
        for index, header in enumerate(detail_headers):
            raw_value = row.get(header, "")
            value = raw_value or "-"
            item = tk.Frame(body, bg=SURFACE_MUTED, padx=12, pady=10, highlightthickness=1, highlightbackground=BORDER)
            item.grid(row=index // 2, column=index % 2, sticky="ew", padx=6, pady=6)
            tk.Label(
                item,
                text=display_character_field_label(header),
                bg=SURFACE_MUTED,
                fg=TEXT_MUTED,
                font=self.label_font,
            ).pack(anchor="w")
            if header == "Color":
                color_icon = self.get_color_icon_image(raw_value, 20)
                if color_icon is not None:
                    value_label = tk.Label(item, image=color_icon, bg=SURFACE_MUTED)
                    value_label.image = color_icon  # type: ignore[attr-defined]
                else:
                    value_label = tk.Label(item, text=value, bg=SURFACE_MUTED, fg=TEXT, font=self.body_font, justify="left", wraplength=180)
            else:
                value_label = tk.Label(item, text=value, bg=SURFACE_MUTED, fg=TEXT, font=self.body_font, justify="left", wraplength=180)
            value_label.pack(anchor="w", pady=(6, 0))

        close_row = tk.Frame(shell, bg=SURFACE, padx=18, pady=18)
        close_row.grid(row=3, column=0, columnspan=2, sticky="e")
        self._make_button(close_row, "Close", popup.destroy, filled=True).pack(anchor="e")

    def _create_slot_widget(
        self,
        parent: tk.Misc,
        slot_key: str,
        row: int,
        column: int,
        columnspan: int = 1,
        padx: tuple[int, int] = (0, 0),
    ) -> None:
        slot = tk.Frame(
            parent,
            bg=SURFACE_MUTED,
            highlightthickness=2,
            highlightbackground=BORDER,
            bd=0,
            padx=12,
            pady=12,
        )
        slot.grid(row=row, column=column, columnspan=columnspan, sticky="nsew", padx=padx, pady=6)
        slot.columnconfigure(1, weight=1)
        slot.slot_key = slot_key  # type: ignore[attr-defined]

        icon_canvas = tk.Canvas(
            slot,
            width=52,
            height=68,
            bg=SURFACE_MUTED,
            highlightthickness=0,
            bd=0,
        )
        icon_canvas.grid(row=0, column=0, sticky="w")

        value_label = tk.Label(
            slot,
            textvariable=self.formation_slot_vars[slot_key],
            bg=SURFACE_MUTED,
            fg=TEXT,
            font=self.card_title_font,
            justify="left",
            anchor="w",
            wraplength=220,
        )
        value_label.grid(row=0, column=1, sticky="ew", padx=(12, 0))

        slot_value = self.formation_slot_keys.get(slot_key, "")
        character_row = self.find_character_row(slot_value)
        border = get_color_border(character_row.get("Color", "") if character_row else "")
        slot_box = centered_ratio_box(52, 68, 4)
        image = self.get_summary_image(character_row.get("Icon", "") if character_row else "", 44, 60)
        icon_canvas.create_rectangle(*slot_box, outline=border, fill=SURFACE if image is not None else PLACEHOLDER_FILL, width=1)
        if image is not None:
            icon_canvas.create_image(26, 34, image=image)
            self.formation_slot_images[slot_key] = image
        else:
            self.formation_slot_images.pop(slot_key, None)
            if not slot_value:
                icon_canvas.create_text(
                    26,
                    34,
                    text="+",
                    fill=TEXT_MUTED,
                    font=self.section_font,
                )

        for widget in (slot, icon_canvas, value_label):
            widget.bind("<Button-1>", lambda _event, current_slot=slot_key: self.on_slot_clicked(current_slot))

        self.formation_slot_frames[slot_key] = slot


    def load_formations(self, select_index: int | None) -> None:
        try:
            self.formations = self.formation_repository.load()
        except Exception as exc:
            messagebox.showerror("Load failed", f"Unable to load formations:\n{exc}")
            self.formations = []
            self.status_var.set("Failed to load formations.")
            return

        self.refresh_formations_list(select_index=select_index)
        self.update_formation_summary()
        self.render_formation_editor()
        if select_index is None or not self.formations:
            self.clear_formation_form(keep_status=True, reopen=False)
        else:
            self.select_formation(min(select_index, len(self.formations) - 1))

    def update_formation_summary(self) -> None:
        team_board_count = 0
        for entry in self.formations:
            teams = entry.get("teams", {})
            for team_name in TEAM_OPTIONS:
                slots = teams.get(team_name, {})
                if any(str(slots.get(slot_key, "") or "").strip() for slot_key in FORMATION_SLOT_ORDER):
                    team_board_count += 1
        self.formation_summary_var.set(
            f"{len(self.formations)} formation(s) with {team_board_count} team board(s)"
        )

    def refresh_formations_list(self, select_index: int | None) -> None:
        for child in self.formations_list_container.winfo_children():
            child.destroy()
        self.formation_preview_images.clear()

        self.formation_preview_columns = self.get_formation_preview_columns()

        if not self.formations:
            empty = tk.Frame(self.formations_list_container, bg=SURFACE, pady=48)
            empty.pack(fill="x")
            tk.Label(
                empty,
                text="No formations yet",
                bg=SURFACE,
                fg=TEXT,
                font=self.section_font,
            ).pack()
            tk.Label(
                empty,
                text="Create a formation to open the editor scene and build a team board.",
                bg=SURFACE,
                fg=TEXT_MUTED,
                font=self.body_font,
            ).pack(pady=(6, 0))
            self.selected_formation_index = None
            return

        if select_index is not None and 0 <= select_index < len(self.formations):
            self.selected_formation_index = select_index
        elif self.selected_formation_index is None or not (0 <= self.selected_formation_index < len(self.formations)):
            self.selected_formation_index = None

        for index, formation in enumerate(self.formations):
            self._add_formation_card(index, formation, selected=index == self.selected_formation_index)

    def _add_formation_card(self, index: int, formation: dict[str, object], selected: bool) -> None:
        bg = PRIMARY_SOFT if selected else SURFACE
        card = tk.Frame(
            self.formations_list_container,
            bg=bg,
            highlightthickness=1,
            highlightbackground=BORDER,
            bd=0,
            padx=14,
            pady=12,
            cursor="hand2",
        )
        card.pack(fill="x", padx=4, pady=6)
        card.columnconfigure(0, weight=1)

        formation_name = str(formation.get("formation_name", "") or "Unnamed Formation")
        teams = formation.get("teams", {})
        active_teams = []
        total_characters = 0
        team_assignments: dict[str, list[str]] = {}
        for team_name in TEAM_OPTIONS:
            slots = teams.get(team_name, {})
            assigned = [
                str(slots.get(slot_key, "") or "").strip()
                for slot_key in FORMATION_SLOT_ORDER
                if str(slots.get(slot_key, "") or "").strip()
            ]
            if assigned:
                active_teams.append(team_name)
                total_characters += len(assigned)
                team_assignments[team_name] = assigned

        team_label = tk.Label(
            card,
            text=", ".join(active_teams) if active_teams else "No teams assigned",
            bg=bg,
            fg=PRIMARY_DARK,
            font=self.label_font,
            anchor="w",
        )
        team_label.grid(row=0, column=0, sticky="w")
        formation_label = tk.Label(card, text=formation_name, bg=bg, fg=TEXT, font=self.card_title_font, anchor="w")
        formation_label.grid(row=1, column=0, sticky="w", pady=(4, 0))
        assigned_label = tk.Label(
            card,
            text=f"{total_characters} character(s) across {len(active_teams)} team(s)" if active_teams else "No characters assigned",
            bg=bg,
            fg=TEXT_MUTED,
            font=self.card_meta_font,
            anchor="w",
            justify="left",
            wraplength=320,
        )
        assigned_label.grid(row=2, column=0, sticky="ew", pady=(6, 0))

        preview_widgets: list[tk.Widget] = []
        if team_assignments:
            previews = tk.Frame(card, bg=bg)
            previews.grid(row=3, column=0, sticky="ew", pady=(10, 0))
            preview_widgets.append(previews)
            preview_columns = self.get_formation_preview_columns()
            for preview_column in range(preview_columns):
                previews.columnconfigure(preview_column, weight=1)

            for preview_index, team_name in enumerate(active_teams):
                members = team_assignments.get(team_name, [])
                preview_row = preview_index // preview_columns
                preview_column = preview_index % preview_columns
                team_tile = tk.Frame(
                    previews,
                    bg=SURFACE if not selected else PRIMARY_SOFT,
                    highlightthickness=1,
                    highlightbackground=BORDER,
                    bd=0,
                    padx=6,
                    pady=6,
                )
                team_tile.grid(
                    row=preview_row,
                    column=preview_column,
                    sticky="w",
                    padx=(0, 6) if preview_column < preview_columns - 1 else (0, 0),
                    pady=(0, 6),
                )
                preview_widgets.append(team_tile)

                team_chip = tk.Label(
                    team_tile,
                    text=team_name,
                    bg=PRIMARY_SOFT if not selected else SURFACE,
                    fg=PRIMARY_DARK,
                    font=self.card_meta_font,
                    padx=6,
                    pady=3,
                )
                team_chip.grid(row=0, column=0, sticky="w", padx=(0, 8))
                preview_widgets.append(team_chip)

                icons_lane = tk.Frame(team_tile, bg=team_tile.cget("bg"))
                icons_lane.grid(row=0, column=1, sticky="ew")
                preview_widgets.append(icons_lane)
                for column_index in range(max(1, len(members))):
                    icons_lane.columnconfigure(column_index, weight=1)

                for member_index, member_key in enumerate(members):
                    member_row = self.find_character_row(member_key)
                    member_icon = tk.Canvas(
                        icons_lane,
                        width=24,
                        height=32,
                        bg=team_tile.cget("bg"),
                        highlightthickness=0,
                        bd=0,
                    )
                    member_icon.grid(row=0, column=member_index, sticky="ew", padx=(0, 6) if member_index < len(members) - 1 else (0, 0))
                    preview_widgets.append(member_icon)
                    box = centered_ratio_box(24, 32, 2)
                    border = get_color_border(member_row.get("Color", "") if member_row else "")
                    image = self.get_summary_image(member_row.get("Icon", "") if member_row else "", 20, 28)
                    member_icon.create_rectangle(
                        *box,
                        outline=border,
                        fill=SURFACE if image is not None else PLACEHOLDER_FILL,
                        width=1,
                    )
                    if image is not None:
                        self.formation_preview_images.append(image)
                        member_icon.image = image  # type: ignore[attr-defined]
                        member_icon.create_image(12, 16, image=image)
                    else:
                        member_icon.create_text(12, 16, text="+", fill=TEXT_MUTED, font=self.card_meta_font)

        actions = tk.Frame(card, bg=bg)
        actions.grid(row=4, column=0, sticky="ew", pady=(10, 0))
        edit_button = self._make_button(actions, "Open", lambda idx=index: self.select_formation(idx), filled=False)
        edit_button.pack(side="left")
        delete_button = self._make_button(
            actions,
            "Delete",
            lambda idx=index: self.delete_formation(idx),
            filled=True,
            bg=DANGER,
            active_bg="#B71C1C",
        )
        delete_button.pack(side="left", padx=(8, 0))

        self._bind_mousewheel(
            self.formations_list_canvas,
            card,
            team_label,
            formation_label,
            assigned_label,
            *preview_widgets,
            actions,
            edit_button,
            delete_button,
        )
        for widget in (card, team_label, formation_label, assigned_label, *preview_widgets):
            widget.bind("<Button-1>", lambda _event, idx=index: self.select_formation(idx))

    def select_formation(self, index: int) -> None:
        if not (0 <= index < len(self.formations)):
            return

        self.selected_formation_index = index
        formation = self.formations[index]
        self.formation_name_var.set(str(formation.get("formation_name", "") or ""))
        self.editor_teams = self.clone_editor_teams(formation.get("teams", {}))
        first_team = self.get_first_populated_team(self.editor_teams)
        self.load_team_slots_into_editor(first_team)

        self.formation_title_var.set(str(formation.get("formation_name", "") or "Unnamed Formation"))
        self.refresh_formations_list(select_index=index)
        self.render_formation_editor()
        self.show_formation_editor_scene()
        self.status_var.set(
            f"Selected formation #{index + 1}: {formation.get('formation_name', '(no name)')}"
        )

    def get_formation_preview_columns(self) -> int:
        width = self.formations_list_canvas.winfo_width()
        if width <= 1:
            width = 420
        usable_width = max(140, width - 36)
        return max(1, min(5, usable_width // 125))

    def on_formations_list_canvas_configure(self, event: tk.Event) -> None:
        self.formations_list_canvas.itemconfigure(self.formations_list_window, width=event.width)
        preview_columns = self.get_formation_preview_columns()
        if (
            preview_columns != self.formation_preview_columns
            and self.formations
            and self.formation_scene_var.get() == "list"
        ):
            self.refresh_formations_list(select_index=self.selected_formation_index)

    def clear_formation_form(self, keep_status: bool = False, reopen: bool = True) -> None:
        self.selected_formation_index = None
        self.formation_name_var.set("")
        self.pending_slot_character = None
        self.pending_slot_origin = None
        self.editor_teams = empty_team_map()
        self.load_team_slots_into_editor(TEAM_OPTIONS[0])

        self.formation_title_var.set("New Formation")
        self.refresh_formations_list(select_index=None)
        self.render_formation_editor()
        if reopen:
            self.show_formation_editor_scene()
        if not keep_status:
            self.status_var.set("Formation editor cleared. Ready for a new team formation.")

    def collect_formation_data(self) -> dict[str, object]:
        self.sync_active_team_slots()
        return {
            "formation_name": self.formation_name_var.get().strip(),
            "teams": self.clone_editor_teams(self.editor_teams),
        }

    def clone_editor_teams(self, teams: object) -> dict[str, dict[str, str]]:
        cloned = empty_team_map()
        if not isinstance(teams, dict):
            return cloned
        for team_name in TEAM_OPTIONS:
            team_slots = teams.get(team_name, {})
            cloned[team_name] = {
                slot_key: str(team_slots.get(slot_key, "") or "").strip()
                for slot_key in FORMATION_SLOT_ORDER
            }
        return cloned

    def get_first_populated_team(self, teams: dict[str, dict[str, str]]) -> str:
        for team_name in TEAM_OPTIONS:
            slots = teams.get(team_name, {})
            if any(str(slots.get(slot_key, "") or "").strip() for slot_key in FORMATION_SLOT_ORDER):
                return team_name
        return TEAM_OPTIONS[0]

    def sync_active_team_slots(self) -> None:
        active_team = self.active_editor_team or TEAM_OPTIONS[0]
        self.editor_teams.setdefault(active_team, empty_slot_map())
        for slot_key in FORMATION_SLOT_ORDER:
            self.editor_teams[active_team][slot_key] = self.formation_slot_keys.get(slot_key, "")

    def load_team_slots_into_editor(self, team_name: str) -> None:
        self.active_editor_team = team_name if team_name in TEAM_OPTIONS else TEAM_OPTIONS[0]
        self.team_name_var.set(self.active_editor_team)
        self.editor_teams.setdefault(self.active_editor_team, empty_slot_map())
        for slot_key in FORMATION_SLOT_ORDER:
            slot_value = self.editor_teams[self.active_editor_team].get(slot_key, "")
            self.formation_slot_keys[slot_key] = slot_value
            self.formation_slot_vars[slot_key].set(
                character_display_name(self.find_character_row(slot_value))
            )

    def on_team_selection_changed(self, _event: tk.Event | None = None) -> None:
        selected_team = self.team_name_var.get().strip() or TEAM_OPTIONS[0]
        self.sync_active_team_slots()
        self.pending_slot_character = None
        self.pending_slot_origin = None
        self.load_team_slots_into_editor(selected_team)
        self.render_formation_editor()
        self.status_var.set(f"Showing {selected_team} for {self.formation_name_var.get().strip() or 'new formation'}.")

    def create_formation(self) -> None:
        previous_formations = self.clone_formations_state()
        try:
            formation = self.prepare_formation_for_save(None)
            self.formations.append(formation)
            self.save_formations()
        except Exception as exc:
            self.formations = previous_formations
            messagebox.showerror("Create failed", str(exc))
            self.status_var.set("Unable to create formation.")
            return

        new_index = self.formations.index(formation)
        self.update_formation_summary()
        self.select_formation(new_index)
        self.status_var.set(
            f"Created formation: {formation.get('formation_name', '(no name)')}"
        )

    def update_formation(self) -> None:
        if self.selected_formation_index is None:
            messagebox.showwarning("No selection", "Select a formation from the list first.")
            return

        previous_formations = self.clone_formations_state()
        index = self.selected_formation_index
        try:
            formation = self.prepare_formation_for_save(index)
            self.formations[index] = formation
            self.save_formations()
        except Exception as exc:
            self.formations = previous_formations
            messagebox.showerror("Update failed", str(exc))
            self.status_var.set("Unable to update formation.")
            return

        self.update_formation_summary()
        self.select_formation(index)
        self.status_var.set(
            f"Updated formation: {formation.get('formation_name', '(no name)')}"
        )

    def delete_formation(self, index: int | None = None) -> None:
        target_index = self.selected_formation_index if index is None else index
        if target_index is None or not (0 <= target_index < len(self.formations)):
            messagebox.showwarning("No selection", "Select a formation from the list first.")
            return

        formation = self.formations[target_index]
        formation_name = str(formation.get("formation_name", "") or "(no name)")
        confirmed = messagebox.askyesno(
            "Delete formation",
            f"Delete formation '{formation_name}'?",
        )
        if not confirmed:
            return

        previous_formations = self.clone_formations_state()
        self.formations.pop(target_index)
        try:
            self.save_formations()
        except Exception as exc:
            self.formations = previous_formations
            messagebox.showerror("Delete failed", str(exc))
            self.status_var.set("Unable to delete formation.")
            return

        self.update_formation_summary()
        if self.formations:
            self.select_formation(min(target_index, len(self.formations) - 1))
        else:
            self.clear_formation_form(keep_status=True, reopen=False)
            self.show_formations_list_scene()
        self.status_var.set(f"Deleted formation: {formation_name}")

    def save_formations(self) -> None:
        self.formation_repository.save(self.formations)
        self.refresh_formations_list(select_index=self.selected_formation_index)

    def clone_formations_state(self) -> list[dict[str, object]]:
        return [
            {
                "formation_name": str(entry.get("formation_name", "")),
                "teams": self.clone_editor_teams(entry.get("teams", {})),
            }
            for entry in self.formations
        ]

    def prepare_formation_for_save(self, exclude_index: int | None) -> dict[str, object]:
        formation = self.collect_formation_data()
        formation_name = str(formation.get("formation_name", "")).strip()
        teams = formation.get("teams", {})

        if not formation_name:
            raise ValueError("Formation name is required.")

        available_names = {
            character_version_key(row)
            for row in self.rows
            if row.get("Name", "").strip()
        }
        all_assigned_names: list[str] = []
        for team_name in TEAM_OPTIONS:
            slots = teams.get(team_name, {})
            assigned = [
                str(slots.get(slot_key, "") or "").strip()
                for slot_key in FORMATION_SLOT_ORDER
                if str(slots.get(slot_key, "") or "").strip()
            ]
            if len(assigned) > 5:
                raise ValueError(f"{team_name} can only contain up to five characters.")
            normalized_names = [character_version_key(self.find_character_row(name) or {"Name": name}) for name in assigned]
            if len(set(normalized_names)) != len(normalized_names):
                raise ValueError(f"A character can only be used once in {team_name}.")
            for name in assigned:
                character_row = self.find_character_row(name)
                if character_row is None or character_version_key(character_row) not in available_names:
                    raise ValueError(f"Character version '{name}' does not exist in the Characters tab.")
            all_assigned_names.extend(assigned)

        if not all_assigned_names:
            raise ValueError("Add at least one character to one of the team boards.")

        all_normalized = [
            character_version_key(self.find_character_row(name) or {"Name": name})
            for name in all_assigned_names
        ]
        if len(set(all_normalized)) != len(all_normalized):
            raise ValueError("A character can only belong to one team inside the same formation.")

        target_formation_key = normalize_team_name(formation_name)
        for index, entry in enumerate(self.formations):
            if exclude_index is not None and index == exclude_index:
                continue
            existing_formation_name = str(entry.get("formation_name", "") or "")
            if normalize_team_name(existing_formation_name) == target_formation_key:
                raise ValueError("A formation with that name already exists.")

        return formation

    def get_character_team(self, character_name: str, exclude_index: int | None = None) -> str | None:
        target_row = self.find_character_row(character_name)
        if target_row is None and not character_name.strip():
            return None
        for index, formation in enumerate(self.formations):
            if exclude_index is not None and index == exclude_index:
                continue
            teams = formation.get("teams", {})
            formation_name = str(formation.get("formation_name", "") or "").strip()
            for team_name in TEAM_OPTIONS:
                slots = teams.get(team_name, {})
                for slot_key in FORMATION_SLOT_ORDER:
                    assigned_name = str(slots.get(slot_key, "") or "").strip()
                    assigned_row = self.find_character_row(assigned_name)
                    if self.rows_match_assignment(target_row, assigned_row, character_name, assigned_name):
                        return f"{formation_name} / {team_name}" if formation_name else team_name
        return None

    def find_character_row(self, character_name: str) -> dict[str, str] | None:
        target_value = (character_name or "").strip()
        if not target_value:
            return None
        for row in self.rows:
            if character_version_key(row) == target_value:
                return row
        target_name = normalize_character_name(target_value)
        for row in self.rows:
            if normalize_character_name(row.get("Name", "")) == target_name:
                return row
        return None

    def rows_match_assignment(
        self,
        left_row: dict[str, str] | None,
        right_row: dict[str, str] | None,
        left_value: str,
        right_value: str,
    ) -> bool:
        if left_row is not None and right_row is not None:
            return character_version_key(left_row) == character_version_key(right_row)
        return normalize_character_name(left_value) == normalize_character_name(right_value)

    def can_assign_character_to_team(
        self,
        character_name: str,
        team_name: str,
        exclude_index: int | None = None,
    ) -> bool:
        existing_team = self.get_character_team_in_editor(character_name)
        if existing_team is None:
            return True
        return normalize_team_name(existing_team) == normalize_team_name(team_name)

    def get_character_team_in_editor(self, character_name: str) -> str | None:
        self.sync_active_team_slots()
        target_row = self.find_character_row(character_name)
        if target_row is None and not character_name.strip():
            return None
        for team_name in TEAM_OPTIONS:
            slots = self.editor_teams.get(team_name, {})
            for slot_key in FORMATION_SLOT_ORDER:
                assigned_name = str(slots.get(slot_key, "") or "").strip()
                assigned_row = self.find_character_row(assigned_name)
                if self.rows_match_assignment(target_row, assigned_row, character_name, assigned_name):
                    return team_name
        return None

    def get_roster_rows_for_active_team(self) -> list[dict[str, str]]:
        self.sync_active_team_slots()
        assigned_keys = {
            assigned_name
            for team_name in TEAM_OPTIONS
            for assigned_name in self.editor_teams.get(team_name, {}).values()
            if assigned_name
        }
        return [
            row
            for row in self.rows
            if row.get("Name", "").strip()
            and self.matches_roster_filters(row)
            and not any(
                self.rows_match_assignment(row, self.find_character_row(assigned_value), character_version_key(row), assigned_value)
                for assigned_value in assigned_keys
            )
        ]

    def matches_roster_filters(self, row: dict[str, str]) -> bool:
        selected_color = self.formation_color_filter_var.get().strip()
        selected_rarity = self.formation_rarity_filter_var.get().strip()
        row_color = (row.get("Color", "") or "").strip()
        row_rarity = (row.get("Rarity", "") or "").strip()
        if selected_color and selected_color != "All Colors" and row_color != selected_color:
            return False
        if selected_rarity and selected_rarity != "All Rarities" and row_rarity != selected_rarity:
            return False
        return True

    def get_roster_color_filter_options(self) -> tuple[str, ...]:
        colors = sorted({(row.get("Color", "") or "").strip() for row in self.rows if (row.get("Color", "") or "").strip()})
        return ("All Colors", *colors)

    def get_roster_rarity_filter_options(self) -> tuple[str, ...]:
        rarities = sorted(
            {(row.get("Rarity", "") or "").strip() for row in self.rows if (row.get("Rarity", "") or "").strip()},
            key=lambda value: RARITY_ORDER.get(value, len(RARITY_ORDER)),
        )
        return ("All Rarities", *rarities)

    def on_roster_filter_changed(self, _event: tk.Event | None = None) -> None:
        self.render_formation_editor()

    def clear_formation_slot(self, slot_key: str) -> None:
        current_value = self.formation_slot_keys.get(slot_key, "").strip()
        if not current_value:
            return
        self.formation_slot_keys[slot_key] = ""
        self.formation_slot_vars[slot_key].set("")
        self.render_formation_editor()
        self.status_var.set(f"Cleared {FORMATION_SLOT_LABELS[slot_key]}.")

    def on_slot_clicked(self, slot_key: str) -> None:
        current_value = self.formation_slot_keys.get(slot_key, "").strip()

        if self.pending_slot_character is None:
            if not current_value:
                return
            self.pending_slot_character = current_value
            self.pending_slot_origin = slot_key
            self.highlight_active_slot(slot_key)
            selected_row = self.find_character_row(current_value)
            self.status_var.set(
                f"Selected {character_display_name(selected_row) or current_value}. Click another slot to move it, or click the same slot to clear it."
            )
            return

        if self.pending_slot_origin == slot_key:
            self.clear_formation_slot(slot_key)
            self.pending_slot_character = None
            self.pending_slot_origin = None
            self.highlight_active_slot(None)
            return

        character_name = self.pending_slot_character
        origin_slot = self.pending_slot_origin
        displaced = self.formation_slot_keys.get(slot_key, "").strip()

        if origin_slot is not None:
            self.formation_slot_keys[origin_slot] = displaced
            self.formation_slot_vars[origin_slot].set(character_display_name(self.find_character_row(displaced)))
        self.formation_slot_keys[slot_key] = character_name
        self.formation_slot_vars[slot_key].set(character_display_name(self.find_character_row(character_name)))
        self.pending_slot_character = None
        self.pending_slot_origin = None
        self.highlight_active_slot(None)
        self.render_formation_editor()
        self.status_var.set(f"Moved {character_display_name(self.find_character_row(character_name)) or character_name} to {FORMATION_SLOT_LABELS[slot_key]}.")

    def start_drag_character(self, event: tk.Event, character_name: str) -> None:
        if not self.can_assign_character_to_team(
            character_name,
            self.team_name_var.get(),
            exclude_index=self.selected_formation_index,
        ):
            return

        self.drag_payload = {"character_name": character_name}
        character_row = self.find_character_row(character_name)
        self.drag_window = tk.Toplevel(self)
        self.drag_window.overrideredirect(True)
        self.drag_window.attributes("-topmost", True)
        self.drag_label = tk.Label(
            self.drag_window,
            text=character_display_name(character_row) or character_name,
            bg=PRIMARY_DARK,
            fg="white",
            padx=10,
            pady=6,
            font=self.card_meta_font,
        )
        self.drag_label.pack()
        self._move_drag_window(event)

    def _move_drag_window(self, event: tk.Event) -> None:
        if self.drag_window is None:
            return
        x = self.winfo_pointerx() + 12
        y = self.winfo_pointery() + 12
        self.drag_window.geometry(f"+{x}+{y}")
        hovered_slot = self.find_slot_under_pointer()
        self.highlight_active_slot(hovered_slot)

    def on_drag_character(self, event: tk.Event) -> None:
        if self.drag_payload is None:
            return
        self._move_drag_window(event)

    def end_drag_character(self, _event: tk.Event) -> None:
        if self.drag_payload is None:
            return

        slot_key = self.find_slot_under_pointer()
        character_name = self.drag_payload["character_name"]
        self.destroy_drag_window()

        if slot_key is None:
            self.status_var.set(f"Drag canceled for {character_name}.")
            return

        self.assign_character_to_slot(character_name, slot_key)

    def destroy_drag_window(self) -> None:
        self.highlight_active_slot(self.pending_slot_origin)
        if self.drag_window is not None:
            self.drag_window.destroy()
        self.drag_window = None
        self.drag_label = None
        self.drag_payload = None

    def find_slot_under_pointer(self) -> str | None:
        hovered = self.winfo_containing(self.winfo_pointerx(), self.winfo_pointery())
        while hovered is not None:
            slot_key = getattr(hovered, "slot_key", None)
            if slot_key:
                return str(slot_key)
            hovered = hovered.master
        return None

    def assign_character_to_slot(self, character_name: str, slot_key: str) -> None:
        team_name = self.team_name_var.get().strip()
        if not team_name:
            messagebox.showwarning("Missing team", "Enter a team name before assigning characters.")
            return
        if not self.can_assign_character_to_team(
            character_name,
            team_name,
            exclude_index=self.selected_formation_index,
        ):
            other_team = self.get_character_team_in_editor(character_name)
            messagebox.showwarning(
                "Character already assigned",
                f"{character_name} is already assigned to team '{other_team}'.",
            )
            return

        for current_slot in FORMATION_SLOT_ORDER:
            if self.formation_slot_keys.get(current_slot, "").strip() == character_name:
                self.formation_slot_keys[current_slot] = ""
                self.formation_slot_vars[current_slot].set("")
        self.formation_slot_keys[slot_key] = character_name
        self.formation_slot_vars[slot_key].set(character_display_name(self.find_character_row(character_name)))
        self.pending_slot_character = None
        self.pending_slot_origin = None
        self.render_formation_editor()
        self.status_var.set(f"Placed {character_display_name(self.find_character_row(character_name)) or character_name} in {FORMATION_SLOT_LABELS[slot_key]}.")

    def highlight_active_slot(self, active_slot: str | None) -> None:
        for slot_key, frame in self.formation_slot_frames.items():
            frame.configure(highlightbackground=PRIMARY if slot_key == active_slot else BORDER)

