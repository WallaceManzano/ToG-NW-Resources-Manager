
from __future__ import annotations

from datetime import datetime
import tkinter as tk
from tkinter import messagebox, ttk
from typing import TYPE_CHECKING

from ..constants import *
from ..helpers import *

if TYPE_CHECKING:
    from ..app_window import TogCharacterManager


class TowerProgressPanelMixin:
    def _build_tower_progress_tab(self) -> None:
        self.tower_progress_tab.columnconfigure(0, weight=3)
        self.tower_progress_tab.columnconfigure(1, weight=2)
        self.tower_progress_tab.rowconfigure(0, weight=1)

        self.tower_progress_summary_panel = self._make_panel(self.tower_progress_tab)
        self.tower_progress_summary_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 16))
        self.tower_progress_summary_panel.columnconfigure(0, weight=1)
        self.tower_progress_summary_panel.rowconfigure(2, weight=1)

        summary_header = tk.Frame(self.tower_progress_summary_panel, bg=SURFACE)
        summary_header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 12))
        summary_header.columnconfigure(0, weight=1)

        tk.Label(summary_header, text="Tower Progress", bg=SURFACE, fg=TEXT, font=self.section_font).grid(row=0, column=0, sticky="w")
        tk.Label(summary_header, textvariable=self.tower_progress_summary_var, bg=SURFACE, fg=TEXT_MUTED, font=self.body_font).grid(row=1, column=0, sticky="w", pady=(4, 0))
        filter_picker = ttk.Combobox(
            summary_header,
            textvariable=self.tower_progress_mode_filter_var,
            values=TOWER_MODE_FILTER_OPTIONS,
            state="readonly",
            width=18,
        )
        filter_picker.grid(row=0, column=1, rowspan=2, sticky="e")
        filter_picker.bind("<<ComboboxSelected>>", self.on_tower_progress_filter_changed)

        chart_card = tk.Frame(self.tower_progress_summary_panel, bg=SURFACE_MUTED, highlightthickness=1, highlightbackground=BORDER, bd=0, padx=18, pady=18)
        chart_card.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 12))
        chart_card.columnconfigure(0, weight=1)
        chart_card.rowconfigure(1, weight=1)

        tk.Label(chart_card, text="Temporal Evolution", bg=SURFACE_MUTED, fg=TEXT, font=self.section_font).grid(row=0, column=0, sticky="w")
        self.tower_progress_chart_canvas = tk.Canvas(
            chart_card,
            bg=SURFACE,
            highlightthickness=1,
            highlightbackground=BORDER,
            bd=0,
            height=300,
        )
        self.tower_progress_chart_canvas.grid(row=1, column=0, sticky="ew", pady=(14, 0))
        self.tower_progress_chart_canvas.bind("<Configure>", self.on_tower_progress_chart_configure)
        tk.Label(
            chart_card,
            textvariable=self.tower_progress_chart_caption_var,
            bg=SURFACE_MUTED,
            fg=TEXT_MUTED,
            font=self.card_meta_font,
            justify="left",
            wraplength=880,
        ).grid(row=2, column=0, sticky="w", pady=(10, 0))

        history_wrap = tk.Frame(self.tower_progress_summary_panel, bg=SURFACE)
        history_wrap.grid(row=2, column=0, sticky="nsew", padx=16, pady=(0, 16))
        history_wrap.columnconfigure(0, weight=1)
        history_wrap.rowconfigure(1, weight=1)

        history_header = tk.Frame(history_wrap, bg=SURFACE)
        history_header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        history_header.columnconfigure(0, weight=1)
        tk.Label(history_header, text="Snapshots", bg=SURFACE, fg=TEXT, font=self.section_font).grid(row=0, column=0, sticky="w")
        tk.Label(
            history_header,
            text="Select a snapshot to edit or delete it. The list respects the active tower filter.",
            bg=SURFACE,
            fg=TEXT_MUTED,
            font=self.body_font,
            justify="left",
            wraplength=740,
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

        history_scroll_wrap = tk.Frame(history_wrap, bg=SURFACE)
        history_scroll_wrap.grid(row=1, column=0, sticky="nsew")
        history_scroll_wrap.columnconfigure(0, weight=1)
        history_scroll_wrap.rowconfigure(0, weight=1)

        self.tower_progress_history_canvas = tk.Canvas(history_scroll_wrap, bg=SURFACE, highlightthickness=0, bd=0)
        self.tower_progress_history_canvas.grid(row=0, column=0, sticky="nsew")
        history_scroll = ttk.Scrollbar(history_scroll_wrap, orient="vertical", command=self.tower_progress_history_canvas.yview)
        history_scroll.grid(row=0, column=1, sticky="ns")
        self.tower_progress_history_canvas.configure(yscrollcommand=history_scroll.set)

        self.tower_progress_history_container = tk.Frame(self.tower_progress_history_canvas, bg=SURFACE)
        self.tower_progress_history_window = self.tower_progress_history_canvas.create_window((0, 0), window=self.tower_progress_history_container, anchor="nw")
        self.tower_progress_history_container.bind(
            "<Configure>",
            lambda _event: self.tower_progress_history_canvas.configure(scrollregion=self.tower_progress_history_canvas.bbox("all")),
        )
        self.tower_progress_history_canvas.bind(
            "<Configure>",
            lambda event: self.tower_progress_history_canvas.itemconfigure(self.tower_progress_history_window, width=event.width),
        )
        self._bind_mousewheel(self.tower_progress_history_canvas, self.tower_progress_history_container)

        self.tower_progress_editor_panel = self._make_panel(self.tower_progress_tab)
        self.tower_progress_editor_panel.grid(row=0, column=1, sticky="nsew")
        self.tower_progress_editor_panel.columnconfigure(0, weight=1)

        editor_header = tk.Frame(self.tower_progress_editor_panel, bg=SURFACE)
        editor_header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 8))
        editor_header.columnconfigure(0, weight=1)
        tk.Label(editor_header, textvariable=self.tower_progress_title_var, bg=SURFACE, fg=TEXT, font=self.section_font).grid(row=0, column=0, sticky="w")
        tk.Label(
            editor_header,
            text="Save a dated floor snapshot for each tracked tower mode. Future modes can be added by extending the tracked mode list.",
            bg=SURFACE,
            fg=TEXT_MUTED,
            font=self.body_font,
            justify="left",
            wraplength=420,
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

        self.tower_progress_action_bar = tk.Frame(self.tower_progress_editor_panel, bg=SURFACE)
        self.tower_progress_action_bar.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 8))
        self.render_tower_progress_action_bar()

        form_card = tk.Frame(self.tower_progress_editor_panel, bg=SURFACE_MUTED, highlightthickness=1, highlightbackground=BORDER, bd=0, padx=18, pady=18)
        form_card.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 12))
        for column in range(2):
            form_card.columnconfigure(column, weight=1)

        tk.Label(form_card, text="Snapshot Details", bg=SURFACE_MUTED, fg=TEXT, font=self.section_font).grid(row=0, column=0, columnspan=2, sticky="w")
        self._make_input(form_card, "Captured At", self.tower_progress_captured_at_var, 1, 0, columnspan=2)
        for index, mode in enumerate(TOWER_TRACKED_MODES):
            mode_key = str(mode["key"])
            self._make_input(form_card, f"{display_tower_mode_label(mode_key)} Floor", self.tower_progress_mode_vars[mode_key], 2 + (index // 2), index % 2)

        tk.Label(
            form_card,
            text="Accepted dates: ISO (2026-03-24 21:30:00) or local-style day/month/year. Floors must be whole numbers greater than or equal to zero.",
            bg=SURFACE_MUTED,
            fg=TEXT_MUTED,
            font=self.body_font,
            justify="left",
            wraplength=420,
        ).grid(row=3 + ((len(TOWER_TRACKED_MODES) - 1) // 2), column=0, columnspan=2, sticky="w", padx=10, pady=(8, 0))

        latest_card = tk.Frame(self.tower_progress_editor_panel, bg=SURFACE, highlightthickness=1, highlightbackground=BORDER, bd=0, padx=18, pady=18)
        latest_card.grid(row=3, column=0, sticky="ew", padx=16, pady=(0, 16))
        latest_card.columnconfigure(0, weight=1)

        tk.Label(latest_card, text="Latest Recorded Floors", bg=SURFACE, fg=TEXT, font=self.section_font).grid(row=0, column=0, sticky="w")
        tk.Label(latest_card, textvariable=self.tower_progress_latest_time_var, bg=SURFACE, fg=TEXT_MUTED, font=self.body_font).grid(row=1, column=0, sticky="w", pady=(4, 12))

        metrics_row = tk.Frame(latest_card, bg=SURFACE)
        metrics_row.grid(row=2, column=0, sticky="ew")
        for index, mode in enumerate(TOWER_TRACKED_MODES):
            metrics_row.columnconfigure(index, weight=1)
            mode_key = str(mode["key"])
            self._create_tower_metric_tile(metrics_row, display_tower_mode_label(mode_key), self.tower_progress_latest_floor_vars[mode_key], index)

    def _create_tower_metric_tile(self, parent: tk.Misc, title: str, variable: tk.StringVar, column: int) -> None:
        tile = tk.Frame(parent, bg=SURFACE_MUTED, highlightthickness=1, highlightbackground=BORDER, bd=0, padx=12, pady=10)
        tile.grid(row=0, column=column, sticky="ew", padx=(0, 8) if column < len(TOWER_TRACKED_MODES) - 1 else (0, 0))
        tk.Label(tile, text=title, bg=SURFACE_MUTED, fg=TEXT_MUTED, font=self.label_font).pack(anchor="w")
        tk.Label(tile, textvariable=variable, bg=SURFACE_MUTED, fg=PRIMARY_DARK, font=self.section_font).pack(anchor="w", pady=(6, 0))

    def render_tower_progress_action_bar(self) -> None:
        for child in self.tower_progress_action_bar.winfo_children():
            child.destroy()

        if self.selected_tower_progress_index is None:
            self.tower_progress_action_bar.columnconfigure(0, weight=0)
            self.tower_progress_action_bar.columnconfigure(1, weight=1)
            self._make_button(self.tower_progress_action_bar, "New", self.clear_tower_progress_form, filled=False).grid(row=0, column=0, padx=(0, 10), sticky="w")
            self._make_button(self.tower_progress_action_bar, "Save Snapshot", self.create_tower_progress_entry, filled=True).grid(row=0, column=1, sticky="e")
        else:
            self.tower_progress_action_bar.columnconfigure(0, weight=0)
            self.tower_progress_action_bar.columnconfigure(1, weight=1)
            self.tower_progress_action_bar.columnconfigure(2, weight=0)
            self._make_button(self.tower_progress_action_bar, "New", self.clear_tower_progress_form, filled=False).grid(row=0, column=0, padx=(0, 10), sticky="w")
            self._make_button(self.tower_progress_action_bar, "Update Snapshot", self.update_tower_progress_entry, filled=True).grid(row=0, column=1, sticky="e")
            self._make_button(self.tower_progress_action_bar, "Delete", self.delete_tower_progress_entry, filled=True, bg=DANGER, active_bg="#B71C1C").grid(row=0, column=2, padx=(10, 0), sticky="e")

    def refresh_tower_progress_tab_visuals(self) -> None:
        self.draw_tower_progress_chart()

    def get_default_tower_progress_timestamp(self) -> str:
        return datetime.now().astimezone().replace(microsecond=0).strftime("%Y-%m-%d %H:%M:%S")

    def parse_tower_progress_timestamp(self, value: str) -> datetime | None:
        cleaned = str(value or "").strip()
        if not cleaned:
            return None

        local_tz = datetime.now().astimezone().tzinfo
        candidates = [cleaned]
        if "T" not in cleaned and " " in cleaned:
            candidates.append(cleaned.replace(" ", "T", 1))

        for candidate in candidates:
            try:
                parsed = datetime.fromisoformat(candidate.replace("Z", "+00:00"))
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=local_tz)
                return parsed.astimezone(local_tz)
            except ValueError:
                pass

        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d", "%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%d/%m/%Y"):
            try:
                parsed = datetime.strptime(cleaned, fmt).replace(tzinfo=local_tz)
                return parsed.astimezone(local_tz)
            except ValueError:
                continue
        return None

    def format_tower_progress_timestamp(self, value: str, multiline: bool = False) -> str:
        parsed = self.parse_tower_progress_timestamp(value)
        if parsed is None:
            return str(value or "").strip() or "Unknown date"
        if multiline:
            return parsed.strftime("%d/%m\n%H:%M")
        return parsed.strftime("%d/%m/%Y %H:%M:%S")

    def format_tower_progress_timestamp_for_form(self, value: str) -> str:
        parsed = self.parse_tower_progress_timestamp(value)
        if parsed is None:
            return str(value or "").strip()
        return parsed.strftime("%Y-%m-%d %H:%M:%S")

    def get_tower_progress_sort_key(self, entry: dict[str, object]) -> tuple[float, str]:
        captured_at = str(entry.get("captured_at", "") or "").strip()
        parsed = self.parse_tower_progress_timestamp(captured_at)
        timestamp = parsed.timestamp() if parsed is not None else float("-inf")
        return (timestamp, captured_at)

    def sort_tower_progress_entries(self) -> None:
        self.tower_progress_entries.sort(key=self.get_tower_progress_sort_key)

    def get_sorted_tower_progress_entries(self, descending: bool) -> list[tuple[int, dict[str, object]]]:
        return sorted(list(enumerate(self.tower_progress_entries)), key=lambda item: self.get_tower_progress_sort_key(item[1]), reverse=descending)

    def get_active_tower_mode_key(self) -> str | None:
        selected = self.tower_progress_mode_filter_var.get().strip()
        if not selected or selected == TOWER_FILTER_ALL:
            return None
        canonical = canonical_tower_mode_key(selected)
        return canonical or None

    def get_visible_tower_mode_keys(self) -> list[str]:
        active_mode = self.get_active_tower_mode_key()
        if active_mode is not None:
            return [active_mode]
        return [str(mode["key"]) for mode in TOWER_TRACKED_MODES]

    def clone_tower_progress_entries(self) -> list[dict[str, object]]:
        cloned: list[dict[str, object]] = []
        for entry in self.tower_progress_entries:
            raw_floors = entry.get("floors", {})
            floors = raw_floors if isinstance(raw_floors, dict) else {}
            cloned.append(
                {
                    "captured_at": str(entry.get("captured_at", "") or "").strip(),
                    "floors": {
                        str(mode["key"]): max(0, parse_int(str(floors.get(str(mode["key"]), 0) or "0")))
                        for mode in TOWER_TRACKED_MODES
                    },
                }
            )
        return cloned

    def load_tower_progress_entries(self, select_index: int | None) -> None:
        try:
            self.tower_progress_entries = self.tower_progress_repository.load()
        except Exception as exc:
            messagebox.showerror("Load failed", f"Unable to load tower progress:\n{exc}")
            self.tower_progress_entries = []
            self.status_var.set("Failed to load tower progress.")
            return

        self.sort_tower_progress_entries()
        self.update_tower_progress_summary()
        self.update_latest_tower_progress_metrics()
        self.refresh_tower_progress_history(select_index=select_index)
        self.render_tower_progress_action_bar()
        if select_index is None or not self.tower_progress_entries:
            self.clear_tower_progress_form(keep_status=True, refresh_history=False)
        else:
            self.select_tower_progress_entry(min(select_index, len(self.tower_progress_entries) - 1))
        self.draw_tower_progress_chart()
        self.status_var.set(f"Loaded {len(self.tower_progress_entries)} tower snapshot(s) from {self.tower_progress_path.name}.")

    def update_tower_progress_summary(self) -> None:
        self.tower_progress_summary_var.set(f"{len(self.tower_progress_entries)} snapshot(s) across {len(TOWER_TRACKED_MODES)} tracked tower(s)")

    def update_latest_tower_progress_metrics(self) -> None:
        if not self.tower_progress_entries:
            self.tower_progress_latest_time_var.set("No snapshots saved yet.")
            for mode in TOWER_TRACKED_MODES:
                self.tower_progress_latest_floor_vars[str(mode["key"])].set("-")
            return

        _latest_index, latest_entry = max(enumerate(self.tower_progress_entries), key=lambda item: self.get_tower_progress_sort_key(item[1]))
        floors_map = latest_entry.get("floors", {}) if isinstance(latest_entry.get("floors", {}), dict) else {}
        self.tower_progress_latest_time_var.set(f"Latest snapshot: {self.format_tower_progress_timestamp(str(latest_entry.get('captured_at', '') or ''))}")
        for mode in TOWER_TRACKED_MODES:
            mode_key = str(mode["key"])
            self.tower_progress_latest_floor_vars[mode_key].set(str(parse_int(str(floors_map.get(mode_key, 0) or "0"))))

    def refresh_tower_progress_history(self, select_index: int | None) -> None:
        for child in self.tower_progress_history_container.winfo_children():
            child.destroy()

        if select_index is not None and 0 <= select_index < len(self.tower_progress_entries):
            self.selected_tower_progress_index = select_index
        elif self.selected_tower_progress_index is None or not (0 <= self.selected_tower_progress_index < len(self.tower_progress_entries)):
            self.selected_tower_progress_index = None

        if not self.tower_progress_entries:
            empty = tk.Frame(self.tower_progress_history_container, bg=SURFACE, pady=48)
            empty.pack(fill="x")
            tk.Label(empty, text="No tower snapshots yet", bg=SURFACE, fg=TEXT, font=self.section_font).pack()
            tk.Label(empty, text="Save the first dated floor snapshot to start tracking progression over time.", bg=SURFACE, fg=TEXT_MUTED, font=self.body_font).pack(pady=(6, 0))
            self.selected_tower_progress_index = None
            self._bind_mousewheel(self.tower_progress_history_canvas, empty)
            return

        previous_entry_map: dict[int, dict[str, object] | None] = {}
        previous_entry: dict[str, object] | None = None
        for actual_index, entry in self.get_sorted_tower_progress_entries(descending=False):
            previous_entry_map[actual_index] = previous_entry
            previous_entry = entry

        for actual_index, entry in self.get_sorted_tower_progress_entries(descending=True):
            self._add_tower_progress_card(actual_index, entry, selected=actual_index == self.selected_tower_progress_index, previous_entry=previous_entry_map.get(actual_index))

    def _add_tower_progress_card(self, index: int, entry: dict[str, object], selected: bool, previous_entry: dict[str, object] | None) -> None:
        bg = PRIMARY_SOFT if selected else SURFACE
        border = PRIMARY if selected else BORDER
        card = tk.Frame(self.tower_progress_history_container, bg=bg, highlightthickness=1, highlightbackground=border, bd=0, padx=14, pady=12, cursor="hand2")
        card.pack(fill="x", padx=4, pady=6)
        card.columnconfigure(0, weight=1)

        title = tk.Label(card, text=self.format_tower_progress_timestamp(str(entry.get("captured_at", "") or "")), bg=bg, fg=TEXT, font=self.card_title_font, anchor="w")
        title.grid(row=0, column=0, sticky="w")
        subtitle = tk.Label(card, text=f"Snapshot #{index + 1}", bg=bg, fg=TEXT_MUTED, font=self.card_meta_font, anchor="w")
        subtitle.grid(row=1, column=0, sticky="w", pady=(4, 10))

        metrics = tk.Frame(card, bg=bg)
        metrics.grid(row=2, column=0, sticky="ew")
        metrics.columnconfigure(0, weight=1)

        floors = entry.get("floors", {}) if isinstance(entry.get("floors", {}), dict) else {}
        previous_map = previous_entry.get("floors", {}) if isinstance(previous_entry, dict) and isinstance(previous_entry.get("floors", {}), dict) else {}
        visible_modes = self.get_visible_tower_mode_keys()

        for row_index, mode_key in enumerate(visible_modes):
            line = tk.Frame(metrics, bg=bg)
            line.grid(row=row_index, column=0, sticky="ew", pady=(0, 6) if row_index < len(visible_modes) - 1 else (0, 0))
            line.columnconfigure(1, weight=1)

            floor_value = parse_int(str(floors.get(mode_key, 0) or "0"))
            previous_floor = parse_int(str(previous_map.get(mode_key, floor_value) or floor_value))
            delta = floor_value - previous_floor if previous_entry is not None else None
            if delta is None:
                delta_text = "First snapshot"
                delta_color = TEXT_MUTED
            elif delta > 0:
                delta_text = f"+{delta}"
                delta_color = "#1B5E20"
            elif delta < 0:
                delta_text = str(delta)
                delta_color = DANGER
            else:
                delta_text = "No change"
                delta_color = TEXT_MUTED

            tk.Label(line, text=display_tower_mode_label(mode_key), bg=bg, fg=TEXT_MUTED, font=self.label_font, anchor="w").grid(row=0, column=0, sticky="w")
            tk.Label(line, text=f"Floor {floor_value}", bg=bg, fg=TEXT, font=self.body_font, anchor="w").grid(row=0, column=1, sticky="w", padx=(10, 0))
            tk.Label(line, text=delta_text, bg=bg, fg=delta_color, font=self.label_font, anchor="e").grid(row=0, column=2, sticky="e", padx=(10, 0))

            self._bind_mousewheel(self.tower_progress_history_canvas, line)
            for widget in line.winfo_children():
                widget.bind("<Button-1>", lambda _event, idx=index: self.select_tower_progress_entry(idx))

        for widget in (card, title, subtitle, metrics):
            widget.bind("<Button-1>", lambda _event, idx=index: self.select_tower_progress_entry(idx))
        self._bind_mousewheel(self.tower_progress_history_canvas, card, title, subtitle, metrics)

    def on_tower_progress_filter_changed(self, _event: tk.Event | None = None) -> None:
        self.refresh_tower_progress_history(select_index=self.selected_tower_progress_index)
        self.draw_tower_progress_chart()
        filter_label = self.tower_progress_mode_filter_var.get().strip() or TOWER_FILTER_ALL
        self.status_var.set(f"Showing tower progress for {filter_label}.")

    def select_tower_progress_entry(self, index: int) -> None:
        if not (0 <= index < len(self.tower_progress_entries)):
            return

        self.selected_tower_progress_index = index
        entry = self.tower_progress_entries[index]
        self.tower_progress_captured_at_var.set(self.format_tower_progress_timestamp_for_form(str(entry.get("captured_at", "") or "")))
        floors = entry.get("floors", {}) if isinstance(entry.get("floors", {}), dict) else {}
        for mode in TOWER_TRACKED_MODES:
            mode_key = str(mode["key"])
            self.tower_progress_mode_vars[mode_key].set(str(parse_int(str(floors.get(mode_key, 0) or "0"))))
        self.tower_progress_title_var.set(f"Snapshot on {self.format_tower_progress_timestamp(str(entry.get('captured_at', '') or ''))}")
        self.refresh_tower_progress_history(select_index=index)
        self.render_tower_progress_action_bar()
        self.draw_tower_progress_chart()
        self.status_var.set(f"Selected tower snapshot #{index + 1}.")

    def clear_tower_progress_form(self, keep_status: bool = False, refresh_history: bool = True) -> None:
        self.selected_tower_progress_index = None
        self.tower_progress_captured_at_var.set(self.get_default_tower_progress_timestamp())
        for mode in TOWER_TRACKED_MODES:
            self.tower_progress_mode_vars[str(mode["key"])].set("")
        self.tower_progress_title_var.set("New Tower Snapshot")
        if refresh_history:
            self.refresh_tower_progress_history(select_index=None)
            self.draw_tower_progress_chart()
        self.render_tower_progress_action_bar()
        if not keep_status:
            self.status_var.set("Tower progress form cleared. Ready for a new snapshot.")

    def collect_tower_progress_data(self) -> dict[str, object]:
        return {
            "captured_at": self.tower_progress_captured_at_var.get().strip(),
            "floors": {str(mode["key"]): self.tower_progress_mode_vars[str(mode["key"])].get().strip() for mode in TOWER_TRACKED_MODES},
        }

    def prepare_tower_progress_entry_for_save(self) -> dict[str, object]:
        payload = self.collect_tower_progress_data()
        captured_at_raw = str(payload.get("captured_at", "") or "").strip()
        parsed = self.parse_tower_progress_timestamp(captured_at_raw)
        if parsed is None:
            raise ValueError("Captured At must be a valid date/time.")

        floors_source = payload.get("floors", {}) if isinstance(payload.get("floors", {}), dict) else {}
        normalized_floors: dict[str, int] = {}
        for mode in TOWER_TRACKED_MODES:
            mode_key = str(mode["key"])
            floor_raw = str(floors_source.get(mode_key, "") or "").strip()
            if floor_raw == "":
                raise ValueError(f"{display_tower_mode_label(mode_key)} floor is required.")
            try:
                floor_value = int(floor_raw)
            except ValueError as exc:
                raise ValueError(f"{display_tower_mode_label(mode_key)} floor must be a whole number.") from exc
            if floor_value < 0:
                raise ValueError(f"{display_tower_mode_label(mode_key)} floor cannot be negative.")
            normalized_floors[mode_key] = floor_value

        return {"captured_at": parsed.isoformat(timespec="seconds"), "floors": normalized_floors}

    def create_tower_progress_entry(self) -> None:
        previous_entries = self.clone_tower_progress_entries()
        try:
            entry = self.prepare_tower_progress_entry_for_save()
            self.tower_progress_entries.append(entry)
            self.save_tower_progress_entries()
        except Exception as exc:
            self.tower_progress_entries = previous_entries
            messagebox.showerror("Create failed", str(exc))
            self.status_var.set("Unable to save tower snapshot.")
            return

        new_index = next((idx for idx, existing in enumerate(self.tower_progress_entries) if existing.get("captured_at") == entry.get("captured_at") and existing.get("floors") == entry.get("floors")), len(self.tower_progress_entries) - 1)
        self.select_tower_progress_entry(new_index)
        self.status_var.set("Saved tower snapshot.")

    def update_tower_progress_entry(self) -> None:
        if self.selected_tower_progress_index is None:
            messagebox.showwarning("No selection", "Select a tower snapshot first.")
            return

        previous_entries = self.clone_tower_progress_entries()
        index = self.selected_tower_progress_index
        try:
            entry = self.prepare_tower_progress_entry_for_save()
            self.tower_progress_entries[index] = entry
            self.save_tower_progress_entries()
        except Exception as exc:
            self.tower_progress_entries = previous_entries
            messagebox.showerror("Update failed", str(exc))
            self.status_var.set("Unable to update tower snapshot.")
            return

        updated_index = next((idx for idx, existing in enumerate(self.tower_progress_entries) if existing.get("captured_at") == entry.get("captured_at") and existing.get("floors") == entry.get("floors")), index)
        self.select_tower_progress_entry(updated_index)
        self.status_var.set("Updated tower snapshot.")

    def delete_tower_progress_entry(self) -> None:
        if self.selected_tower_progress_index is None:
            messagebox.showwarning("No selection", "Select a tower snapshot first.")
            return

        index = self.selected_tower_progress_index
        entry = self.tower_progress_entries[index]
        captured_at_text = self.format_tower_progress_timestamp(str(entry.get("captured_at", "") or ""))
        confirmed = messagebox.askyesno("Delete tower snapshot", f"Delete the tower snapshot recorded on '{captured_at_text}'?")
        if not confirmed:
            return

        previous_entries = self.clone_tower_progress_entries()
        self.tower_progress_entries.pop(index)
        try:
            self.save_tower_progress_entries()
        except Exception as exc:
            self.tower_progress_entries = previous_entries
            messagebox.showerror("Delete failed", str(exc))
            self.status_var.set("Unable to delete tower snapshot.")
            return

        if self.tower_progress_entries:
            self.select_tower_progress_entry(min(index, len(self.tower_progress_entries) - 1))
        else:
            self.clear_tower_progress_form(keep_status=True)
        self.status_var.set(f"Deleted tower snapshot from {captured_at_text}.")

    def save_tower_progress_entries(self) -> None:
        self.sort_tower_progress_entries()
        self.tower_progress_repository.save(self.tower_progress_entries)
        self.update_tower_progress_summary()
        self.update_latest_tower_progress_metrics()
        self.refresh_tower_progress_history(select_index=self.selected_tower_progress_index)
        self.draw_tower_progress_chart()

    def on_tower_progress_chart_configure(self, _event: tk.Event | None = None) -> None:
        self.draw_tower_progress_chart()

    def draw_tower_progress_chart(self) -> None:
        canvas = getattr(self, "tower_progress_chart_canvas", None)
        if canvas is None or not canvas.winfo_exists():
            return

        canvas.delete("all")
        width = max(480, canvas.winfo_width())
        height = max(260, canvas.winfo_height())
        canvas.configure(width=width, height=height)

        if not self.tower_progress_entries:
            canvas.create_text(width // 2, height // 2, text="Save snapshots to draw the tower evolution chart.", fill=TEXT_MUTED, font=self.body_font)
            self.tower_progress_chart_caption_var.set("No tower snapshots available yet.")
            return

        visible_mode_keys = self.get_visible_tower_mode_keys()
        ordered_entries = self.get_sorted_tower_progress_entries(descending=False)
        series: dict[str, list[dict[str, float | int | str]]] = {mode_key: [] for mode_key in visible_mode_keys}
        for actual_index, entry in ordered_entries:
            parsed = self.parse_tower_progress_timestamp(str(entry.get("captured_at", "") or ""))
            if parsed is None:
                continue
            floors = entry.get("floors", {}) if isinstance(entry.get("floors", {}), dict) else {}
            for mode_key in visible_mode_keys:
                series[mode_key].append(
                    {
                        "timestamp": parsed.timestamp(),
                        "floor": parse_int(str(floors.get(mode_key, 0) or "0")),
                        "label": self.format_tower_progress_timestamp(str(entry.get("captured_at", "") or ""), multiline=True),
                        "index": actual_index,
                    }
                )

        all_points = [point for points in series.values() for point in points]
        if not all_points:
            canvas.create_text(width // 2, height // 2, text="No valid dated snapshots available for the chart.", fill=TEXT_MUTED, font=self.body_font)
            self.tower_progress_chart_caption_var.set("No valid dated snapshots available for the chart.")
            return

        plot_left = 56
        plot_top = 28
        plot_right = width - 24
        plot_bottom = height - 52
        plot_width = max(1, plot_right - plot_left)
        plot_height = max(1, plot_bottom - plot_top)
        canvas.create_rectangle(plot_left, plot_top, plot_right, plot_bottom, outline=BORDER, fill=SURFACE)

        timestamps = [float(point["timestamp"]) for point in all_points]
        floors = [int(point["floor"]) for point in all_points]
        min_time = min(timestamps)
        max_time = max(timestamps)
        min_floor = min(floors)
        max_floor = max(floors)
        floor_padding = max(1, (max_floor - min_floor) // 5 if max_floor != min_floor else max(1, max_floor // 10))
        y_min = max(0, min_floor - floor_padding)
        y_max = max_floor + floor_padding
        if y_max <= y_min:
            y_max = y_min + 1

        def scale_x(value: float) -> float:
            if max_time == min_time:
                return plot_left + (plot_width / 2)
            return plot_left + (((value - min_time) / (max_time - min_time)) * plot_width)

        def scale_y(value: int) -> float:
            return plot_bottom - (((value - y_min) / (y_max - y_min)) * plot_height)

        for tick in range(5):
            ratio = tick / 4
            y = plot_bottom - (ratio * plot_height)
            floor_value = round(y_min + ((y_max - y_min) * ratio))
            canvas.create_line(plot_left, y, plot_right, y, fill=PRIMARY_SOFT if tick not in {0, 4} else BORDER)
            canvas.create_text(plot_left - 10, y, text=str(floor_value), fill=TEXT_MUTED, font=self.card_meta_font, anchor="e")

        tick_positions = sorted({0, len(ordered_entries) // 3, (2 * len(ordered_entries)) // 3, len(ordered_entries) - 1})
        for tick_index in tick_positions:
            point = next((points[min(tick_index, len(points) - 1)] for points in series.values() if points), None)
            if point is None:
                continue
            x = scale_x(float(point["timestamp"]))
            canvas.create_line(x, plot_bottom, x, plot_bottom + 4, fill=BORDER)
            canvas.create_text(x, plot_bottom + 12, text=str(point["label"]), fill=TEXT_MUTED, font=self.card_meta_font, anchor="n")

        legend_x = plot_left + 12
        legend_y = plot_top + 12
        for mode_index, mode_key in enumerate(visible_mode_keys):
            points = series.get(mode_key, [])
            if not points:
                continue
            accent = TOWER_MODE_ACCENTS.get(mode_key, PRIMARY)
            coords: list[float] = []
            for point in points:
                coords.extend((scale_x(float(point["timestamp"])), scale_y(int(point["floor"]))))
            if len(coords) >= 4:
                canvas.create_line(*coords, fill=accent, width=3)

            for point in points:
                x = scale_x(float(point["timestamp"]))
                y = scale_y(int(point["floor"]))
                radius = 4 if int(point["index"]) == self.selected_tower_progress_index else 3
                canvas.create_oval(x - radius, y - radius, x + radius, y + radius, outline=accent, fill=SURFACE, width=2)

            last_point = points[-1]
            last_x = scale_x(float(last_point["timestamp"]))
            last_y = scale_y(int(last_point["floor"]))
            canvas.create_text(min(plot_right - 6, last_x + 10), last_y, text=f"{display_tower_mode_label(mode_key)}: {int(last_point['floor'])}", fill=accent, font=self.label_font, anchor="w")

            if len(visible_mode_keys) > 1:
                y = legend_y + (mode_index * 18)
                canvas.create_line(legend_x, y, legend_x + 20, y, fill=accent, width=3)
                canvas.create_text(legend_x + 28, y, text=display_tower_mode_label(mode_key), fill=TEXT_MUTED, font=self.card_meta_font, anchor="w")

        active_mode = self.get_active_tower_mode_key()
        if active_mode is not None and series.get(active_mode):
            points = series[active_mode]
            first_floor = int(points[0]["floor"])
            last_floor = int(points[-1]["floor"])
            delta = last_floor - first_floor
            delta_text = f"{delta:+d}" if delta != 0 else "0"
            self.tower_progress_chart_caption_var.set(f"{display_tower_mode_label(active_mode)} across {len(points)} snapshot(s): floor {first_floor} to {last_floor} ({delta_text}).")
        else:
            self.tower_progress_chart_caption_var.set(f"Showing {', '.join(display_tower_mode_label(mode_key) for mode_key in visible_mode_keys)} across {len(ordered_entries)} snapshot(s).")
