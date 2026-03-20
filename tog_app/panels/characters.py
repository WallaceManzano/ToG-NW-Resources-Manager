from __future__ import annotations

import hashlib
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk
from typing import TYPE_CHECKING
from urllib.parse import unquote, urlparse
from urllib.request import Request, urlopen

try:
    from PIL import Image, ImageTk  # type: ignore
except ImportError:
    Image = None
    ImageTk = None

from ..constants import *
from ..helpers import *

if TYPE_CHECKING:
    from ..app_window import TogCharacterManager


class CharactersPanelMixin:
    def _build_characters_tab(self) -> None:
        self.characters_tab.columnconfigure(0, weight=3)
        self.characters_tab.columnconfigure(1, weight=4)
        self.characters_tab.rowconfigure(0, weight=1)

        self.summary_panel = self._make_panel(self.characters_tab)
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
        sort_picker = ttk.Combobox(
            summary_header,
            textvariable=self.sort_mode_var,
            values=SORT_OPTIONS,
            state="readonly",
            width=16,
        )
        sort_picker.grid(row=0, column=1, rowspan=2, sticky="e")
        sort_picker.bind("<<ComboboxSelected>>", self.on_sort_changed)

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
            lambda _event: self.summary_canvas.configure(scrollregion=self.summary_canvas.bbox("all")),
        )
        self.summary_canvas.bind(
            "<Configure>",
            lambda event: self.summary_canvas.itemconfigure(self.summary_window, width=event.width),
        )
        self._bind_mousewheel(self.summary_canvas, self.summary_container)

        self.editor_panel = self._make_panel(self.characters_tab)
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
        action_bar.columnconfigure(0, weight=1)
        self.character_action_bar = action_bar
        self.render_character_action_bar()

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
        self.form_window = self.editor_canvas.create_window((0, 0), window=self.form_frame, anchor="nw")
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

    def render_character_action_bar(self) -> None:
        for child in self.character_action_bar.winfo_children():
            child.destroy()

        if self.selected_index is None:
            self.character_action_bar.columnconfigure(0, weight=0)
            self.character_action_bar.columnconfigure(1, weight=1)
            self._make_button(
                self.character_action_bar,
                "New",
                self.clear_form,
                filled=False,
            ).grid(row=0, column=0, padx=(0, 10), sticky="w")
            self._make_button(
                self.character_action_bar,
                "Create",
                self.create_row,
                filled=True,
            ).grid(row=0, column=1, sticky="e")
        else:
            self.character_action_bar.columnconfigure(0, weight=0)
            self.character_action_bar.columnconfigure(1, weight=1)
            self.character_action_bar.columnconfigure(2, weight=0)
            self._make_button(
                self.character_action_bar,
                "New",
                self.clear_form,
                filled=False,
            ).grid(row=0, column=0, padx=(0, 10), sticky="w")
            self._make_button(
                self.character_action_bar,
                "Update",
                self.update_row,
                filled=True,
            ).grid(row=0, column=1, sticky="e")
            self._make_button(
                self.character_action_bar,
                "Delete",
                self.delete_row,
                filled=True,
                bg=DANGER,
                active_bg="#B71C1C",
            ).grid(row=0, column=2, padx=(10, 0), sticky="e")


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
            messagebox.showerror("Load failed", f"Unable to load character data:\n{exc}")
            self.status_var.set("Failed to load character data.")
            return

        self.headers = list(self.repository.headers or DEFAULT_HEADERS)
        for header in self.headers:
            self.variables.setdefault(header, tk.StringVar())

        self.apply_current_sort(save=False)
        self.summary_images.clear()
        self.render_form_fields()
        self.refresh_summary(select_index=select_index)
        self.refresh_formations_list(select_index=self.selected_formation_index)
        self.render_formation_editor()
        self.render_character_action_bar()

        if select_index is None or not self.rows:
            self.clear_form(keep_status=True)
        else:
            self.select_item(min(select_index, len(self.rows) - 1))

        self.summary_count_var.set(f"{len(self.rows)} character(s)")
        self.status_var.set(f"Loaded {len(self.rows)} character(s) from {self.characters_path.name}.")

    def row_sort_key_lb(self, row: dict[str, str]) -> tuple[int, int, int, int]:
        return (
            L_ORDER.get((row.get("L", "") or "").strip().upper(), len(L_ORDER)),
            -parse_int(row.get("B", "")),
            -parse_int(row.get("R", "")),
            RARITY_ORDER.get((row.get("Rarity", "") or "").strip(), len(RARITY_ORDER)),
        )

    def row_sort_key_rarity(self, row: dict[str, str]) -> tuple[int, int, int, int]:
        return (
            RARITY_ORDER.get((row.get("Rarity", "") or "").strip(), len(RARITY_ORDER)),
            L_ORDER.get((row.get("L", "") or "").strip().upper(), len(L_ORDER)),
            -parse_int(row.get("B", "")),
            -parse_int(row.get("R", "")),
        )

    def row_sort_key_color(self, row: dict[str, str]) -> tuple[int, int, int, int, int]:
        return (
            COLOR_ORDER.get((row.get("Color", "") or "").strip().upper(), len(COLOR_ORDER)),
            RARITY_ORDER.get((row.get("Rarity", "") or "").strip(), len(RARITY_ORDER)),
            L_ORDER.get((row.get("L", "") or "").strip().upper(), len(L_ORDER)),
            -parse_int(row.get("B", "")),
            -parse_int(row.get("R", "")),
        )

    def apply_current_sort(self, save: bool) -> None:
        if not self.rows:
            return

        selected_row = self.rows[self.selected_index] if self.selected_index is not None and 0 <= self.selected_index < len(self.rows) else None
        sort_mode = self.sort_mode_var.get()
        if sort_mode == "Sort by Rarity":
            self.rows.sort(key=self.row_sort_key_rarity)
        elif sort_mode == "Sort by Color":
            self.rows.sort(key=self.row_sort_key_color)
        else:
            self.rows.sort(key=self.row_sort_key_lb)

        if selected_row is not None:
            try:
                self.selected_index = self.rows.index(selected_row)
            except ValueError:
                self.selected_index = None

        if save:
            self.repository.save(self.rows)

    def on_sort_changed(self, _event: tk.Event | None = None) -> None:
        self.apply_current_sort(save=True)
        self.summary_images.clear()
        self.refresh_summary(select_index=self.selected_index)
        if self.selected_index is not None:
            self.select_item(self.selected_index)
        self.status_var.set(f"Applied {self.sort_mode_var.get().lower()}.")

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
        meta = " â€¢ ".join(
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
        self.render_character_action_bar()
        self.status_var.set(f"Selected character #{index + 1}: {row.get('Name', '(no name)')}")

    def clear_form(self, keep_status: bool = False) -> None:
        self.selected_index = None
        for header in self.headers:
            self.variables[header].set("")

        self.selected_title_var.set("New Character")
        self.summary_images.clear()
        self.refresh_summary(select_index=None)
        self.update_icon_preview()
        self.render_character_action_bar()
        if not keep_status:
            self.status_var.set("Editor cleared. Ready for a new character.")

    def collect_form_data(self) -> dict[str, str]:
        return {header: self.variables[header].get().strip() for header in self.headers}

    def create_row(self) -> None:
        row: dict[str, str] | None = None
        previous_rows = [existing.copy() for existing in self.rows]
        try:
            row = self.prepare_row_for_save()
            self.rows.append(row)
            self.apply_current_sort(save=True)
        except Exception as exc:
            self.rows = previous_rows
            messagebox.showerror("Create failed", str(exc))
            self.status_var.set("Unable to create character.")
            return

        new_index = self.rows.index(row) if row in self.rows else len(self.rows) - 1
        self.summary_count_var.set(f"{len(self.rows)} character(s)")
        self.select_item(new_index)
        self.render_formation_editor()
        self.status_var.set(f"Created character: {row.get('Name', '(no name)')}")

    def update_row(self) -> None:
        if self.selected_index is None:
            messagebox.showwarning("No selection", "Select a character from the summary list first.")
            return

        index = self.selected_index
        previous_row = self.rows[index].copy()
        previous_rows = [existing.copy() for existing in self.rows]
        previous_formations = self.clone_formations_state()
        row: dict[str, str] | None = None
        try:
            row = self.prepare_row_for_save()
            self.rows[index] = row
            self.rename_character_in_formations(previous_row, row)
            self.apply_current_sort(save=True)
            self.formation_repository.save(self.formations)
        except Exception as exc:
            self.rows = previous_rows
            self.formations = previous_formations
            messagebox.showerror("Update failed", str(exc))
            self.status_var.set("Unable to update character.")
            return

        updated_index = self.rows.index(row) if row in self.rows else index
        self.select_item(updated_index)
        self.refresh_formations_list(select_index=self.selected_formation_index)
        self.render_formation_editor()
        self.status_var.set(f"Updated character: {row.get('Name', '(no name)')}")

    def delete_row(self) -> None:
        if self.selected_index is None:
            messagebox.showwarning("No selection", "Select a character from the summary list first.")
            return

        index = self.selected_index
        row = self.rows[index]
        item_name = row.get("Name", "(no name)")
        assigned_team = self.get_character_team(character_version_key(row))
        if assigned_team is not None:
            messagebox.showwarning(
                "Character in team",
                f"Remove '{item_name}' from team '{assigned_team}' before deleting the character.",
            )
            return
        confirmed = messagebox.askyesno("Delete character", f"Delete '{item_name}' from the character store?")
        if not confirmed:
            return

        previous_rows = [existing.copy() for existing in self.rows]
        deleted_row = self.rows.pop(index)
        try:
            self.apply_current_sort(save=True)
        except Exception as exc:
            self.rows = previous_rows
            messagebox.showerror("Delete failed", str(exc))
            self.status_var.set("Unable to delete character.")
            return

        self.summary_count_var.set(f"{len(self.rows)} character(s)")
        if self.rows:
            self.select_item(min(index, len(self.rows) - 1))
        else:
            self.clear_form(keep_status=True)
        self.render_formation_editor()
        self.status_var.set(f"Deleted character: {item_name}")

    def rename_character_in_formations(
        self,
        previous_row: dict[str, str],
        new_row: dict[str, str],
    ) -> None:
        old_key = character_version_key(previous_row)
        new_key = character_version_key(new_row)
        if not old_key or not new_key or old_key == new_key:
            return

        for formation in self.formations:
            teams = formation.get("teams", {})
            for team_name in TEAM_OPTIONS:
                slots = teams.get(team_name, {})
                for slot_key in FORMATION_SLOT_ORDER:
                    assigned = str(slots.get(slot_key, "") or "").strip()
                    assigned_row = self.find_character_row(assigned)
                    if self.rows_match_assignment(previous_row, assigned_row, old_key, assigned):
                        slots[slot_key] = new_key

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

        request = Request(url, headers={"User-Agent": "ToG-Character-Manager/1.0"})
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


