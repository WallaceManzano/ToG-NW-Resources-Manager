from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import TYPE_CHECKING

from ..constants import *
from ..helpers import *

if TYPE_CHECKING:
    from ..app_window import TogCharacterManager


class PacksPanelMixin:
    def _build_packs_tab(self) -> None:
        self.packs_tab.columnconfigure(0, weight=1)
        self.packs_tab.rowconfigure(0, weight=1)

        self.packs_list_scene = self._make_panel(self.packs_tab)
        self.packs_list_scene.grid(row=0, column=0, sticky="nsew")
        self.packs_list_scene.columnconfigure(0, weight=1)
        self.packs_list_scene.rowconfigure(1, weight=1)

        packs_header = tk.Frame(self.packs_list_scene, bg=SURFACE)
        packs_header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 12))
        packs_header.columnconfigure(0, weight=1)

        title_wrap = tk.Frame(packs_header, bg=SURFACE)
        title_wrap.grid(row=0, column=0, sticky="w")
        tk.Label(
            title_wrap,
            text="Saved Packs",
            bg=SURFACE,
            fg=TEXT,
            font=self.section_font,
        ).pack(anchor="w")
        tk.Label(
            title_wrap,
            textvariable=self.pack_summary_var,
            bg=SURFACE,
            fg=TEXT_MUTED,
            font=self.body_font,
        ).pack(anchor="w", pady=(4, 0))

        list_actions = tk.Frame(packs_header, bg=SURFACE)
        list_actions.grid(row=0, column=1, sticky="e")
        self._make_button(
            list_actions,
            "Manage Item Base",
            self.open_item_base_manager,
            filled=False,
        ).pack(side="left")
        self._make_button(
            list_actions,
            "New Pack",
            self.open_new_pack_scene,
            filled=True,
        ).pack(side="left", padx=(8, 0))

        packs_list_wrap = tk.Frame(self.packs_list_scene, bg=SURFACE)
        packs_list_wrap.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))
        packs_list_wrap.columnconfigure(0, weight=1)
        packs_list_wrap.rowconfigure(0, weight=1)

        self.packs_list_canvas = tk.Canvas(packs_list_wrap, bg=SURFACE, highlightthickness=0, bd=0)
        self.packs_list_canvas.grid(row=0, column=0, sticky="nsew")
        packs_scroll = ttk.Scrollbar(packs_list_wrap, orient="vertical", command=self.packs_list_canvas.yview)
        packs_scroll.grid(row=0, column=1, sticky="ns")
        self.packs_list_canvas.configure(yscrollcommand=packs_scroll.set)

        self.packs_list_container = tk.Frame(self.packs_list_canvas, bg=SURFACE)
        self.packs_list_window = self.packs_list_canvas.create_window((0, 0), window=self.packs_list_container, anchor="nw")
        self.packs_list_container.bind(
            "<Configure>",
            lambda _event: self.packs_list_canvas.configure(scrollregion=self.packs_list_canvas.bbox("all")),
        )
        self.packs_list_canvas.bind(
            "<Configure>",
            lambda event: self.packs_list_canvas.itemconfigure(self.packs_list_window, width=event.width),
        )
        self._bind_mousewheel(self.packs_list_canvas, self.packs_list_container)

        self.packs_editor_scene = self._make_panel(self.packs_tab)
        self.packs_editor_scene.grid(row=0, column=0, sticky="nsew")
        self.packs_editor_scene.columnconfigure(0, weight=1)
        self.packs_editor_scene.rowconfigure(1, weight=1)

        editor_header = tk.Frame(self.packs_editor_scene, bg=SURFACE)
        editor_header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 8))
        editor_header.columnconfigure(1, weight=1)

        self._make_button(
            editor_header,
            "Back",
            self.show_packs_list_scene,
            filled=False,
        ).grid(row=0, column=0, rowspan=2, sticky="w", padx=(0, 12))
        tk.Label(
            editor_header,
            textvariable=self.pack_title_var,
            bg=SURFACE,
            fg=TEXT,
            font=self.section_font,
        ).grid(row=0, column=1, sticky="w")
        tk.Label(
            editor_header,
            text="Choose items from the global item base catalog, then compare the total pack value against the BRL price converted using 1 USD = 6.25 BRL.",
            bg=SURFACE,
            fg=TEXT_MUTED,
            font=self.body_font,
            wraplength=760,
            justify="left",
        ).grid(row=1, column=1, sticky="w", pady=(4, 0))
        self._make_button(
            editor_header,
            "Manage Item Base",
            self.open_item_base_manager,
            filled=False,
        ).grid(row=0, column=2, rowspan=2, sticky="e")

        self.packs_editor_body = tk.Frame(self.packs_editor_scene, bg=SURFACE)
        self.packs_editor_body.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))
        self.packs_editor_body.columnconfigure(0, weight=1)
        self.packs_editor_body.rowconfigure(1, weight=1)

        self.packs_form_frame = tk.Frame(self.packs_editor_body, bg=SURFACE)
        self.packs_form_frame.grid(row=0, column=0, sticky="ew")
        self.packs_form_frame.columnconfigure(0, weight=1)

        catalog_wrap = tk.Frame(self.packs_editor_body, bg=SURFACE)
        catalog_wrap.grid(row=1, column=0, sticky="nsew")
        catalog_wrap.columnconfigure(0, weight=1)
        catalog_wrap.rowconfigure(0, weight=1)

        self.packs_catalog_canvas = tk.Canvas(catalog_wrap, bg=SURFACE, highlightthickness=0, bd=0)
        self.packs_catalog_canvas.grid(row=0, column=0, sticky="nsew")
        catalog_scroll = ttk.Scrollbar(catalog_wrap, orient="vertical", command=self.packs_catalog_canvas.yview)
        catalog_scroll.grid(row=0, column=1, sticky="ns")
        self.packs_catalog_canvas.configure(yscrollcommand=catalog_scroll.set)

        self.packs_catalog_frame = tk.Frame(self.packs_catalog_canvas, bg=SURFACE)
        self.packs_catalog_window = self.packs_catalog_canvas.create_window((0, 0), window=self.packs_catalog_frame, anchor="nw")
        self.packs_catalog_frame.bind(
            "<Configure>",
            lambda _event: self.packs_catalog_canvas.configure(scrollregion=self.packs_catalog_canvas.bbox("all")),
        )
        self.packs_catalog_canvas.bind("<Configure>", self.on_packs_catalog_canvas_configure)
        self._bind_mousewheel(self.packs_catalog_canvas, self.packs_catalog_frame)

        self.show_packs_list_scene()
        self.render_pack_editor()

    def refresh_pack_tab_visuals(self) -> None:
        if self.pack_scene_var.get() == "list":
            self.refresh_packs_list(select_index=self.selected_pack_index)
        else:
            self.render_pack_editor()

    def render_pack_editor(self) -> None:
        self.update_pack_metrics()
        for child in self.packs_form_frame.winfo_children():
            child.destroy()
        for child in self.packs_catalog_frame.winfo_children():
            child.destroy()

        self.packs_form_frame.configure(padx=10, pady=8)
        self.packs_form_frame.columnconfigure(0, weight=1)
        self.packs_catalog_frame.columnconfigure(0, weight=1)

        pack_card = tk.Frame(
            self.packs_form_frame,
            bg=SURFACE_MUTED,
            highlightthickness=1,
            highlightbackground=BORDER,
            bd=0,
            padx=18,
            pady=18,
        )
        pack_card.grid(row=0, column=0, sticky="ew", padx=10, pady=(6, 12))
        pack_card.columnconfigure(0, weight=1)
        pack_card.columnconfigure(1, weight=1)

        tk.Label(
            pack_card,
            text="Pack Details",
            bg=SURFACE_MUTED,
            fg=TEXT,
            font=self.section_font,
        ).grid(row=0, column=0, columnspan=2, sticky="w")
        self._make_input(pack_card, "Pack Name", self.pack_name_var, 1, 0)
        self._make_input(pack_card, "Price (BRL)", self.pack_price_brl_var, 1, 1)
        tk.Label(
            pack_card,
            text="Packs can only use items from the global item base manager.",
            bg=SURFACE_MUTED,
            fg=TEXT_MUTED,
            font=self.body_font,
            justify="left",
        ).grid(row=2, column=0, columnspan=2, sticky="w", padx=10, pady=(6, 0))

        metrics = tk.Frame(pack_card, bg=SURFACE_MUTED)
        metrics.grid(row=3, column=0, columnspan=2, sticky="ew", padx=10, pady=(14, 0))
        for column in range(3):
            metrics.columnconfigure(column, weight=1)
        self._create_metric_tile(metrics, "Total Value", self.pack_total_value_var, 0)
        self._create_metric_tile(metrics, "Price in USD", self.pack_price_usd_var, 1)
        self._create_metric_tile(metrics, "Value / USD", self.pack_value_ratio_var, 2)

        actions = tk.Frame(pack_card, bg=SURFACE_MUTED)
        actions.grid(row=4, column=0, columnspan=2, sticky="e", padx=10, pady=(14, 0))
        if self.selected_pack_index is None:
            self._make_button(actions, "Create", self.create_pack, filled=True).pack(anchor="e")
        else:
            self._make_button(actions, "Update", self.update_pack, filled=True).pack(side="left")
            self._make_button(actions, "Delete", self.delete_pack, filled=True, bg=DANGER, active_bg="#B71C1C").pack(side="left", padx=(8, 0))

        items_card = tk.Frame(
            self.packs_form_frame,
            bg=SURFACE,
            highlightthickness=1,
            highlightbackground=BORDER,
            bd=0,
            padx=18,
            pady=18,
        )
        items_card.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 12))
        items_card.columnconfigure(0, weight=1)
        tk.Label(items_card, text="Pack Items", bg=SURFACE, fg=TEXT, font=self.section_font).grid(row=0, column=0, sticky="w")
        tk.Label(
            items_card,
            text="Use Add to Pack from the catalog below. Each line keeps the item fixed and only lets you change the amount.",
            bg=SURFACE,
            fg=TEXT_MUTED,
            font=self.body_font,
            justify="left",
            wraplength=900,
        ).grid(row=1, column=0, sticky="w", pady=(4, 12))

        if not self.pack_editor_items:
            empty = tk.Frame(items_card, bg=SURFACE_MUTED, padx=14, pady=18, highlightthickness=1, highlightbackground=BORDER, bd=0)
            empty.grid(row=2, column=0, sticky="ew")
            tk.Label(empty, text="No items in this pack yet", bg=SURFACE_MUTED, fg=TEXT, font=self.card_title_font).pack(anchor="w")
            tk.Label(empty, text="Open the global item base manager to create items, then add them from the catalog here.", bg=SURFACE_MUTED, fg=TEXT_MUTED, font=self.body_font, justify="left", wraplength=860).pack(anchor="w", pady=(4, 0))
        else:
            for index, item in enumerate(self.pack_editor_items):
                self._create_pack_item_row(items_card, index, item, 2 + index)

        catalog_card = tk.Frame(
            self.packs_catalog_frame,
            bg=SURFACE_MUTED,
            highlightthickness=1,
            highlightbackground=BORDER,
            bd=0,
            padx=18,
            pady=18,
        )
        catalog_card.grid(row=0, column=0, sticky="nsew", padx=10, pady=(0, 12))
        catalog_card.columnconfigure(0, weight=1)

        catalog_header = tk.Frame(catalog_card, bg=SURFACE_MUTED)
        catalog_header.grid(row=0, column=0, sticky="ew")
        catalog_header.columnconfigure(0, weight=1)
        tk.Label(catalog_header, text="Item Catalog", bg=SURFACE_MUTED, fg=TEXT, font=self.section_font).grid(row=0, column=0, sticky="w")
        tk.Label(catalog_header, textvariable=self.item_base_summary_var, bg=SURFACE_MUTED, fg=TEXT_MUTED, font=self.body_font).grid(row=1, column=0, sticky="w", pady=(4, 0))
        self._make_button(catalog_header, "Manage Item Base", self.open_item_base_manager, filled=False).grid(row=0, column=1, rowspan=2, sticky="e")

        if not self.item_bases:
            empty = tk.Frame(catalog_card, bg=SURFACE, padx=14, pady=18, highlightthickness=1, highlightbackground=BORDER, bd=0)
            empty.grid(row=1, column=0, sticky="ew", pady=(12, 0))
            tk.Label(empty, text="No global item base items yet", bg=SURFACE, fg=TEXT, font=self.card_title_font).pack(anchor="w")
            tk.Label(empty, text="Use Manage Item Base to create the shared catalog before building packs.", bg=SURFACE, fg=TEXT_MUTED, font=self.body_font, justify="left", wraplength=860).pack(anchor="w", pady=(4, 0))
        else:
            catalog_grid = tk.Frame(catalog_card, bg=SURFACE_MUTED)
            catalog_grid.grid(row=1, column=0, sticky="ew", pady=(12, 0))
            column_count, wraplength = self.get_pack_catalog_layout_metrics()
            self.pack_catalog_layout_key = self.get_pack_catalog_layout_key()
            for column in range(column_count):
                catalog_grid.columnconfigure(column, weight=1)
            for index, item_base in enumerate(self.item_bases):
                self._create_item_base_card(catalog_grid, index, item_base, wraplength, row=index // column_count, column=index % column_count)

    def _create_metric_tile(self, parent: tk.Misc, title: str, variable: tk.StringVar, column: int) -> None:
        tile = tk.Frame(parent, bg=SURFACE, highlightthickness=1, highlightbackground=BORDER, bd=0, padx=12, pady=10)
        tile.grid(row=0, column=column, sticky="ew", padx=(0, 8) if column < 2 else (0, 0))
        tk.Label(tile, text=title, bg=SURFACE, fg=TEXT_MUTED, font=self.label_font).pack(anchor="w")
        tk.Label(tile, textvariable=variable, bg=SURFACE, fg=PRIMARY_DARK, font=self.section_font).pack(anchor="w", pady=(6, 0))

    def _create_pack_item_row(self, parent: tk.Misc, index: int, item: dict[str, str], row: int) -> None:
        item_name = str(item.get("item_name", "") or "").strip()
        amount_value = str(item.get("amount", "") or "").strip() or "1"
        item_base = self.find_item_base(item_name)
        bg = SURFACE_MUTED if index % 2 == 0 else SURFACE

        line = tk.Frame(parent, bg=bg, highlightthickness=1, highlightbackground=BORDER, bd=0, padx=14, pady=12)
        line.grid(row=row, column=0, sticky="ew", pady=(0, 8))
        line.columnconfigure(0, weight=1)
        line.columnconfigure(1, weight=0)
        line.columnconfigure(2, weight=0)
        line.columnconfigure(3, weight=0)

        if item_base is None:
            meta_text = "Missing item base. Restore it in Manage Item Base before saving this pack."
            line_total = 0.0
            name_color = DANGER
        else:
            item_value = self.calculate_item_base_value(item_base)
            meta_text = f"Priority: {item_base.get('item_priority', '0')}   Base: {item_base.get('item_base_value', '0')}   Item Value: {format_decimal(item_value)}"
            line_total = item_value * parse_int(amount_value)
            name_color = TEXT

        tk.Label(line, text=item_name or "Unnamed Item", bg=bg, fg=name_color, font=self.card_title_font, anchor="w").grid(row=0, column=0, sticky="w")
        tk.Label(line, text=meta_text, bg=bg, fg=TEXT_MUTED, font=self.card_meta_font, justify="left", anchor="w").grid(row=1, column=0, sticky="w", pady=(4, 0))

        amount_var = tk.StringVar(value=amount_value)
        amount_wrap = tk.Frame(line, bg=bg)
        amount_wrap.grid(row=0, column=1, rowspan=2, sticky="e", padx=(12, 8))
        tk.Label(amount_wrap, text="Amount", bg=bg, fg=TEXT_MUTED, font=self.label_font).pack(anchor="e")
        amount_entry = tk.Entry(amount_wrap, textvariable=amount_var, width=8, justify="center", bg=SURFACE, fg=TEXT, relief="flat", bd=0, insertbackground=TEXT, highlightthickness=1, highlightbackground=BORDER, highlightcolor=PRIMARY, font=self.body_font)
        amount_entry.pack(anchor="e", pady=(6, 0), ipady=6)
        amount_entry.bind("<FocusOut>", lambda _event, idx=index, variable=amount_var: self.update_pack_item_amount(idx, variable.get()))
        amount_entry.bind("<Return>", lambda _event, idx=index, variable=amount_var: self.update_pack_item_amount(idx, variable.get()))

        tk.Label(line, text=f"Line Value: {format_decimal(line_total)}", bg=bg, fg=PRIMARY_DARK, font=self.label_font, anchor="e").grid(row=0, column=2, rowspan=2, sticky="e", padx=(0, 8))
        self._make_button(line, "Remove", lambda idx=index: self.remove_pack_item(idx), filled=False).grid(row=0, column=3, rowspan=2, sticky="e")

    def _create_item_base_card(self, parent: tk.Misc, index: int, item_base: dict[str, str], wraplength: int, row: int, column: int) -> None:
        card = tk.Frame(parent, bg=SURFACE, highlightthickness=1, highlightbackground=BORDER, bd=0, padx=14, pady=12)
        card.grid(row=row, column=column, sticky="ew", padx=6, pady=6)
        card.columnconfigure(0, weight=1)

        item_value = self.calculate_item_base_value(item_base)
        tk.Label(card, text=item_base.get("item_name", "") or "Unnamed Item", bg=SURFACE, fg=TEXT, font=self.card_title_font, anchor="w", wraplength=wraplength, justify="left").grid(row=0, column=0, sticky="ew")
        tk.Label(card, text=f"Priority: {item_base.get('item_priority', '0')}   Base: {item_base.get('item_base_value', '0')}", bg=SURFACE, fg=TEXT_MUTED, font=self.card_meta_font, anchor="w", wraplength=wraplength, justify="left").grid(row=1, column=0, sticky="ew", pady=(6, 0))
        tk.Label(card, text=f"Item Value: {format_decimal(item_value)}", bg=SURFACE, fg=PRIMARY_DARK, font=self.label_font, anchor="w").grid(row=2, column=0, sticky="w", pady=(8, 0))
        self._make_button(card, "Add to Pack", lambda name=item_base.get("item_name", ""): self.add_item_to_pack(str(name)), filled=True).grid(row=3, column=0, sticky="w", pady=(10, 0))

    def get_pack_catalog_layout_metrics(self) -> tuple[int, int]:
        width = self.packs_catalog_canvas.winfo_width()
        if width <= 1:
            width = 720
        usable_width = max(260, width - 56)
        column_count = max(1, min(3, usable_width // 280))
        card_width = max(220, usable_width // column_count)
        wraplength = max(140, card_width - 28)
        return column_count, wraplength

    def get_pack_catalog_layout_key(self) -> tuple[int, int]:
        width = self.packs_catalog_canvas.winfo_width()
        if width <= 1:
            width = 720
        usable_width = max(260, width - 56)
        column_count = max(1, min(3, usable_width // 280))
        card_width = max(220, usable_width // column_count)
        return column_count, card_width // 24

    def on_packs_catalog_canvas_configure(self, event: tk.Event) -> None:
        self.packs_catalog_canvas.itemconfigure(self.packs_catalog_window, width=event.width)
        new_layout_key = self.get_pack_catalog_layout_key()
        if new_layout_key != self.pack_catalog_layout_key and self.pack_scene_var.get() == "editor":
            self.render_pack_editor()

    def show_packs_list_scene(self) -> None:
        self.pack_scene_var.set("list")
        self.packs_editor_scene.grid_remove()
        self.packs_list_scene.grid()

    def show_pack_editor_scene(self) -> None:
        self.pack_scene_var.set("editor")
        self.packs_list_scene.grid_remove()
        self.packs_editor_scene.grid()

    def open_new_pack_scene(self) -> None:
        self.clear_pack_form(keep_status=True, reopen=False)
        self.show_pack_editor_scene()
        self.status_var.set("Creating a new pack.")
    def load_pack_data(self, select_index: int | None) -> None:
        try:
            self.item_bases, self.packs = self.pack_repository.load()
        except Exception as exc:
            messagebox.showerror("Load failed", f"Unable to load packs:\n{exc}")
            self.item_bases = []
            self.packs = []
            self.status_var.set("Failed to load pack data.")
            return

        self.sort_item_bases()
        self.update_pack_summary()
        self.refresh_packs_list(select_index=select_index)
        self.update_item_base_preview_value()
        self.render_pack_editor()
        if select_index is None or not self.packs:
            self.clear_pack_form(keep_status=True, reopen=False)
        else:
            self.select_pack(min(select_index, len(self.packs) - 1))
        self.clear_item_base_form(keep_status=True, rerender_popup=False, rerender_pack=False)
        self.render_item_base_manager()

    def update_pack_summary(self) -> None:
        self.pack_summary_var.set(f"{len(self.packs)} pack(s) with {len(self.item_bases)} catalog item(s)")
        self.item_base_summary_var.set(f"{len(self.item_bases)} catalog item(s)")

    def refresh_packs_list(self, select_index: int | None) -> None:
        for child in self.packs_list_container.winfo_children():
            child.destroy()

        if not self.packs:
            empty = tk.Frame(self.packs_list_container, bg=SURFACE, pady=48)
            empty.pack(fill="x")
            tk.Label(empty, text="No packs yet", bg=SURFACE, fg=TEXT, font=self.section_font).pack()
            tk.Label(empty, text="Create a pack to calculate total value versus the converted USD price.", bg=SURFACE, fg=TEXT_MUTED, font=self.body_font).pack(pady=(6, 0))
            self.selected_pack_index = None
            return

        if select_index is not None and 0 <= select_index < len(self.packs):
            self.selected_pack_index = select_index
        elif self.selected_pack_index is None or not (0 <= self.selected_pack_index < len(self.packs)):
            self.selected_pack_index = None

        for index, pack in enumerate(self.packs):
            self._add_pack_card(index, pack, selected=index == self.selected_pack_index)

    def _add_pack_card(self, index: int, pack: dict[str, object], selected: bool) -> None:
        bg = PRIMARY_SOFT if selected else SURFACE
        card = tk.Frame(self.packs_list_container, bg=bg, highlightthickness=1, highlightbackground=BORDER, bd=0, padx=14, pady=12, cursor="hand2")
        card.pack(fill="x", padx=4, pady=6)
        card.columnconfigure(0, weight=1)

        pack_name = str(pack.get("pack_name", "") or "Unnamed Pack")
        items = self.clone_pack_items(pack.get("items", []))
        total_units = sum(parse_int(item.get("amount", "")) for item in items)
        total_value = self.calculate_pack_total_value(items)
        price_brl = str(pack.get("price_brl", "") or "").strip()
        price_usd = self.calculate_pack_price_usd(price_brl)
        ratio = total_value / price_usd if price_usd > 0 else 0.0

        title = tk.Label(card, text=pack_name, bg=bg, fg=TEXT, font=self.card_title_font, anchor="w")
        title.grid(row=0, column=0, sticky="w")
        subtitle = tk.Label(card, text=f"{len(items)} line item(s) and {total_units} total unit(s)", bg=bg, fg=PRIMARY_DARK, font=self.label_font, anchor="w")
        subtitle.grid(row=1, column=0, sticky="w", pady=(4, 0))
        summary = tk.Label(card, text=f"Total Value: {format_decimal(total_value)}   Price: BRL {price_brl or '0'} / US$ {format_decimal(price_usd)}   Value / USD: {format_decimal(ratio, 4)}", bg=bg, fg=TEXT_MUTED, font=self.card_meta_font, anchor="w", justify="left", wraplength=640)
        summary.grid(row=2, column=0, sticky="ew", pady=(6, 0))
        preview_names = [str(item.get("item_name", "") or "").strip() for item in items[:4]]
        preview = tk.Label(card, text=", ".join(name for name in preview_names if name) or "No items", bg=bg, fg=TEXT_MUTED, font=self.card_meta_font, anchor="w", justify="left", wraplength=640)
        preview.grid(row=3, column=0, sticky="ew", pady=(8, 0))

        actions = tk.Frame(card, bg=bg)
        actions.grid(row=4, column=0, sticky="ew", pady=(10, 0))
        open_button = self._make_button(actions, "Open", lambda idx=index: self.select_pack(idx), filled=False)
        open_button.pack(side="left")
        delete_button = self._make_button(actions, "Delete", lambda idx=index: self.delete_pack(idx), filled=True, bg=DANGER, active_bg="#B71C1C")
        delete_button.pack(side="left", padx=(8, 0))

        self._bind_mousewheel(self.packs_list_canvas, card, title, subtitle, summary, preview, actions, open_button, delete_button)
        for widget in (card, title, subtitle, summary, preview):
            widget.bind("<Button-1>", lambda _event, idx=index: self.select_pack(idx))

    def select_pack(self, index: int) -> None:
        if not (0 <= index < len(self.packs)):
            return

        self.selected_pack_index = index
        pack = self.packs[index]
        self.pack_name_var.set(str(pack.get("pack_name", "") or ""))
        self.pack_price_brl_var.set(str(pack.get("price_brl", "") or ""))
        self.pack_editor_items = self.clone_pack_items(pack.get("items", []))
        self.pack_title_var.set(str(pack.get("pack_name", "") or "Unnamed Pack"))
        self.update_pack_metrics()
        self.refresh_packs_list(select_index=index)
        self.render_pack_editor()
        self.show_pack_editor_scene()
        self.status_var.set(f"Selected pack #{index + 1}: {pack.get('pack_name', '(no name)')}")

    def clear_pack_form(self, keep_status: bool = False, reopen: bool = True) -> None:
        self.selected_pack_index = None
        self.pack_name_var.set("")
        self.pack_price_brl_var.set("")
        self.pack_editor_items = []
        self.pack_title_var.set("New Pack")
        self.update_pack_metrics()
        self.refresh_packs_list(select_index=None)
        self.render_pack_editor()
        if reopen:
            self.show_pack_editor_scene()
        if not keep_status:
            self.status_var.set("Pack editor cleared. Ready for a new pack.")

    def collect_pack_data(self) -> dict[str, object]:
        return {
            "pack_name": self.pack_name_var.get().strip(),
            "price_brl": self.pack_price_brl_var.get().strip(),
            "items": self.clone_pack_items(self.pack_editor_items),
        }

    def clone_pack_items(self, items: object) -> list[dict[str, str]]:
        if not isinstance(items, list):
            return []
        cloned: list[dict[str, str]] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            cloned.append({"item_name": str(item.get("item_name", "") or "").strip(), "amount": str(item.get("amount", "") or "").strip()})
        return cloned

    def clone_packs_state(self) -> list[dict[str, object]]:
        return [{"pack_name": str(entry.get("pack_name", "") or "").strip(), "price_brl": str(entry.get("price_brl", "") or "").strip(), "items": self.clone_pack_items(entry.get("items", []))} for entry in self.packs]

    def clone_item_bases_state(self) -> list[dict[str, str]]:
        return [{"item_name": str(entry.get("item_name", "") or "").strip(), "item_priority": str(entry.get("item_priority", "") or "").strip(), "item_base_value": str(entry.get("item_base_value", "") or "").strip(), "item_value": str(entry.get("item_value", "") or "").strip()} for entry in self.item_bases]

    def prepare_pack_for_save(self, exclude_index: int | None) -> dict[str, object]:
        pack = self.collect_pack_data()
        pack_name = str(pack.get("pack_name", "") or "").strip()
        price_brl = str(pack.get("price_brl", "") or "").strip()
        items = self.clone_pack_items(pack.get("items", []))
        if not pack_name:
            raise ValueError("Pack name is required.")

        price_brl_value = parse_float(price_brl)
        if price_brl_value <= 0:
            raise ValueError("Price in BRL must be greater than zero.")
        if not items:
            raise ValueError("Add at least one item to the pack.")

        seen_names: set[str] = set()
        normalized_items: list[dict[str, str]] = []
        for item in items:
            item_name = str(item.get("item_name", "") or "").strip()
            amount_raw = str(item.get("amount", "") or "").strip()
            if not item_name:
                raise ValueError("Each pack item must have a catalog item selected.")
            item_key = normalize_item_name(item_name)
            if item_key in seen_names:
                raise ValueError("A catalog item can only appear once per pack.")
            seen_names.add(item_key)
            item_base = self.find_item_base(item_name)
            if item_base is None:
                raise ValueError(f"Catalog item '{item_name}' does not exist in the global item base.")
            try:
                amount = int(amount_raw)
            except ValueError as exc:
                raise ValueError(f"Amount for '{item_name}' must be a whole number.") from exc
            if amount <= 0:
                raise ValueError(f"Amount for '{item_name}' must be greater than zero.")
            normalized_items.append({"item_name": item_base.get("item_name", item_name), "amount": str(amount)})

        target_key = normalize_item_name(pack_name)
        for index, entry in enumerate(self.packs):
            if exclude_index is not None and index == exclude_index:
                continue
            existing_name = str(entry.get("pack_name", "") or "").strip()
            if normalize_item_name(existing_name) == target_key:
                raise ValueError("A pack with that name already exists.")

        return {"pack_name": pack_name, "price_brl": format_decimal(price_brl_value), "items": normalized_items}

    def create_pack(self) -> None:
        previous_packs = self.clone_packs_state()
        try:
            pack = self.prepare_pack_for_save(None)
            self.packs.append(pack)
            self.save_pack_data()
        except Exception as exc:
            self.packs = previous_packs
            messagebox.showerror("Create failed", str(exc))
            self.status_var.set("Unable to create pack.")
            return

        new_index = self.packs.index(pack)
        self.update_pack_summary()
        self.select_pack(new_index)
        self.status_var.set(f"Created pack: {pack.get('pack_name', '(no name)')}")

    def update_pack(self) -> None:
        if self.selected_pack_index is None:
            messagebox.showwarning("No selection", "Select a pack from the list first.")
            return

        previous_packs = self.clone_packs_state()
        index = self.selected_pack_index
        try:
            pack = self.prepare_pack_for_save(index)
            self.packs[index] = pack
            self.save_pack_data()
        except Exception as exc:
            self.packs = previous_packs
            messagebox.showerror("Update failed", str(exc))
            self.status_var.set("Unable to update pack.")
            return

        self.update_pack_summary()
        self.select_pack(index)
        self.status_var.set(f"Updated pack: {pack.get('pack_name', '(no name)')}")

    def delete_pack(self, index: int | None = None) -> None:
        target_index = self.selected_pack_index if index is None else index
        if target_index is None or not (0 <= target_index < len(self.packs)):
            messagebox.showwarning("No selection", "Select a pack from the list first.")
            return

        pack = self.packs[target_index]
        pack_name = str(pack.get("pack_name", "") or "(no name)")
        confirmed = messagebox.askyesno("Delete pack", f"Delete pack '{pack_name}'?")
        if not confirmed:
            return

        previous_packs = self.clone_packs_state()
        self.packs.pop(target_index)
        try:
            self.save_pack_data()
        except Exception as exc:
            self.packs = previous_packs
            messagebox.showerror("Delete failed", str(exc))
            self.status_var.set("Unable to delete pack.")
            return

        self.update_pack_summary()
        if self.packs:
            self.select_pack(min(target_index, len(self.packs) - 1))
        else:
            self.clear_pack_form(keep_status=True, reopen=False)
            self.show_packs_list_scene()
        self.status_var.set(f"Deleted pack: {pack_name}")

    def save_pack_data(self) -> None:
        self.pack_repository.save(self.item_bases, self.packs)
        self.update_pack_summary()
        self.refresh_packs_list(select_index=self.selected_pack_index)
        if self.pack_scene_var.get() == "editor":
            self.render_pack_editor()
        self.render_item_base_manager()
    def add_item_to_pack(self, item_name: str) -> None:
        item_base = self.find_item_base(item_name)
        if item_base is None:
            messagebox.showwarning("Missing item base", f"Catalog item '{item_name}' no longer exists.")
            return

        target_key = normalize_item_name(item_base.get("item_name", item_name))
        for item in self.pack_editor_items:
            if normalize_item_name(item.get("item_name", "")) == target_key:
                item["amount"] = str(max(1, parse_int(item.get("amount", ""))) + 1)
                self.update_pack_metrics()
                self.render_pack_editor()
                self.status_var.set(f"Increased amount for {item_base.get('item_name', item_name)}.")
                return

        self.pack_editor_items.append({"item_name": item_base.get("item_name", item_name), "amount": "1"})
        self.update_pack_metrics()
        self.render_pack_editor()
        self.status_var.set(f"Added {item_base.get('item_name', item_name)} to the current pack.")

    def remove_pack_item(self, index: int) -> None:
        if not (0 <= index < len(self.pack_editor_items)):
            return
        item_name = self.pack_editor_items[index].get("item_name", "") or "item"
        self.pack_editor_items.pop(index)
        self.update_pack_metrics()
        self.render_pack_editor()
        self.status_var.set(f"Removed {item_name} from the current pack.")

    def update_pack_item_amount(self, index: int, raw_value: str) -> None:
        if not (0 <= index < len(self.pack_editor_items)):
            return
        try:
            amount = int(str(raw_value or "").strip())
        except ValueError:
            messagebox.showwarning("Invalid amount", "Amount must be a whole number.")
            self.render_pack_editor()
            return
        if amount <= 0:
            messagebox.showwarning("Invalid amount", "Amount must be greater than zero.")
            self.render_pack_editor()
            return

        self.pack_editor_items[index]["amount"] = str(amount)
        self.update_pack_metrics()
        self.render_pack_editor()

    def open_item_base_manager(self) -> None:
        existing_popup = getattr(self, "item_base_manager_popup", None)
        if existing_popup is not None and existing_popup.winfo_exists():
            existing_popup.deiconify()
            existing_popup.lift()
            existing_popup.focus_force()
            self.render_item_base_manager()
            return

        popup = tk.Toplevel(self)
        popup.title("Item Base Manager")
        popup.configure(bg=BACKGROUND)
        popup.geometry("1100x720")
        popup.minsize(900, 620)
        popup.transient(self)
        popup.protocol("WM_DELETE_WINDOW", self.close_item_base_manager)
        self.item_base_manager_popup = popup

        shell = self._make_panel(popup)
        shell.pack(fill="both", expand=True, padx=20, pady=20)
        shell.columnconfigure(0, weight=1)
        shell.rowconfigure(1, weight=1)
        self.item_base_manager_shell = shell

        header = tk.Frame(shell, bg=SURFACE)
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 8))
        header.columnconfigure(0, weight=1)
        tk.Label(header, text="Global Item Base", bg=SURFACE, fg=TEXT, font=self.section_font).grid(row=0, column=0, sticky="w")
        tk.Label(header, text="Changes here affect every pack, and packs can only use items from this catalog.", bg=SURFACE, fg=TEXT_MUTED, font=self.body_font).grid(row=1, column=0, sticky="w", pady=(4, 0))
        self._make_button(header, "Close", self.close_item_base_manager, filled=False).grid(row=0, column=1, rowspan=2, sticky="e")

        body = tk.Frame(shell, bg=SURFACE)
        body.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        list_wrap = tk.Frame(body, bg=SURFACE)
        list_wrap.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        list_wrap.columnconfigure(0, weight=1)
        list_wrap.rowconfigure(0, weight=1)
        self.item_base_manager_canvas = tk.Canvas(list_wrap, bg=SURFACE, highlightthickness=0, bd=0)
        self.item_base_manager_canvas.grid(row=0, column=0, sticky="nsew")
        list_scroll = ttk.Scrollbar(list_wrap, orient="vertical", command=self.item_base_manager_canvas.yview)
        list_scroll.grid(row=0, column=1, sticky="ns")
        self.item_base_manager_canvas.configure(yscrollcommand=list_scroll.set)

        self.item_base_manager_container = tk.Frame(self.item_base_manager_canvas, bg=SURFACE)
        self.item_base_manager_window = self.item_base_manager_canvas.create_window((0, 0), window=self.item_base_manager_container, anchor="nw")
        self.item_base_manager_container.bind("<Configure>", lambda _event: self.item_base_manager_canvas.configure(scrollregion=self.item_base_manager_canvas.bbox("all")))
        self.item_base_manager_canvas.bind("<Configure>", lambda event: self.item_base_manager_canvas.itemconfigure(self.item_base_manager_window, width=event.width))
        self._bind_mousewheel(self.item_base_manager_canvas, self.item_base_manager_container)

        self.item_base_manager_form = tk.Frame(body, bg=SURFACE)
        self.item_base_manager_form.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        self.item_base_manager_form.columnconfigure(0, weight=1)

        self.render_item_base_manager()

    def close_item_base_manager(self) -> None:
        popup = getattr(self, "item_base_manager_popup", None)
        if popup is not None and popup.winfo_exists():
            popup.destroy()
        self.item_base_manager_popup = None
        self.item_base_manager_shell = None
        self.item_base_manager_canvas = None
        self.item_base_manager_container = None
        self.item_base_manager_window = None
        self.item_base_manager_form = None

    def render_item_base_manager(self) -> None:
        popup = getattr(self, "item_base_manager_popup", None)
        if popup is None or not popup.winfo_exists():
            return

        list_container = getattr(self, "item_base_manager_container", None)
        form_frame = getattr(self, "item_base_manager_form", None)
        if list_container is None or form_frame is None:
            return

        for child in list_container.winfo_children():
            child.destroy()
        for child in form_frame.winfo_children():
            child.destroy()

        summary_card = tk.Frame(form_frame, bg=SURFACE_MUTED, highlightthickness=1, highlightbackground=BORDER, bd=0, padx=18, pady=18)
        summary_card.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        summary_card.columnconfigure(0, weight=1)
        tk.Label(summary_card, textvariable=self.item_base_title_var, bg=SURFACE_MUTED, fg=TEXT, font=self.section_font).grid(row=0, column=0, sticky="w")
        tk.Label(summary_card, textvariable=self.item_base_summary_var, bg=SURFACE_MUTED, fg=TEXT_MUTED, font=self.body_font).grid(row=1, column=0, sticky="w", pady=(4, 0))
        self._make_input(summary_card, "Item Name", self.item_base_name_var, 2, 0)
        fields_row = tk.Frame(summary_card, bg=SURFACE_MUTED)
        fields_row.grid(row=3, column=0, sticky="ew")
        fields_row.columnconfigure(0, weight=1)
        fields_row.columnconfigure(1, weight=1)
        self._make_input(fields_row, "Priority", self.item_base_priority_var, 0, 0)
        self._make_input(fields_row, "Base Value", self.item_base_value_var, 0, 1)

        preview = tk.Frame(summary_card, bg=SURFACE_MUTED)
        preview.grid(row=4, column=0, sticky="ew", padx=10, pady=(12, 0))
        preview.columnconfigure(1, weight=1)
        tk.Label(preview, text="Item Value", bg=SURFACE_MUTED, fg=TEXT_MUTED, font=self.label_font).grid(row=0, column=0, sticky="w")
        tk.Label(preview, textvariable=self.item_base_total_var, bg=SURFACE_MUTED, fg=PRIMARY_DARK, font=self.section_font).grid(row=0, column=1, sticky="e")

        actions = tk.Frame(summary_card, bg=SURFACE_MUTED)
        actions.grid(row=5, column=0, sticky="e", padx=10, pady=(14, 0))
        self._make_button(actions, "New", self.clear_item_base_form, filled=False).pack(side="left")
        if self.selected_item_base_index is None:
            self._make_button(actions, "Create", self.create_item_base, filled=True).pack(side="left", padx=(8, 0))
        else:
            self._make_button(actions, "Update", self.update_item_base, filled=True).pack(side="left", padx=(8, 0))
            self._make_button(actions, "Delete", self.delete_item_base, filled=True, bg=DANGER, active_bg="#B71C1C").pack(side="left", padx=(8, 0))

        list_header = tk.Frame(list_container, bg=SURFACE)
        list_header.pack(fill="x", padx=4, pady=(0, 8))
        tk.Label(list_header, text="Catalog Items", bg=SURFACE, fg=TEXT, font=self.section_font).pack(anchor="w")
        tk.Label(list_header, text="Select an item to edit it. Packs use these values globally.", bg=SURFACE, fg=TEXT_MUTED, font=self.body_font, justify="left", wraplength=360).pack(anchor="w", pady=(4, 0))

        if not self.item_bases:
            empty = tk.Frame(list_container, bg=SURFACE, pady=48)
            empty.pack(fill="x")
            tk.Label(empty, text="No item base items yet", bg=SURFACE, fg=TEXT, font=self.section_font).pack()
            tk.Label(empty, text="Create the first shared catalog item on the right.", bg=SURFACE, fg=TEXT_MUTED, font=self.body_font).pack(pady=(6, 0))
            return

        for index, item_base in enumerate(self.item_bases):
            self._create_item_base_manager_card(index, item_base)

    def _create_item_base_manager_card(self, index: int, item_base: dict[str, str]) -> None:
        selected = index == self.selected_item_base_index
        bg = PRIMARY_SOFT if selected else SURFACE
        item_value = self.calculate_item_base_value(item_base)
        card = tk.Frame(self.item_base_manager_container, bg=bg, highlightthickness=1, highlightbackground=PRIMARY if selected else BORDER, bd=0, padx=14, pady=12, cursor="hand2")
        card.pack(fill="x", padx=4, pady=6)
        card.columnconfigure(0, weight=1)

        name_label = tk.Label(card, text=item_base.get("item_name", "") or "Unnamed Item", bg=bg, fg=TEXT, font=self.card_title_font, anchor="w")
        name_label.grid(row=0, column=0, sticky="w")
        meta_label = tk.Label(card, text=f"Priority: {item_base.get('item_priority', '0')}   Base: {item_base.get('item_base_value', '0')}", bg=bg, fg=TEXT_MUTED, font=self.card_meta_font, anchor="w", justify="left", wraplength=360)
        meta_label.grid(row=1, column=0, sticky="w", pady=(4, 0))
        value_label = tk.Label(card, text=f"Item Value: {format_decimal(item_value)}", bg=bg, fg=PRIMARY_DARK, font=self.label_font, anchor="w")
        value_label.grid(row=2, column=0, sticky="w", pady=(8, 0))

        for widget in (card, name_label, meta_label, value_label):
            widget.bind("<Button-1>", lambda _event, idx=index: self.select_item_base(idx))
        self._bind_mousewheel(self.item_base_manager_canvas, card, name_label, meta_label, value_label)
    def select_item_base(self, index: int) -> None:
        if not (0 <= index < len(self.item_bases)):
            return

        self.selected_item_base_index = index
        item_base = self.item_bases[index]
        self.item_base_name_var.set(str(item_base.get("item_name", "") or ""))
        self.item_base_priority_var.set(str(item_base.get("item_priority", "") or ""))
        self.item_base_value_var.set(str(item_base.get("item_base_value", "") or ""))
        self.item_base_title_var.set(str(item_base.get("item_name", "") or "Edit Item Base"))
        self.update_item_base_preview_value()
        self.render_item_base_manager()
        if self.pack_scene_var.get() == "editor":
            self.render_pack_editor()
        self.status_var.set(f"Editing item base: {item_base.get('item_name', '(no name)')}")

    def clear_item_base_form(
        self,
        keep_status: bool = False,
        rerender_popup: bool = True,
        rerender_pack: bool = True,
    ) -> None:
        self.selected_item_base_index = None
        self.item_base_name_var.set("")
        self.item_base_priority_var.set("")
        self.item_base_value_var.set("")
        self.item_base_title_var.set("New Item Base")
        self.update_item_base_preview_value()
        if rerender_popup:
            self.render_item_base_manager()
        if rerender_pack and self.pack_scene_var.get() == "editor":
            self.render_pack_editor()
        if not keep_status:
            self.status_var.set("Item base manager cleared.")

    def update_item_base_preview_value(self) -> None:
        priority = parse_float(self.item_base_priority_var.get())
        base_value = parse_float(self.item_base_value_var.get())
        self.item_base_total_var.set(format_decimal(priority * base_value))

    def prepare_item_base_for_save(self, exclude_index: int | None) -> dict[str, str]:
        item_name = self.item_base_name_var.get().strip()
        if not item_name:
            raise ValueError("Item name is required.")

        priority = parse_float(self.item_base_priority_var.get())
        base_value = parse_float(self.item_base_value_var.get())
        if priority <= 0:
            raise ValueError("Item priority must be greater than zero.")
        if base_value <= 0:
            raise ValueError("Item base value must be greater than zero.")

        target_key = normalize_item_name(item_name)
        for index, entry in enumerate(self.item_bases):
            if exclude_index is not None and index == exclude_index:
                continue
            existing_name = str(entry.get("item_name", "") or "").strip()
            if normalize_item_name(existing_name) == target_key:
                raise ValueError("A catalog item with that name already exists.")

        return {
            "item_name": item_name,
            "item_priority": format_decimal(priority),
            "item_base_value": format_decimal(base_value),
            "item_value": format_decimal(priority * base_value),
        }

    def create_item_base(self) -> None:
        previous_item_bases = self.clone_item_bases_state()
        try:
            item_base = self.prepare_item_base_for_save(None)
            self.item_bases.append(item_base)
            self.sort_item_bases()
            self.save_pack_data()
        except Exception as exc:
            self.item_bases = previous_item_bases
            messagebox.showerror("Create failed", str(exc))
            self.status_var.set("Unable to create item base.")
            return

        new_index = next((index for index, entry in enumerate(self.item_bases) if normalize_item_name(entry.get("item_name", "")) == normalize_item_name(item_base.get("item_name", ""))), None)
        if new_index is not None:
            self.select_item_base(new_index)
        self.status_var.set(f"Created item base: {item_base.get('item_name', '(no name)')}")

    def update_item_base(self) -> None:
        if self.selected_item_base_index is None:
            messagebox.showwarning("No selection", "Select a catalog item first.")
            return

        previous_item_bases = self.clone_item_bases_state()
        previous_packs = self.clone_packs_state()
        previous_editor_items = self.clone_pack_items(self.pack_editor_items)
        index = self.selected_item_base_index
        previous_name = str(self.item_bases[index].get("item_name", "") or "")
        item_base = self.prepare_item_base_for_save(index)
        try:
            self.item_bases[index] = item_base
            self.rename_item_base_references(previous_name, item_base.get("item_name", ""))
            self.sort_item_bases()
            self.save_pack_data()
        except Exception as exc:
            self.item_bases = previous_item_bases
            self.packs = previous_packs
            self.pack_editor_items = previous_editor_items
            messagebox.showerror("Update failed", str(exc))
            self.status_var.set("Unable to update item base.")
            return

        updated_index = next((item_index for item_index, entry in enumerate(self.item_bases) if normalize_item_name(entry.get("item_name", "")) == normalize_item_name(item_base.get("item_name", ""))), None)
        if updated_index is not None:
            self.select_item_base(updated_index)
        else:
            self.render_item_base_manager()
        self.status_var.set(f"Updated item base: {item_base.get('item_name', '(no name)')}")

    def delete_item_base(self) -> None:
        if self.selected_item_base_index is None:
            messagebox.showwarning("No selection", "Select a catalog item first.")
            return

        item_base = self.item_bases[self.selected_item_base_index]
        item_name = str(item_base.get("item_name", "") or "(no name)")
        usage = self.get_item_base_usage(item_name)
        if usage:
            messagebox.showwarning("Item used in packs", f"Remove '{item_name}' from these packs before deleting it:\n" + "\n".join(usage))
            return

        confirmed = messagebox.askyesno("Delete item base", f"Delete item base '{item_name}'?")
        if not confirmed:
            return

        previous_item_bases = self.clone_item_bases_state()
        self.item_bases.pop(self.selected_item_base_index)
        try:
            self.save_pack_data()
        except Exception as exc:
            self.item_bases = previous_item_bases
            messagebox.showerror("Delete failed", str(exc))
            self.status_var.set("Unable to delete item base.")
            return

        self.clear_item_base_form(keep_status=True, rerender_popup=False, rerender_pack=False)
        self.render_item_base_manager()
        if self.pack_scene_var.get() == "editor":
            self.render_pack_editor()
        self.status_var.set(f"Deleted item base: {item_name}")

    def sort_item_bases(self) -> None:
        self.item_bases.sort(key=lambda item: normalize_item_name(item.get("item_name", "")))

    def find_item_base(self, item_name: str) -> dict[str, str] | None:
        target_key = normalize_item_name(item_name)
        if not target_key:
            return None
        for item_base in self.item_bases:
            if normalize_item_name(item_base.get("item_name", "")) == target_key:
                return item_base
        return None

    def rename_item_base_references(self, previous_name: str, new_name: str) -> None:
        previous_key = normalize_item_name(previous_name)
        if not previous_key:
            return
        if not new_name:
            new_name = previous_name

        for pack in self.packs:
            items = pack.get("items", [])
            if not isinstance(items, list):
                continue
            for item in items:
                if isinstance(item, dict) and normalize_item_name(item.get("item_name", "")) == previous_key:
                    item["item_name"] = new_name

        for item in self.pack_editor_items:
            if normalize_item_name(item.get("item_name", "")) == previous_key:
                item["item_name"] = new_name

        self.update_pack_metrics()

    def get_item_base_usage(self, item_name: str) -> list[str]:
        target_key = normalize_item_name(item_name)
        usages: list[str] = []
        for pack in self.packs:
            pack_name = str(pack.get("pack_name", "") or "Unnamed Pack")
            items = pack.get("items", [])
            if isinstance(items, list) and any(normalize_item_name(str(item.get("item_name", "") or "")) == target_key for item in items if isinstance(item, dict)):
                usages.append(pack_name)

        if any(normalize_item_name(item.get("item_name", "")) == target_key for item in self.pack_editor_items):
            current_name = self.pack_name_var.get().strip() or "Current Draft"
            if all(normalize_item_name(current_name) != normalize_item_name(name) for name in usages):
                usages.append(current_name)
        return usages

    def calculate_item_base_value(self, item_base: dict[str, str]) -> float:
        return parse_float(item_base.get("item_priority", "")) * parse_float(item_base.get("item_base_value", ""))

    def calculate_pack_total_value(self, items: list[dict[str, str]]) -> float:
        total = 0.0
        for item in items:
            item_base = self.find_item_base(item.get("item_name", ""))
            if item_base is None:
                continue
            total += self.calculate_item_base_value(item_base) * parse_int(item.get("amount", ""))
        return total

    def calculate_pack_price_usd(self, price_brl: str) -> float:
        price_brl_value = parse_float(price_brl)
        return price_brl_value / BRL_TO_USD_RATE if BRL_TO_USD_RATE > 0 else 0.0

    def update_pack_metrics(self) -> None:
        total_value = self.calculate_pack_total_value(self.pack_editor_items)
        price_usd = self.calculate_pack_price_usd(self.pack_price_brl_var.get())
        ratio = total_value / price_usd if price_usd > 0 else 0.0
        self.pack_total_value_var.set(format_decimal(total_value))
        self.pack_price_usd_var.set(f"US$ {format_decimal(price_usd)}")
        self.pack_value_ratio_var.set(format_decimal(ratio, 4))



