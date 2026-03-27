
from __future__ import annotations

import base64
import io
import json
import threading
import tkinter as tk
from datetime import datetime, timedelta
from tkinter import messagebox, ttk


_PATCHED = False


def apply_runtime_patches() -> None:
    global _PATCHED
    if _PATCHED:
        return

    from tog_app.constants import (
        BORDER,
        DANGER,
        PRIMARY,
        PRIMARY_DARK,
        PRIMARY_SOFT,
        SURFACE,
        SURFACE_MUTED,
        TEXT,
        TEXT_MUTED,
        TOWER_FILTER_ALL,
        TOWER_MODE_ACCENTS,
        TOWER_MODE_FILTER_OPTIONS,
        TOWER_TRACKED_MODES,
    )
    from tog_app.helpers import display_tower_mode_label, format_decimal, normalize_item_name, parse_float, parse_int
    from tog_app.panels.packs import PacksPanelMixin
    from tog_app.panels.tower_progress import TowerProgressPanelMixin
    from tog_app.repositories import PackRepository

    def _ensure_tower_progress_async_state(self) -> None:
        if not hasattr(self, "tower_progress_chart_request_id"):
            self.tower_progress_chart_request_id = 0
        if not hasattr(self, "tower_progress_chart_payload"):
            self.tower_progress_chart_payload = None
        if not hasattr(self, "tower_progress_chart_pending_result"):
            self.tower_progress_chart_pending_result = None
        if not hasattr(self, "tower_progress_chart_worker"):
            self.tower_progress_chart_worker = None
        if not hasattr(self, "tower_progress_chart_image"):
            self.tower_progress_chart_image = None

    def _get_tower_progress_chart_size(self) -> tuple[int, int]:
        canvas = getattr(self, "tower_progress_chart_canvas", None)
        if canvas is None or not canvas.winfo_exists():
            return (720, 300)
        width = max(480, int(canvas.winfo_width() or 0))
        height = max(260, int(canvas.winfo_height() or 0))
        return width, height

    def _build_tower_progress_tab(self) -> None:
        self._ensure_tower_progress_async_state()
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

        chart_card = tk.Frame(
            self.tower_progress_summary_panel,
            bg=SURFACE_MUTED,
            highlightthickness=1,
            highlightbackground=BORDER,
            bd=0,
            padx=18,
            pady=18,
        )
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
            text="Save a floor snapshot using the current date and time. Future modes can be added by extending the tracked mode list.",
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
        for index, mode in enumerate(TOWER_TRACKED_MODES):
            mode_key = str(mode["key"])
            self._make_input(
                form_card,
                f"{display_tower_mode_label(mode_key)} Floor",
                self.tower_progress_mode_vars[mode_key],
                1 + (index // 2),
                index % 2,
            )

        tk.Label(
            form_card,
            text="When you save a snapshot, the app records the current date and time automatically. Floors must be whole numbers greater than or equal to zero.",
            bg=SURFACE_MUTED,
            fg=TEXT_MUTED,
            font=self.body_font,
            justify="left",
            wraplength=420,
        ).grid(row=2 + ((len(TOWER_TRACKED_MODES) - 1) // 2), column=0, columnspan=2, sticky="w", padx=10, pady=(8, 0))

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

    def refresh_tower_progress_tab_visuals(self) -> None:
        payload = getattr(self, "tower_progress_chart_payload", None)
        payload_size = None
        if isinstance(payload, dict):
            payload_size = payload.get("size")
        current_size = self._get_tower_progress_chart_size()
        worker = getattr(self, "tower_progress_chart_worker", None)

        if payload is None or payload_size != current_size:
            if worker is not None and getattr(worker, "is_alive", lambda: False)():
                self._render_tower_progress_chart_message("Loading temporal evolution...")
            else:
                self.request_tower_progress_chart_refresh()
            return
        self.draw_tower_progress_chart()

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
        self.request_tower_progress_chart_refresh()
        self.status_var.set(f"Loaded {len(self.tower_progress_entries)} tower snapshot(s) from {self.tower_progress_path.name}.")

    def on_tower_progress_filter_changed(self, _event: tk.Event | None = None) -> None:
        self.refresh_tower_progress_history(select_index=self.selected_tower_progress_index)
        self.request_tower_progress_chart_refresh()
        filter_label = self.tower_progress_mode_filter_var.get().strip() or TOWER_FILTER_ALL
        self.status_var.set(f"Showing tower progress for {filter_label}.")

    def select_tower_progress_entry(self, index: int) -> None:
        if not (0 <= index < len(self.tower_progress_entries)):
            return

        self.selected_tower_progress_index = index
        entry = self.tower_progress_entries[index]
        floors = entry.get("floors", {}) if isinstance(entry.get("floors", {}), dict) else {}
        for mode in TOWER_TRACKED_MODES:
            mode_key = str(mode["key"])
            self.tower_progress_mode_vars[mode_key].set(str(parse_int(str(floors.get(mode_key, 0) or "0"))))
        self.tower_progress_title_var.set(f"Snapshot on {self.format_tower_progress_timestamp(str(entry.get('captured_at', '') or ''))}")
        self.refresh_tower_progress_history(select_index=index)
        self.render_tower_progress_action_bar()
        self.request_tower_progress_chart_refresh()
        self.status_var.set(f"Selected tower snapshot #{index + 1}.")

    def clear_tower_progress_form(self, keep_status: bool = False, refresh_history: bool = True) -> None:
        self.selected_tower_progress_index = None
        for mode in TOWER_TRACKED_MODES:
            self.tower_progress_mode_vars[str(mode["key"])].set("")
        self.tower_progress_title_var.set("New Tower Snapshot")
        if refresh_history:
            self.refresh_tower_progress_history(select_index=None)
            self.request_tower_progress_chart_refresh()
        self.render_tower_progress_action_bar()
        if not keep_status:
            self.status_var.set("Tower progress form cleared. Ready for a new snapshot.")

    def get_tower_progress_fallback_floors(self, source_index: int | None = None) -> dict[str, int]:
        candidate_entry: dict[str, object] | None = None
        if source_index is not None and 0 <= source_index < len(self.tower_progress_entries):
            candidate_entry = self.tower_progress_entries[source_index]
        elif self.tower_progress_entries:
            candidate_entry = max(self.tower_progress_entries, key=self.get_tower_progress_sort_key)

        if candidate_entry is None:
            return {}

        floors = candidate_entry.get("floors", {}) if isinstance(candidate_entry.get("floors", {}), dict) else {}
        fallback_floors: dict[str, int] = {}
        for mode in TOWER_TRACKED_MODES:
            mode_key = str(mode["key"])
            fallback_floors[mode_key] = parse_int(str(floors.get(mode_key, 0) or "0"))
        return fallback_floors

    def prepare_tower_progress_entry_for_save(
        self,
        captured_at_override: str | None = None,
        fallback_floors: dict[str, int] | None = None,
    ) -> dict[str, object]:
        payload = self.collect_tower_progress_data()
        floors_source = payload.get("floors", {}) if isinstance(payload.get("floors", {}), dict) else {}
        normalized_floors: dict[str, int] = {}
        fallback_floors = fallback_floors or {}
        for mode in TOWER_TRACKED_MODES:
            mode_key = str(mode["key"])
            floor_raw = str(floors_source.get(mode_key, "") or "").strip()
            if floor_raw == "":
                if mode_key not in fallback_floors:
                    raise ValueError(f"{display_tower_mode_label(mode_key)} floor is required for the first snapshot.")
                floor_value = int(fallback_floors[mode_key])
            else:
                try:
                    floor_value = int(floor_raw)
                except ValueError as exc:
                    raise ValueError(f"{display_tower_mode_label(mode_key)} floor must be a whole number.") from exc
            if floor_value < 0:
                raise ValueError(f"{display_tower_mode_label(mode_key)} floor cannot be negative.")
            normalized_floors[mode_key] = floor_value

        if captured_at_override:
            parsed = self.parse_tower_progress_timestamp(captured_at_override)
            if parsed is None:
                parsed = datetime.now().astimezone().replace(microsecond=0)
        else:
            parsed = datetime.now().astimezone().replace(microsecond=0)

        return {"captured_at": parsed.isoformat(timespec="seconds"), "floors": normalized_floors}

    def create_tower_progress_entry(self) -> None:
        previous_entries = self.clone_tower_progress_entries()
        try:
            fallback_floors = self.get_tower_progress_fallback_floors()
            entry = self.prepare_tower_progress_entry_for_save(fallback_floors=fallback_floors)
            self.tower_progress_entries.append(entry)
            self.save_tower_progress_entries()
        except Exception as exc:
            self.tower_progress_entries = previous_entries
            messagebox.showerror("Create failed", str(exc))
            self.status_var.set("Unable to save tower snapshot.")
            return

        self.clear_tower_progress_form(keep_status=True)
        self.status_var.set(f"Saved tower snapshot for {self.format_tower_progress_timestamp(str(entry.get('captured_at', '') or ''))}. Ready for a new snapshot.")

    def update_tower_progress_entry(self) -> None:
        if self.selected_tower_progress_index is None:
            messagebox.showwarning("No selection", "Select a tower snapshot first.")
            return

        previous_entries = self.clone_tower_progress_entries()
        index = self.selected_tower_progress_index
        existing_entry = self.tower_progress_entries[index]
        try:
            fallback_floors = self.get_tower_progress_fallback_floors(source_index=index)
            entry = self.prepare_tower_progress_entry_for_save(
                str(existing_entry.get("captured_at", "") or ""),
                fallback_floors=fallback_floors,
            )
            self.tower_progress_entries[index] = entry
            self.save_tower_progress_entries()
        except Exception as exc:
            self.tower_progress_entries = previous_entries
            messagebox.showerror("Update failed", str(exc))
            self.status_var.set("Unable to update tower snapshot.")
            return

        self.clear_tower_progress_form(keep_status=True)
        self.status_var.set("Updated tower snapshot. Ready for a new snapshot.")

    def save_tower_progress_entries(self) -> None:
        self.sort_tower_progress_entries()
        self.tower_progress_repository.save(self.tower_progress_entries)
        self.update_tower_progress_summary()
        self.update_latest_tower_progress_metrics()
        self.refresh_tower_progress_history(select_index=self.selected_tower_progress_index)
        self.request_tower_progress_chart_refresh()

    def _render_tower_progress_chart_message(self, message: str) -> None:
        canvas = getattr(self, "tower_progress_chart_canvas", None)
        if canvas is None or not canvas.winfo_exists():
            return
        canvas.delete("all")
        width, height = self._get_tower_progress_chart_size()
        canvas.create_text(width // 2, height // 2, text=message, fill=TEXT_MUTED, font=self.body_font)

    def on_tower_progress_chart_configure(self, _event: tk.Event | None = None) -> None:
        self.refresh_tower_progress_tab_visuals()

    def request_tower_progress_chart_refresh(self) -> None:
        self._ensure_tower_progress_async_state()
        request_id = self.tower_progress_chart_request_id + 1
        self.tower_progress_chart_request_id = request_id
        self.tower_progress_chart_pending_result = None
        self.tower_progress_chart_payload = None

        entries = self.clone_tower_progress_entries()
        active_mode_key = self.get_active_tower_mode_key()
        visible_mode_keys = [active_mode_key] if active_mode_key is not None else [str(mode["key"]) for mode in TOWER_TRACKED_MODES]
        width, height = self._get_tower_progress_chart_size()

        self.tower_progress_chart_caption_var.set("Loading temporal evolution...")
        self._render_tower_progress_chart_message("Loading temporal evolution...")

        self.tower_progress_chart_worker = threading.Thread(
            target=self._build_tower_progress_chart_payload_worker,
            args=(request_id, entries, visible_mode_keys, active_mode_key, width, height, self.selected_tower_progress_index),
            daemon=True,
        )
        self.tower_progress_chart_worker.start()
        self.after(40, lambda req_id=request_id: self._poll_tower_progress_chart_refresh(req_id))

    def _build_tower_progress_chart_payload_worker(
        self,
        request_id: int,
        entries: list[dict[str, object]],
        visible_mode_keys: list[str],
        active_mode_key: str | None,
        width: int,
        height: int,
        selected_index: int | None,
    ) -> None:
        try:
            payload = self.build_tower_progress_chart_payload(entries, visible_mode_keys, active_mode_key, width, height, selected_index)
        except Exception as exc:
            self.tower_progress_chart_pending_result = {
                "request_id": request_id,
                "error": str(exc),
            }
            return

        self.tower_progress_chart_pending_result = {
            "request_id": request_id,
            "payload": payload,
        }

    def _poll_tower_progress_chart_refresh(self, request_id: int) -> None:
        if getattr(self, "tower_progress_chart_request_id", 0) != request_id:
            return

        pending_result = getattr(self, "tower_progress_chart_pending_result", None)
        if pending_result is None or pending_result.get("request_id") != request_id:
            self.after(40, lambda req_id=request_id: self._poll_tower_progress_chart_refresh(req_id))
            return

        self.tower_progress_chart_pending_result = None
        self._finish_tower_progress_chart_refresh(pending_result)

    def _finish_tower_progress_chart_refresh(self, payload: dict[str, object]) -> None:
        error = str(payload.get("error", "") or "")
        if error:
            self.tower_progress_chart_payload = {
                "state": "error",
                "message": "Unable to load temporal evolution.",
                "caption": error,
                "size": self._get_tower_progress_chart_size(),
            }
        else:
            self.tower_progress_chart_payload = payload.get("payload")
        self.draw_tower_progress_chart()
        self.tower_progress_chart_worker = None

    def build_tower_progress_chart_payload(
        self,
        entries: list[dict[str, object]],
        visible_mode_keys: list[str],
        active_mode_key: str | None,
        width: int,
        height: int,
        selected_index: int | None,
    ) -> dict[str, object]:
        if not entries:
            return {
                "state": "empty",
                "message": "Save snapshots to draw the tower evolution chart.",
                "caption": "No tower snapshots available yet.",
                "size": (width, height),
            }

        ordered_entries = sorted(list(enumerate(entries)), key=lambda item: self.get_tower_progress_sort_key(item[1]))
        series: dict[str, list[dict[str, object]]] = {mode_key: [] for mode_key in visible_mode_keys}

        for actual_index, entry in ordered_entries:
            captured_at = str(entry.get("captured_at", "") or "")
            parsed = self.parse_tower_progress_timestamp(captured_at)
            if parsed is None:
                continue
            floors = entry.get("floors", {}) if isinstance(entry.get("floors", {}), dict) else {}
            for mode_key in visible_mode_keys:
                series[mode_key].append(
                    {
                        "dt": parsed,
                        "floor": parse_int(str(floors.get(mode_key, 0) or "0")),
                        "index": actual_index,
                    }
                )

        all_points = [point for points in series.values() for point in points]
        snapshot_datetimes: list[datetime] = []
        if visible_mode_keys:
            snapshot_datetimes = [point["dt"] for point in series.get(visible_mode_keys[0], [])]
        snapshot_datetimes = list(dict.fromkeys(snapshot_datetimes))
        if not all_points:
            return {
                "state": "empty",
                "message": "No valid dated snapshots available for the chart.",
                "caption": "No valid dated snapshots available for the chart.",
                "size": (width, height),
            }

        if active_mode_key is not None and series.get(active_mode_key):
            active_points = series[active_mode_key]
            first_floor = int(active_points[0]["floor"])
            last_floor = int(active_points[-1]["floor"])
            delta = last_floor - first_floor
            delta_text = f"{delta:+d}" if delta != 0 else "0"
            caption = f"{display_tower_mode_label(active_mode_key)} across {len(active_points)} snapshot(s): floor {first_floor} to {last_floor} ({delta_text})."
        else:
            caption = f"Showing {', '.join(display_tower_mode_label(mode_key) for mode_key in visible_mode_keys)} across {len(snapshot_datetimes)} snapshot(s)."

        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.dates as mdates
            import matplotlib.pyplot as plt
        except Exception as exc:
            return {
                "state": "error",
                "message": "Matplotlib is unavailable for tower progress charts.",
                "caption": str(exc),
                "size": (width, height),
            }

        figure_width = max(4.8, width / 100)
        figure_height = max(2.6, height / 100)
        fig, ax = plt.subplots(figsize=(figure_width, figure_height), dpi=100)
        fig.patch.set_facecolor(SURFACE)
        ax.set_facecolor(SURFACE)

        for spine in ax.spines.values():
            spine.set_color(BORDER)

        ax.grid(True, axis="y", color=PRIMARY_SOFT, linewidth=0.8)
        ax.tick_params(axis="x", colors=TEXT_MUTED, labelsize=8)
        ax.tick_params(axis="y", colors=TEXT_MUTED, labelsize=8)
        ax.set_ylabel("Floor", color=TEXT_MUTED)

        min_dt = min(point["dt"] for point in all_points)
        max_dt = max(point["dt"] for point in all_points)
        if min_dt == max_dt:
            ax.set_xlim(min_dt - timedelta(hours=12), max_dt + timedelta(hours=12))

        if snapshot_datetimes:
            ax.set_xticks(snapshot_datetimes)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m\n%H:%M"))

        for mode_key in visible_mode_keys:
            points = series.get(mode_key, [])
            if not points:
                continue
            accent = TOWER_MODE_ACCENTS.get(mode_key, PRIMARY)
            x_values = [point["dt"] for point in points]
            y_values = [int(point["floor"]) for point in points]
            ax.plot(x_values, y_values, color=accent, linewidth=2.4, marker="o", markersize=5, label=display_tower_mode_label(mode_key))

            if selected_index is not None:
                selected_points = [point for point in points if int(point["index"]) == selected_index]
                if selected_points:
                    selected_point = selected_points[-1]
                    ax.scatter([selected_point["dt"]], [int(selected_point["floor"])], color=accent, s=90, edgecolors=SURFACE, linewidths=1.6, zorder=5)

            last_point = points[-1]
            ax.annotate(
                f"{display_tower_mode_label(mode_key)}: {int(last_point['floor'])}",
                xy=(last_point["dt"], int(last_point["floor"])),
                xytext=(8, 0),
                textcoords="offset points",
                color=accent,
                fontsize=8,
                fontweight="bold",
                va="center",
            )

        ax.set_ylim(bottom=0)

        if len(visible_mode_keys) > 1:
            legend = ax.legend(frameon=False, loc="upper left")
            if legend is not None:
                for text in legend.get_texts():
                    text.set_color(TEXT_MUTED)

        fig.subplots_adjust(left=0.10, right=0.98, top=0.92, bottom=0.22)
        buffer = io.BytesIO()
        fig.savefig(buffer, format="png", facecolor=fig.get_facecolor())
        plt.close(fig)
        image_data = base64.b64encode(buffer.getvalue()).decode("ascii")

        return {
            "state": "ready",
            "image_data": image_data,
            "caption": caption,
            "size": (width, height),
        }

    def draw_tower_progress_chart(self) -> None:
        canvas = getattr(self, "tower_progress_chart_canvas", None)
        if canvas is None or not canvas.winfo_exists():
            return

        payload = getattr(self, "tower_progress_chart_payload", None)
        if not isinstance(payload, dict):
            self._render_tower_progress_chart_message("Loading temporal evolution...")
            return

        state = str(payload.get("state", "") or "")
        self.tower_progress_chart_caption_var.set(str(payload.get("caption", "") or ""))
        if state != "ready":
            self._render_tower_progress_chart_message(str(payload.get("message", "No chart data available.")))
            return

        image_data = str(payload.get("image_data", "") or "")
        if not image_data:
            self._render_tower_progress_chart_message("No chart image available.")
            return

        width, height = self._get_tower_progress_chart_size()
        canvas.delete("all")
        self.tower_progress_chart_image = tk.PhotoImage(data=image_data)
        canvas.create_image(width // 2, height // 2, image=self.tower_progress_chart_image, anchor="center")

    TowerProgressPanelMixin._ensure_tower_progress_async_state = _ensure_tower_progress_async_state
    TowerProgressPanelMixin._get_tower_progress_chart_size = _get_tower_progress_chart_size
    TowerProgressPanelMixin._build_tower_progress_tab = _build_tower_progress_tab
    TowerProgressPanelMixin.refresh_tower_progress_tab_visuals = refresh_tower_progress_tab_visuals
    TowerProgressPanelMixin.load_tower_progress_entries = load_tower_progress_entries
    TowerProgressPanelMixin.on_tower_progress_filter_changed = on_tower_progress_filter_changed
    TowerProgressPanelMixin.select_tower_progress_entry = select_tower_progress_entry
    TowerProgressPanelMixin.clear_tower_progress_form = clear_tower_progress_form
    TowerProgressPanelMixin.get_tower_progress_fallback_floors = get_tower_progress_fallback_floors
    TowerProgressPanelMixin.prepare_tower_progress_entry_for_save = prepare_tower_progress_entry_for_save
    TowerProgressPanelMixin.create_tower_progress_entry = create_tower_progress_entry
    TowerProgressPanelMixin.update_tower_progress_entry = update_tower_progress_entry
    TowerProgressPanelMixin.save_tower_progress_entries = save_tower_progress_entries
    TowerProgressPanelMixin._render_tower_progress_chart_message = _render_tower_progress_chart_message
    TowerProgressPanelMixin.on_tower_progress_chart_configure = on_tower_progress_chart_configure
    TowerProgressPanelMixin.request_tower_progress_chart_refresh = request_tower_progress_chart_refresh
    TowerProgressPanelMixin._build_tower_progress_chart_payload_worker = _build_tower_progress_chart_payload_worker
    TowerProgressPanelMixin._poll_tower_progress_chart_refresh = _poll_tower_progress_chart_refresh
    TowerProgressPanelMixin._finish_tower_progress_chart_refresh = _finish_tower_progress_chart_refresh
    TowerProgressPanelMixin.build_tower_progress_chart_payload = build_tower_progress_chart_payload
    TowerProgressPanelMixin.draw_tower_progress_chart = draw_tower_progress_chart


    original_build_packs_tab = PacksPanelMixin._build_packs_tab
    original_render_pack_editor = PacksPanelMixin.render_pack_editor

    def _ensure_lootbox_state(self) -> None:
        if not hasattr(self, "lootbox_name_var"):
            self.lootbox_name_var = tk.StringVar()
        if not hasattr(self, "lootbox_expected_value_var"):
            self.lootbox_expected_value_var = tk.StringVar(value="0")
        if not hasattr(self, "lootbox_total_probability_var"):
            self.lootbox_total_probability_var = tk.StringVar(value="0%")
        if not hasattr(self, "lootbox_probability_note_var"):
            self.lootbox_probability_note_var = tk.StringVar(value="Add lootbox items to calculate the expected value.")
        if not hasattr(self, "lootbox_editor_items") or not isinstance(self.lootbox_editor_items, list):
            self.lootbox_editor_items = []
        if not self.lootbox_editor_items:
            self.lootbox_editor_items = [{"item_name": "", "probability": "", "amount": "1"}]
        for attribute_name in (
            "lootbox_popup",
            "lootbox_shell",
            "lootbox_canvas",
            "lootbox_content",
            "lootbox_window",
        ):
            if not hasattr(self, attribute_name):
                setattr(self, attribute_name, None)
        if not hasattr(self, "lootbox_edit_item_base_index"):
            self.lootbox_edit_item_base_index = None

    def _build_packs_tab(self) -> None:
        original_build_packs_tab(self)
        self._ensure_lootbox_state()

        packs_header = None
        if getattr(self, "packs_list_scene", None) is not None:
            children = self.packs_list_scene.winfo_children()
            if children:
                packs_header = children[0]

        list_actions = None
        if packs_header is not None:
            for child in packs_header.winfo_children():
                if isinstance(child, tk.Frame):
                    buttons = [widget for widget in child.winfo_children() if isinstance(widget, tk.Button)]
                    if len(buttons) >= 2:
                        list_actions = child
                        break

        return

    def render_pack_editor(self) -> None:
        original_render_pack_editor(self)
        self._ensure_lootbox_state()

        header = None
        if getattr(self, "packs_editor_content", None) is not None:
            children = self.packs_editor_content.winfo_children()
            if children:
                header = children[0]

        if header is None or not header.winfo_exists():
            return

        return

    def render_item_base_manager(self) -> None:
        original_render_item_base_manager(self)
        self._ensure_lootbox_state()
        shell = getattr(self, "item_base_manager_shell", None)
        form_frame = getattr(self, "item_base_manager_form", None)
        if shell is None or not shell.winfo_exists() or form_frame is None or not form_frame.winfo_exists():
            return

        header = None
        for child in shell.winfo_children():
            if isinstance(child, tk.Frame) and int(child.grid_info().get("row", -1)) == 0:
                header = child
                break
        if header is not None and header.winfo_exists():
            for child in list(header.winfo_children()):
                if int(child.grid_info().get("column", -1)) == 1:
                    child.destroy()
            header_actions = tk.Frame(header, bg=SURFACE)
            header_actions.grid(row=0, column=1, rowspan=2, sticky="e")
            self._make_button(header_actions, "New Item", self.clear_item_base_form, filled=False).pack(side="left")
            self._make_button(header_actions, "New Lootbox", self.open_new_lootbox_draft, filled=False).pack(side="left", padx=(8, 0))
            self._make_button(header_actions, "Close", self.close_item_base_manager, filled=False).pack(side="left", padx=(8, 0))

        if self.selected_item_base_index is None or not (0 <= self.selected_item_base_index < len(self.item_bases)):
            summary_card = None
            children = form_frame.winfo_children()
            if children:
                summary_card = children[0]
            if summary_card is not None and summary_card.winfo_exists():
                for child in summary_card.winfo_children():
                    if isinstance(child, tk.Frame) and int(child.grid_info().get("row", -1)) == 5:
                        for widget in list(child.winfo_children()):
                            if isinstance(widget, tk.Button) and str(widget.cget("text")) == "New":
                                widget.destroy()
            return

        selected_item_base = self.item_bases[self.selected_item_base_index]
        summary_card = None
        children = form_frame.winfo_children()
        if children:
            summary_card = children[0]
        if summary_card is None or not summary_card.winfo_exists():
            return

        actions = None
        for child in summary_card.winfo_children():
            if isinstance(child, tk.Frame) and int(child.grid_info().get("row", -1)) == 5:
                actions = child
                break
        if actions is not None:
            for widget in list(actions.winfo_children()):
                if isinstance(widget, tk.Button) and str(widget.cget("text")) == "New":
                    widget.destroy()

        if not _is_lootbox_item_base(selected_item_base):
            return

        fields_row = None
        for child in summary_card.winfo_children():
            if isinstance(child, tk.Frame) and int(child.grid_info().get("row", -1)) == 3:
                fields_row = child
                break
        if fields_row is not None:
            for field in fields_row.winfo_children():
                for widget in field.winfo_children():
                    if isinstance(widget, tk.Entry):
                        widget.configure(
                            state="disabled",
                            disabledbackground=SURFACE_MUTED,
                            disabledforeground=TEXT_MUTED,
                        )

        info_label = tk.Label(
            summary_card,
            text="This Item Base is generated from a lootbox definition. Use Edit Lootbox to update its items, amounts, and probabilities.",
            bg=SURFACE_MUTED,
            fg=TEXT_MUTED,
            font=self.body_font,
            justify="left",
            wraplength=420,
        )
        info_label.grid(row=6, column=0, sticky="w", padx=10, pady=(12, 0))

        if actions is None:
            return

        for widget in list(actions.winfo_children()):
            if isinstance(widget, tk.Button) and str(widget.cget("text")) == "Update":
                widget.destroy()

        existing = [str(widget.cget("text")) for widget in actions.winfo_children() if isinstance(widget, tk.Button)]
        if "Edit Lootbox" not in existing:
            self._make_button(actions, "Edit Lootbox", self.edit_selected_lootbox_item_base, filled=True).pack(side="left", padx=(8, 0))

    def clone_lootbox_items(self, items: object) -> list[dict[str, str]]:
        if not isinstance(items, list):
            return []
        cloned: list[dict[str, str]] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            cloned.append(
                {
                    "item_name": str(item.get("item_name", "") or "").strip(),
                    "probability": str(item.get("probability", "") or "").strip(),
                    "item_value": str(item.get("item_value", "") or "").strip(),
                }
            )
        return cloned

    def _lootbox_row_has_content(self, item: dict[str, str]) -> bool:
        return any(str(item.get(field_name, "") or "").strip() for field_name in ("item_name", "probability", "item_value"))

    def calculate_lootbox_line_expected_value(self, item: dict[str, str]) -> float:
        probability = max(0.0, parse_float(item.get("probability", "")))
        item_value = max(0.0, parse_float(item.get("item_value", "")))
        return (probability / 100.0) * item_value

    def calculate_lootbox_expected_value(self, items: list[dict[str, str]]) -> float:
        total = 0.0
        for item in items:
            if not self._lootbox_row_has_content(item):
                continue
            total += self.calculate_lootbox_line_expected_value(item)
        return total

    def calculate_lootbox_probability_total(self, items: list[dict[str, str]]) -> float:
        total = 0.0
        for item in items:
            if not self._lootbox_row_has_content(item):
                continue
            total += max(0.0, parse_float(item.get("probability", "")))
        return total

    def update_lootbox_metrics(self) -> None:
        self._ensure_lootbox_state()
        items = self.clone_lootbox_items(self.lootbox_editor_items)
        expected_value = self.calculate_lootbox_expected_value(items)
        total_probability = self.calculate_lootbox_probability_total(items)
        self.lootbox_expected_value_var.set(format_decimal(expected_value))
        self.lootbox_total_probability_var.set(f"{format_decimal(total_probability)}%")

        if total_probability <= 0:
            note = "Enter probabilities in percent to calculate the expected value."
        elif abs(total_probability - 100.0) < 0.0001:
            note = "Probability total is exactly 100%, so the expected value is fully balanced."
        elif total_probability < 100.0:
            note = f"Probability total is below 100% by {format_decimal(100.0 - total_probability)}%."
        else:
            note = f"Probability total exceeds 100% by {format_decimal(total_probability - 100.0)}%."
        self.lootbox_probability_note_var.set(note)

    def clear_lootbox_form(self, keep_status: bool = False, rerender: bool = True) -> None:
        self._ensure_lootbox_state()
        self.lootbox_edit_item_base_index = None
        self.lootbox_name_var.set("")
        self.lootbox_editor_items = [{"item_name": "", "probability": "", "amount": "1"}]
        self.update_lootbox_metrics()
        if rerender:
            self.render_lootbox_calculator()
        if not keep_status:
            self.status_var.set("Lootbox calculator cleared.")

    def add_lootbox_item(self) -> None:
        self._ensure_lootbox_state()
        self.lootbox_editor_items.append({"item_name": "", "probability": "", "amount": "1"})
        self.update_lootbox_metrics()
        self.render_lootbox_calculator()
        self.status_var.set("Added a new lootbox item row.")

    def remove_lootbox_item(self, index: int) -> None:
        self._ensure_lootbox_state()
        if not (0 <= index < len(self.lootbox_editor_items)):
            return
        if len(self.lootbox_editor_items) == 1:
            self.lootbox_editor_items = [{"item_name": "", "probability": "", "amount": "1"}]
        else:
            self.lootbox_editor_items.pop(index)
        self.update_lootbox_metrics()
        self.render_lootbox_calculator()
        self.status_var.set("Removed the lootbox item row.")

    def open_new_lootbox_draft(self) -> None:
        self.clear_lootbox_form(keep_status=True, rerender=False)
        self.open_lootbox_calculator()
        self.status_var.set("Creating a new lootbox.")

    def edit_selected_lootbox_item_base(self) -> None:
        self._ensure_lootbox_state()
        index = self.selected_item_base_index
        if index is None or not (0 <= index < len(self.item_bases)):
            messagebox.showwarning("No selection", "Select a lootbox item base first.")
            return
        item_base = self.item_bases[index]
        if not _is_lootbox_item_base(item_base):
            messagebox.showwarning("Not a lootbox", "The selected item base is not backed by a lootbox definition.")
            return

        lootbox_rows = self.clone_lootbox_items(item_base.get("lootbox_items", []))
        self.lootbox_edit_item_base_index = index
        self.lootbox_name_var.set(str(item_base.get("item_name", "") or ""))
        self.lootbox_editor_items = lootbox_rows or [{"item_name": "", "probability": "", "amount": "1"}]
        self.update_lootbox_metrics()
        self.open_lootbox_calculator()
        self.status_var.set(f"Editing lootbox item base: {item_base.get('item_name', '(no name)')}")
    def open_lootbox_calculator(self) -> None:
        self._ensure_lootbox_state()
        popup = getattr(self, "lootbox_popup", None)
        if popup is not None and popup.winfo_exists():
            popup.deiconify()
            popup.lift()
            popup.focus_force()
            self.render_lootbox_calculator()
            return

        popup = tk.Toplevel(self)
        popup.title("Lootbox Value Calculator")
        popup.configure(bg=SURFACE)
        popup.geometry("1180x760")
        popup.minsize(920, 640)
        popup.transient(self)
        popup.protocol("WM_DELETE_WINDOW", self.close_lootbox_calculator)
        self.lootbox_popup = popup

        shell = self._make_panel(popup)
        shell.pack(fill="both", expand=True, padx=20, pady=20)
        shell.columnconfigure(0, weight=1)
        shell.rowconfigure(0, weight=1)
        self.lootbox_shell = shell

        self.lootbox_canvas = tk.Canvas(shell, bg=SURFACE, highlightthickness=0, bd=0)
        self.lootbox_canvas.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(shell, orient="vertical", command=self.lootbox_canvas.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        self.lootbox_canvas.configure(yscrollcommand=scroll.set)

        self.lootbox_content = tk.Frame(self.lootbox_canvas, bg=SURFACE)
        self.lootbox_window = self.lootbox_canvas.create_window((0, 0), window=self.lootbox_content, anchor="nw")
        self.lootbox_content.bind(
            "<Configure>",
            lambda _event: self.lootbox_canvas.configure(scrollregion=self.lootbox_canvas.bbox("all")),
        )
        self.lootbox_canvas.bind(
            "<Configure>",
            lambda event: self.lootbox_canvas.itemconfigure(self.lootbox_window, width=event.width),
        )
        self._bind_mousewheel(self.lootbox_canvas, self.lootbox_content)

        self.render_lootbox_calculator()

    def close_lootbox_calculator(self) -> None:
        popup = getattr(self, "lootbox_popup", None)
        if popup is not None and popup.winfo_exists():
            popup.destroy()
        self.lootbox_popup = None
        self.lootbox_shell = None
        self.lootbox_canvas = None
        self.lootbox_content = None
        self.lootbox_window = None

    def render_lootbox_calculator(self) -> None:
        self._ensure_lootbox_state()
        self.update_lootbox_metrics()
        popup = getattr(self, "lootbox_popup", None)
        content = getattr(self, "lootbox_content", None)
        if popup is None or not popup.winfo_exists() or content is None or not content.winfo_exists():
            return

        for child in content.winfo_children():
            child.destroy()

        content.configure(padx=20, pady=20)
        content.columnconfigure(0, weight=1)

        header = tk.Frame(content, bg=SURFACE)
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)
        tk.Label(header, text="Lootbox Value Calculator", bg=SURFACE, fg=TEXT, font=self.section_font).grid(row=0, column=0, sticky="w")
        tk.Label(
            header,
            text="Expected value = sum of each item value multiplied by its drop probability. Save the result as an item base when you want to reuse that lootbox inside Packs Value.",
            bg=SURFACE,
            fg=TEXT_MUTED,
            font=self.body_font,
            justify="left",
            wraplength=860,
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))
        self._make_button(header, "Close", self.close_lootbox_calculator, filled=False).grid(row=0, column=1, rowspan=2, sticky="e")

        summary_card = tk.Frame(
            content,
            bg=SURFACE_MUTED,
            highlightthickness=1,
            highlightbackground=BORDER,
            bd=0,
            padx=18,
            pady=18,
        )
        summary_card.grid(row=1, column=0, sticky="ew", pady=(16, 12))
        summary_card.columnconfigure(0, weight=1)
        summary_card.columnconfigure(1, weight=1)
        tk.Label(summary_card, text="Lootbox Details", bg=SURFACE_MUTED, fg=TEXT, font=self.section_font).grid(row=0, column=0, columnspan=2, sticky="w")
        self._make_input(summary_card, "Lootbox Name", self.lootbox_name_var, 1, 0, columnspan=2)
        tk.Label(
            summary_card,
            text="Use the item value directly for each drop. Probabilities are percentages and do not need to be whole numbers.",
            bg=SURFACE_MUTED,
            fg=TEXT_MUTED,
            font=self.body_font,
            justify="left",
            wraplength=900,
        ).grid(row=2, column=0, columnspan=2, sticky="w", padx=10, pady=(6, 0))

        metrics = tk.Frame(summary_card, bg=SURFACE_MUTED)
        metrics.grid(row=3, column=0, columnspan=2, sticky="ew", padx=10, pady=(14, 0))
        for column in range(2):
            metrics.columnconfigure(column, weight=1)
        self._create_metric_tile(metrics, "Expected Value", self.lootbox_expected_value_var, 0)
        self._create_metric_tile(metrics, "Total Probability", self.lootbox_total_probability_var, 1)

        tk.Label(
            summary_card,
            textvariable=self.lootbox_probability_note_var,
            bg=SURFACE_MUTED,
            fg=TEXT_MUTED,
            font=self.body_font,
            justify="left",
            wraplength=900,
        ).grid(row=4, column=0, columnspan=2, sticky="w", padx=10, pady=(12, 0))

        actions = tk.Frame(summary_card, bg=SURFACE_MUTED)
        actions.grid(row=5, column=0, columnspan=2, sticky="e", padx=10, pady=(14, 0))
        self._make_button(actions, "New", self.clear_lootbox_form, filled=False).pack(side="left")
        self._make_button(actions, "Add Item", self.add_lootbox_item, filled=False).pack(side="left", padx=(8, 0))
        self._make_button(actions, "Save as Item Base", self.save_lootbox_as_item_base, filled=True).pack(side="left", padx=(8, 0))

        items_card = tk.Frame(
            content,
            bg=SURFACE,
            highlightthickness=1,
            highlightbackground=BORDER,
            bd=0,
            padx=18,
            pady=18,
        )
        items_card.grid(row=2, column=0, sticky="ew")
        items_card.columnconfigure(0, weight=1)
        tk.Label(items_card, text="Lootbox Items", bg=SURFACE, fg=TEXT, font=self.section_font).grid(row=0, column=0, sticky="w")
        tk.Label(
            items_card,
            text="Add one row per possible drop. Expected contribution is calculated as probability x item value.",
            bg=SURFACE,
            fg=TEXT_MUTED,
            font=self.body_font,
            justify="left",
            wraplength=900,
        ).grid(row=1, column=0, sticky="w", pady=(4, 12))

        for index, item in enumerate(self.lootbox_editor_items):
            self._create_lootbox_item_row(items_card, index, item, 2 + index)

        self._bind_mousewheel_deep(self.lootbox_canvas, self.lootbox_content)

    def _create_lootbox_item_row(self, parent: tk.Misc, index: int, item: dict[str, str], row: int) -> None:
        bg = SURFACE_MUTED if index % 2 == 0 else SURFACE
        line = tk.Frame(parent, bg=bg, highlightthickness=1, highlightbackground=BORDER, bd=0, padx=14, pady=12)
        line.grid(row=row, column=0, sticky="ew", pady=(0, 8))
        line.columnconfigure(0, weight=2)
        line.columnconfigure(1, weight=1)
        line.columnconfigure(2, weight=1)
        line.columnconfigure(3, weight=0)
        line.columnconfigure(4, weight=0)

        item_name_var = tk.StringVar(value=str(item.get("item_name", "") or "").strip())
        probability_var = tk.StringVar(value=str(item.get("probability", "") or "").strip())
        item_value_var = tk.StringVar(value=str(item.get("item_value", "") or "").strip())
        contribution_var = tk.StringVar(value=format_decimal(self.calculate_lootbox_line_expected_value(item)))

        def sync_row(*_args: object) -> None:
            if not (0 <= index < len(self.lootbox_editor_items)):
                return
            updated_item = {
                "item_name": item_name_var.get().strip(),
                "probability": probability_var.get().strip(),
                "item_value": item_value_var.get().strip(),
            }
            self.lootbox_editor_items[index] = updated_item
            contribution_var.set(format_decimal(self.calculate_lootbox_line_expected_value(updated_item)))
            self.update_lootbox_metrics()

        for variable in (item_name_var, probability_var, item_value_var):
            variable.trace_add("write", sync_row)

        name_field = tk.Frame(line, bg=bg)
        name_field.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        name_field.columnconfigure(0, weight=1)
        tk.Label(name_field, text="Item Name", bg=bg, fg=TEXT_MUTED, font=self.label_font).grid(row=0, column=0, sticky="w")
        tk.Entry(name_field, textvariable=item_name_var, bg=SURFACE, fg=TEXT, relief="flat", bd=0, insertbackground=TEXT, highlightthickness=1, highlightbackground=BORDER, highlightcolor=PRIMARY, font=self.body_font).grid(row=1, column=0, sticky="ew", pady=(6, 0), ipady=8)

        probability_field = tk.Frame(line, bg=bg)
        probability_field.grid(row=0, column=1, sticky="ew", padx=(0, 8))
        probability_field.columnconfigure(0, weight=1)
        tk.Label(probability_field, text="Probability (%)", bg=bg, fg=TEXT_MUTED, font=self.label_font).grid(row=0, column=0, sticky="w")
        tk.Entry(probability_field, textvariable=probability_var, bg=SURFACE, fg=TEXT, relief="flat", bd=0, insertbackground=TEXT, highlightthickness=1, highlightbackground=BORDER, highlightcolor=PRIMARY, font=self.body_font).grid(row=1, column=0, sticky="ew", pady=(6, 0), ipady=8)

        value_field = tk.Frame(line, bg=bg)
        value_field.grid(row=0, column=2, sticky="ew", padx=(0, 8))
        value_field.columnconfigure(0, weight=1)
        tk.Label(value_field, text="Item Value", bg=bg, fg=TEXT_MUTED, font=self.label_font).grid(row=0, column=0, sticky="w")
        tk.Entry(value_field, textvariable=item_value_var, bg=SURFACE, fg=TEXT, relief="flat", bd=0, insertbackground=TEXT, highlightthickness=1, highlightbackground=BORDER, highlightcolor=PRIMARY, font=self.body_font).grid(row=1, column=0, sticky="ew", pady=(6, 0), ipady=8)

        contribution = tk.Frame(line, bg=bg)
        contribution.grid(row=0, column=3, sticky="e", padx=(0, 8))
        tk.Label(contribution, text="Expected", bg=bg, fg=TEXT_MUTED, font=self.label_font).pack(anchor="e")
        tk.Label(contribution, textvariable=contribution_var, bg=bg, fg=PRIMARY_DARK, font=self.card_title_font).pack(anchor="e", pady=(6, 0))

        self._make_button(line, "Remove", lambda idx=index: self.remove_lootbox_item(idx), filled=False).grid(row=0, column=4, sticky="e", pady=(18, 0))

    def save_lootbox_as_item_base(self) -> None:
        self._ensure_lootbox_state()
        lootbox_name = self.lootbox_name_var.get().strip()
        editing_index = self.lootbox_edit_item_base_index
        if not lootbox_name:
            messagebox.showwarning("Missing name", "Enter a lootbox name before saving it as an item base.")
            return

        normalized_rows = []
        for position, item in enumerate(self.clone_lootbox_items(self.lootbox_editor_items), start=1):
            if not self._lootbox_row_has_content(item):
                continue
            display_name = item.get("item_name", "") or f"Item {position}"
            probability = parse_float(item.get("probability", ""))
            item_value = parse_float(item.get("item_value", ""))
            if probability <= 0:
                messagebox.showerror("Invalid probability", f"Probability for '{display_name}' must be greater than zero.")
                self.status_var.set("Unable to save lootbox as item base.")
                return
            if item_value < 0:
                messagebox.showerror("Invalid item value", f"Item value for '{display_name}' cannot be negative.")
                self.status_var.set("Unable to save lootbox as item base.")
                return
            normalized_rows.append(
                {
                    "item_name": display_name,
                    "probability": format_decimal(probability),
                    "item_value": format_decimal(item_value),
                }
            )

        if not normalized_rows:
            messagebox.showwarning("No lootbox items", "Add at least one lootbox item before saving it as an item base.")
            return

        existing_item_base = self.find_item_base(lootbox_name)
        if existing_item_base is not None and (
            editing_index is None
            or not (0 <= editing_index < len(self.item_bases))
            or self.item_bases[editing_index] is not existing_item_base
        ):
            messagebox.showerror("Duplicate item base", "A catalog item with that name already exists.")
            self.status_var.set("Unable to save lootbox as item base.")
            return

        expected_value = self.calculate_lootbox_expected_value(normalized_rows)
        if expected_value <= 0:
            messagebox.showerror("Invalid expected value", "Expected value must be greater than zero before saving it as an item base.")
            self.status_var.set("Unable to save lootbox as item base.")
            return

        total_probability = self.calculate_lootbox_probability_total(normalized_rows)
        if abs(total_probability - 100.0) >= 0.0001:
            proceed = messagebox.askyesno(
                "Probability total is not 100%",
                f"The current probability total is {format_decimal(total_probability)}%. Save this expected value anyway?",
            )
            if not proceed:
                self.status_var.set("Save cancelled for lootbox item base.")
                return

        previous_item_bases = self.clone_item_bases_state()
        item_base = {
            "item_name": lootbox_name,
            "item_priority": "1",
            "item_base_value": format_decimal(expected_value),
            "item_value": format_decimal(expected_value),
        }

        try:
            self.item_bases.append(item_base)
            self.sort_item_bases()
            self.save_pack_data()
        except Exception as exc:
            self.item_bases = previous_item_bases
            messagebox.showerror("Save failed", str(exc))
            self.status_var.set("Unable to save lootbox as item base.")
            return

        new_index = next(
            (
                item_index
                for item_index, entry in enumerate(self.item_bases)
                if normalize_item_name(entry.get("item_name", "")) == normalize_item_name(lootbox_name)
            ),
            None,
        )
        if new_index is not None:
            self.select_item_base(new_index)
        self.status_var.set(f"Saved lootbox expected value as item base: {lootbox_name}")

    original_load_pack_data = PacksPanelMixin.load_pack_data
    original_save_pack_data = PacksPanelMixin.save_pack_data
    original_render_item_base_manager = PacksPanelMixin.render_item_base_manager
    original_rename_item_base_references = PacksPanelMixin.rename_item_base_references
    original_get_item_base_usage = PacksPanelMixin.get_item_base_usage
    original_clone_item_bases_state = PacksPanelMixin.clone_item_bases_state
    original_prepare_item_base_for_save = PacksPanelMixin.prepare_item_base_for_save
    original_update_item_base_preview_value = PacksPanelMixin.update_item_base_preview_value
    original_pack_repository_load = PackRepository.load
    original_pack_repository_save = PackRepository.save

    def _normalize_lootbox_rows(items: object) -> list[dict[str, str]]:
        normalized_rows: list[dict[str, str]] = []
        if not isinstance(items, list):
            return normalized_rows
        for item in items:
            if not isinstance(item, dict):
                continue
            normalized_rows.append(
                {
                    "item_name": str(item.get("item_name", "") or "").strip(),
                    "probability": str(item.get("probability", "") or "").strip(),
                    "amount": str(item.get("amount", "") or "").strip() or "1",
                }
            )
        return normalized_rows

    def _is_lootbox_item_base(entry: dict[str, str]) -> bool:
        return str(entry.get("item_source", "") or "").strip() == "lootbox"

    def load(self) -> tuple[list[dict[str, str]], list[dict[str, object]]]:
        self.ensure_file()
        with self.json_path.open("r", encoding="utf-8-sig") as json_file:
            payload = json.load(json_file)

        if not isinstance(payload, dict):
            return [], []

        raw_item_bases = payload.get("item_bases", [])
        raw_packs = payload.get("packs", [])

        item_bases: list[dict[str, str]] = []
        if isinstance(raw_item_bases, list):
            for entry in raw_item_bases:
                if not isinstance(entry, dict):
                    continue
                normalized = {
                    "item_name": str(entry.get("item_name", "") or "").strip(),
                    "item_priority": str(entry.get("item_priority", "") or "").strip(),
                    "item_base_value": str(entry.get("item_base_value", "") or "").strip(),
                    "item_value": str(entry.get("item_value", "") or "").strip(),
                }
                if str(entry.get("item_source", "") or "").strip() == "lootbox":
                    normalized["item_source"] = "lootbox"
                    normalized["lootbox_items"] = _normalize_lootbox_rows(entry.get("lootbox_items", []))
                if any(str(value or "").strip() for key, value in normalized.items() if key != "lootbox_items") or normalized.get("lootbox_items"):
                    item_bases.append(normalized)

        packs: list[dict[str, object]] = []
        if isinstance(raw_packs, list):
            for entry in raw_packs:
                if not isinstance(entry, dict):
                    continue
                items: list[dict[str, str]] = []
                raw_items = entry.get("items", [])
                if isinstance(raw_items, list):
                    for item in raw_items:
                        if not isinstance(item, dict):
                            continue
                        normalized_item = {
                            "item_name": str(item.get("item_name", "") or "").strip(),
                            "amount": str(item.get("amount", "") or "").strip(),
                        }
                        if any(normalized_item.values()):
                            items.append(normalized_item)
                packs.append(
                    {
                        "pack_name": str(entry.get("pack_name", "") or "").strip(),
                        "price_brl": str(entry.get("price_brl", "") or "").strip(),
                        "items": items,
                    }
                )

        return item_bases, packs

    def save(
        self,
        item_bases: list[dict[str, str]],
        packs: list[dict[str, object]],
    ) -> None:
        self.json_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "item_bases": [],
            "packs": [],
        }

        for entry in item_bases:
            normalized_entry: dict[str, object] = {
                "item_name": str(entry.get("item_name", "") or "").strip(),
                "item_priority": str(entry.get("item_priority", "") or "").strip(),
                "item_base_value": str(entry.get("item_base_value", "") or "").strip(),
                "item_value": str(entry.get("item_value", "") or "").strip(),
            }
            if _is_lootbox_item_base(entry):
                normalized_entry["item_source"] = "lootbox"
                normalized_entry["lootbox_items"] = _normalize_lootbox_rows(entry.get("lootbox_items", []))
            payload["item_bases"].append(normalized_entry)

        for entry in packs:
            raw_items = entry.get("items", [])
            payload["packs"].append(
                {
                    "pack_name": str(entry.get("pack_name", "") or "").strip(),
                    "price_brl": str(entry.get("price_brl", "") or "").strip(),
                    "items": [
                        {
                            "item_name": str(item.get("item_name", "") or "").strip(),
                            "amount": str(item.get("amount", "") or "").strip(),
                        }
                        for item in raw_items
                        if isinstance(item, dict)
                    ],
                }
            )

        with self.json_path.open("w", encoding="utf-8") as json_file:
            json.dump(payload, json_file, indent=2)

    def clone_lootbox_items(self, items: object) -> list[dict[str, str]]:
        if not isinstance(items, list):
            return []
        cloned: list[dict[str, str]] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            cloned.append(
                {
                    "item_name": str(item.get("item_name", "") or "").strip(),
                    "probability": str(item.get("probability", "") or "").strip(),
                    "amount": str(item.get("amount", "") or "").strip(),
                }
            )
        return cloned

    def _lootbox_row_has_content(self, item: dict[str, str]) -> bool:
        return any(str(item.get(field_name, "") or "").strip() for field_name in ("item_name", "probability", "amount"))

    def get_lootbox_item_base_value(self, item_name: str) -> float:
        target_key = normalize_item_name(item_name)
        selected_index = getattr(self, "selected_item_base_index", None)
        if (
            target_key
            and selected_index is not None
            and 0 <= selected_index < len(self.item_bases)
        ):
            selected_item_base = self.item_bases[selected_index]
            selected_key = normalize_item_name(selected_item_base.get("item_name", ""))
            draft_key = normalize_item_name(self.item_base_name_var.get().strip())
            if target_key == selected_key or (draft_key and target_key == draft_key):
                return parse_float(self.item_base_priority_var.get()) * parse_float(self.item_base_value_var.get())

        item_base = self.find_item_base(item_name)
        if item_base is None:
            return 0.0
        return self.calculate_item_base_value(item_base)

    def calculate_item_base_value(self, item_base: dict[str, str], trail: set[str] | None = None) -> float:
        item_name = str(item_base.get("item_name", "") or "").strip()
        target_key = normalize_item_name(item_name)
        if not target_key:
            return 0.0

        if trail is None:
            trail = set()
        if target_key in trail:
            return 0.0

        if _is_lootbox_item_base(item_base):
            next_trail = set(trail)
            next_trail.add(target_key)
            total = 0.0
            for lootbox_item in self.clone_lootbox_items(item_base.get("lootbox_items", [])):
                if not self._lootbox_row_has_content(lootbox_item):
                    continue
                probability = max(0.0, parse_float(lootbox_item.get("probability", "")))
                amount = max(0.0, parse_float(lootbox_item.get("amount", "")))
                referenced_item = self.find_item_base(str(lootbox_item.get("item_name", "") or "").strip())
                if referenced_item is None:
                    continue
                total += (probability / 100.0) * amount * self.calculate_item_base_value(referenced_item, next_trail)
            return total

        selected_index = getattr(self, "selected_item_base_index", None)
        if (
            selected_index is not None
            and 0 <= selected_index < len(self.item_bases)
            and target_key == normalize_item_name(self.item_bases[selected_index].get("item_name", ""))
            and not _is_lootbox_item_base(self.item_bases[selected_index])
        ):
            return parse_float(self.item_base_priority_var.get()) * parse_float(self.item_base_value_var.get())

        return parse_float(item_base.get("item_priority", "")) * parse_float(item_base.get("item_base_value", ""))

    def recalculate_stored_lootbox_item_bases(self) -> bool:
        changed = False
        for entry in self.item_bases:
            if not _is_lootbox_item_base(entry):
                continue
            lootbox_rows = self.clone_lootbox_items(entry.get("lootbox_items", []))
            expected_value = self.calculate_lootbox_expected_value(lootbox_rows)
            expected_text = format_decimal(expected_value)
            if str(entry.get("item_priority", "") or "").strip() != "1":
                entry["item_priority"] = "1"
                changed = True
            if str(entry.get("item_base_value", "") or "").strip() != expected_text:
                entry["item_base_value"] = expected_text
                changed = True
            if str(entry.get("item_value", "") or "").strip() != expected_text:
                entry["item_value"] = expected_text
                changed = True
            if entry.get("lootbox_items") != lootbox_rows:
                entry["lootbox_items"] = lootbox_rows
                changed = True
        return changed

    def update_item_base_preview_value(self) -> None:
        original_update_item_base_preview_value(self)
        self.update_lootbox_metrics()
        popup = getattr(self, "lootbox_popup", None)
        if popup is not None and popup.winfo_exists():
            self.render_lootbox_calculator()

    def calculate_lootbox_line_expected_value(self, item: dict[str, str]) -> float:
        probability = max(0.0, parse_float(item.get("probability", "")))
        amount = max(0.0, parse_float(item.get("amount", "")))
        item_value = self.get_lootbox_item_base_value(str(item.get("item_name", "") or "").strip())
        return (probability / 100.0) * item_value * amount

    def calculate_lootbox_expected_value(self, items: list[dict[str, str]]) -> float:
        total = 0.0
        for item in items:
            if not self._lootbox_row_has_content(item):
                continue
            total += self.calculate_lootbox_line_expected_value(item)
        return total

    def calculate_lootbox_probability_total(self, items: list[dict[str, str]]) -> float:
        total = 0.0
        for item in items:
            if not self._lootbox_row_has_content(item):
                continue
            total += max(0.0, parse_float(item.get("probability", "")))
        return total

    def update_lootbox_metrics(self) -> None:
        self._ensure_lootbox_state()
        items = self.clone_lootbox_items(self.lootbox_editor_items)
        expected_value = self.calculate_lootbox_expected_value(items)
        total_probability = self.calculate_lootbox_probability_total(items)
        self.lootbox_expected_value_var.set(format_decimal(expected_value))
        self.lootbox_total_probability_var.set(f"{format_decimal(total_probability)}%")

        if not self.item_bases:
            note = "Create Item Base entries first, then build the lootbox from that shared catalog."
        elif total_probability <= 0:
            note = "Select Item Base entries, set amounts, and enter probabilities in percent to calculate the expected value."
        elif abs(total_probability - 100.0) < 0.0001:
            note = "Probability total is exactly 100%, so the expected value is fully balanced."
        elif total_probability < 100.0:
            note = f"Probability total is below 100% by {format_decimal(100.0 - total_probability)}%."
        else:
            note = f"Probability total exceeds 100% by {format_decimal(total_probability - 100.0)}%."
        self.lootbox_probability_note_var.set(note)

    def render_lootbox_calculator(self) -> None:
        self._ensure_lootbox_state()
        self.update_lootbox_metrics()
        popup = getattr(self, "lootbox_popup", None)
        content = getattr(self, "lootbox_content", None)
        if popup is None or not popup.winfo_exists() or content is None or not content.winfo_exists():
            return

        for child in content.winfo_children():
            child.destroy()

        content.configure(padx=20, pady=20)
        content.columnconfigure(0, weight=1)

        header = tk.Frame(content, bg=SURFACE)
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)
        tk.Label(header, text="Lootbox Value Calculator", bg=SURFACE, fg=TEXT, font=self.section_font).grid(row=0, column=0, sticky="w")
        editing_lootbox = (
            self.lootbox_edit_item_base_index is not None
            and 0 <= self.lootbox_edit_item_base_index < len(self.item_bases)
        )

        tk.Label(
            header,
            text=(
                "Update the selected lootbox-backed Item Base from here."
                if editing_lootbox
                else "Each lootbox row now points to an Item Base entry and an amount. The expected value updates automatically when that Item Base value changes."
            ),
            bg=SURFACE,
            fg=TEXT_MUTED,
            font=self.body_font,
            justify="left",
            wraplength=860,
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))
        self._make_button(header, "Close", self.close_lootbox_calculator, filled=False).grid(row=0, column=1, rowspan=2, sticky="e")

        summary_card = tk.Frame(
            content,
            bg=SURFACE_MUTED,
            highlightthickness=1,
            highlightbackground=BORDER,
            bd=0,
            padx=18,
            pady=18,
        )
        summary_card.grid(row=1, column=0, sticky="ew", pady=(16, 12))
        summary_card.columnconfigure(0, weight=1)
        summary_card.columnconfigure(1, weight=1)
        tk.Label(summary_card, text="Lootbox Details", bg=SURFACE_MUTED, fg=TEXT, font=self.section_font).grid(row=0, column=0, columnspan=2, sticky="w")
        self._make_input(summary_card, "Lootbox Name", self.lootbox_name_var, 1, 0, columnspan=2)
        tk.Label(
            summary_card,
            text="Pick items from the shared Item Base catalog, set the amount dropped for each one, and the calculator will use the current catalog values automatically.",
            bg=SURFACE_MUTED,
            fg=TEXT_MUTED,
            font=self.body_font,
            justify="left",
            wraplength=900,
        ).grid(row=2, column=0, columnspan=2, sticky="w", padx=10, pady=(6, 0))

        metrics = tk.Frame(summary_card, bg=SURFACE_MUTED)
        metrics.grid(row=3, column=0, columnspan=2, sticky="ew", padx=10, pady=(14, 0))
        for column in range(2):
            metrics.columnconfigure(column, weight=1)
        self._create_metric_tile(metrics, "Expected Value", self.lootbox_expected_value_var, 0)
        self._create_metric_tile(metrics, "Total Probability", self.lootbox_total_probability_var, 1)

        tk.Label(
            summary_card,
            textvariable=self.lootbox_probability_note_var,
            bg=SURFACE_MUTED,
            fg=TEXT_MUTED,
            font=self.body_font,
            justify="left",
            wraplength=900,
        ).grid(row=4, column=0, columnspan=2, sticky="w", padx=10, pady=(12, 0))

        actions = tk.Frame(summary_card, bg=SURFACE_MUTED)
        actions.grid(row=5, column=0, columnspan=2, sticky="e", padx=10, pady=(14, 0))
        self._make_button(actions, "New", self.clear_lootbox_form, filled=False).pack(side="left")
        self._make_button(actions, "Add Item", self.add_lootbox_item, filled=False).pack(side="left", padx=(8, 0))
        self._make_button(
            actions,
            "Update Lootbox" if editing_lootbox else "Save as Item Base",
            self.save_lootbox_as_item_base,
            filled=True,
        ).pack(side="left", padx=(8, 0))

        items_card = tk.Frame(
            content,
            bg=SURFACE,
            highlightthickness=1,
            highlightbackground=BORDER,
            bd=0,
            padx=18,
            pady=18,
        )
        items_card.grid(row=2, column=0, sticky="ew")
        items_card.columnconfigure(0, weight=1)
        tk.Label(items_card, text="Lootbox Items", bg=SURFACE, fg=TEXT, font=self.section_font).grid(row=0, column=0, sticky="w")
        tk.Label(
            items_card,
            text="Every row uses the current Item Base value and its drop amount. If you edit an Item Base later, the lootbox expected value recalculates automatically.",
            bg=SURFACE,
            fg=TEXT_MUTED,
            font=self.body_font,
            justify="left",
            wraplength=900,
        ).grid(row=1, column=0, sticky="w", pady=(4, 12))

        for index, item in enumerate(self.lootbox_editor_items):
            self._create_lootbox_item_row(items_card, index, item, 2 + index)

        self._bind_mousewheel_deep(self.lootbox_canvas, self.lootbox_content)

    def _create_lootbox_item_row(self, parent: tk.Misc, index: int, item: dict[str, str], row: int) -> None:
        bg = SURFACE_MUTED if index % 2 == 0 else SURFACE
        line = tk.Frame(parent, bg=bg, highlightthickness=1, highlightbackground=BORDER, bd=0, padx=14, pady=12)
        line.grid(row=row, column=0, sticky="ew", pady=(0, 8))
        line.columnconfigure(0, weight=2)
        line.columnconfigure(1, weight=1)
        line.columnconfigure(2, weight=1)
        line.columnconfigure(3, weight=1)
        line.columnconfigure(4, weight=1)
        line.columnconfigure(5, weight=0)

        item_name_var = tk.StringVar(value=str(item.get("item_name", "") or "").strip())
        probability_var = tk.StringVar(value=str(item.get("probability", "") or "").strip())
        amount_var = tk.StringVar(value=str(item.get("amount", "") or "").strip() or "1")
        item_value_var = tk.StringVar(value="0")
        contribution_var = tk.StringVar(value=format_decimal(self.calculate_lootbox_line_expected_value(item)))
        item_base_names = [str(entry.get("item_name", "") or "").strip() for entry in self.item_bases if str(entry.get("item_name", "") or "").strip()]

        def sync_row(*_args: object) -> None:
            if not (0 <= index < len(self.lootbox_editor_items)):
                return
            updated_item = {
                "item_name": item_name_var.get().strip(),
                "probability": probability_var.get().strip(),
                "amount": amount_var.get().strip(),
            }
            self.lootbox_editor_items[index] = updated_item
            live_value = self.get_lootbox_item_base_value(updated_item.get("item_name", ""))
            item_value_var.set(format_decimal(live_value))
            contribution_var.set(format_decimal(self.calculate_lootbox_line_expected_value(updated_item)))
            self.update_lootbox_metrics()

        for variable in (item_name_var, probability_var, amount_var):
            variable.trace_add("write", sync_row)

        name_field = tk.Frame(line, bg=bg)
        name_field.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        name_field.columnconfigure(0, weight=1)
        tk.Label(name_field, text="Item Base", bg=bg, fg=TEXT_MUTED, font=self.label_font).grid(row=0, column=0, sticky="w")
        item_picker = ttk.Combobox(
            name_field,
            textvariable=item_name_var,
            values=item_base_names,
            state="readonly" if item_base_names else "disabled",
            font=self.body_font,
        )
        item_picker.grid(row=1, column=0, sticky="ew", pady=(6, 0), ipady=5)

        probability_field = tk.Frame(line, bg=bg)
        probability_field.grid(row=0, column=1, sticky="ew", padx=(0, 8))
        probability_field.columnconfigure(0, weight=1)
        tk.Label(probability_field, text="Probability (%)", bg=bg, fg=TEXT_MUTED, font=self.label_font).grid(row=0, column=0, sticky="w")
        tk.Entry(probability_field, textvariable=probability_var, bg=SURFACE, fg=TEXT, relief="flat", bd=0, insertbackground=TEXT, highlightthickness=1, highlightbackground=BORDER, highlightcolor=PRIMARY, font=self.body_font).grid(row=1, column=0, sticky="ew", pady=(6, 0), ipady=8)

        amount_field = tk.Frame(line, bg=bg)
        amount_field.grid(row=0, column=2, sticky="ew", padx=(0, 8))
        amount_field.columnconfigure(0, weight=1)
        tk.Label(amount_field, text="Amount", bg=bg, fg=TEXT_MUTED, font=self.label_font).grid(row=0, column=0, sticky="w")
        tk.Entry(amount_field, textvariable=amount_var, bg=SURFACE, fg=TEXT, relief="flat", bd=0, insertbackground=TEXT, highlightthickness=1, highlightbackground=BORDER, highlightcolor=PRIMARY, font=self.body_font).grid(row=1, column=0, sticky="ew", pady=(6, 0), ipady=8)

        value_field = tk.Frame(line, bg=bg)
        value_field.grid(row=0, column=3, sticky="ew", padx=(0, 8))
        tk.Label(value_field, text="Item Base Value", bg=bg, fg=TEXT_MUTED, font=self.label_font).pack(anchor="w")
        tk.Label(value_field, textvariable=item_value_var, bg=bg, fg=PRIMARY_DARK, font=self.card_title_font, anchor="w").pack(anchor="w", pady=(10, 0))

        contribution = tk.Frame(line, bg=bg)
        contribution.grid(row=0, column=4, sticky="ew", padx=(0, 8))
        tk.Label(contribution, text="Expected", bg=bg, fg=TEXT_MUTED, font=self.label_font).pack(anchor="w")
        tk.Label(contribution, textvariable=contribution_var, bg=bg, fg=PRIMARY_DARK, font=self.card_title_font, anchor="w").pack(anchor="w", pady=(10, 0))

        if not item_base_names:
            helper_text = "Create Item Base entries before adding lootbox rows."
            helper_color = TEXT_MUTED
        elif item_name_var.get().strip() and self.find_item_base(item_name_var.get().strip()) is None:
            helper_text = "This Item Base no longer exists. Pick another catalog item."
            helper_color = DANGER
        else:
            helper_text = ""
            helper_color = TEXT_MUTED
        tk.Label(line, text=helper_text, bg=bg, fg=helper_color, font=self.card_meta_font, anchor="w", justify="left").grid(row=1, column=0, columnspan=5, sticky="w", pady=(8, 0))

        self._make_button(line, "Remove", lambda idx=index: self.remove_lootbox_item(idx), filled=False).grid(row=0, column=5, sticky="e", pady=(18, 0))
        sync_row()

    def save_lootbox_as_item_base(self) -> None:
        self._ensure_lootbox_state()
        lootbox_name = self.lootbox_name_var.get().strip()
        editing_index = self.lootbox_edit_item_base_index
        if not lootbox_name:
            messagebox.showwarning("Missing name", "Enter a lootbox name before saving it as an item base.")
            return

        normalized_rows = []
        for position, item in enumerate(self.clone_lootbox_items(self.lootbox_editor_items), start=1):
            if not self._lootbox_row_has_content(item):
                continue
            item_name = str(item.get("item_name", "") or "").strip()
            probability = parse_float(item.get("probability", ""))
            amount = parse_float(item.get("amount", ""))
            if not item_name:
                messagebox.showerror("Missing item", f"Select an Item Base for lootbox row {position}.")
                self.status_var.set("Unable to save lootbox as item base.")
                return
            item_base = self.find_item_base(item_name)
            if item_base is None:
                messagebox.showerror("Missing item base", f"Item Base '{item_name}' no longer exists.")
                self.status_var.set("Unable to save lootbox as item base.")
                return
            if probability <= 0:
                messagebox.showerror("Invalid probability", f"Probability for '{item_name}' must be greater than zero.")
                self.status_var.set("Unable to save lootbox as item base.")
                return
            if amount <= 0:
                messagebox.showerror("Invalid amount", f"Amount for '{item_name}' must be greater than zero.")
                self.status_var.set("Unable to save lootbox as item base.")
                return
            normalized_rows.append(
                {
                    "item_name": item_base.get("item_name", item_name),
                    "probability": format_decimal(probability),
                    "amount": format_decimal(amount),
                }
            )

        if not normalized_rows:
            messagebox.showwarning("No lootbox items", "Add at least one lootbox item before saving it as an item base.")
            return

        existing_item_base = self.find_item_base(lootbox_name)
        if existing_item_base is not None and (
            editing_index is None
            or not (0 <= editing_index < len(self.item_bases))
            or self.item_bases[editing_index] is not existing_item_base
        ):
            messagebox.showerror("Duplicate item base", "A catalog item with that name already exists.")
            self.status_var.set("Unable to save lootbox as item base.")
            return

        expected_value = self.calculate_lootbox_expected_value(normalized_rows)
        if expected_value <= 0:
            messagebox.showerror("Invalid expected value", "Expected value must be greater than zero before saving it as an item base.")
            self.status_var.set("Unable to save lootbox as item base.")
            return

        total_probability = self.calculate_lootbox_probability_total(normalized_rows)
        if abs(total_probability - 100.0) >= 0.0001:
            proceed = messagebox.askyesno(
                "Probability total is not 100%",
                f"The current probability total is {format_decimal(total_probability)}%. Save this expected value anyway?",
            )
            if not proceed:
                self.status_var.set("Save cancelled for lootbox item base.")
                return

        previous_item_bases = self.clone_item_bases_state()
        item_base = {
            "item_name": lootbox_name,
            "item_priority": "1",
            "item_base_value": format_decimal(expected_value),
            "item_value": format_decimal(expected_value),
            "item_source": "lootbox",
            "lootbox_items": self.clone_lootbox_items(normalized_rows),
        }

        try:
            if editing_index is not None and 0 <= editing_index < len(self.item_bases):
                self.item_bases[editing_index] = item_base
            else:
                self.item_bases.append(item_base)
            self.sort_item_bases()
            self.save_pack_data()
        except Exception as exc:
            self.item_bases = previous_item_bases
            messagebox.showerror("Save failed", str(exc))
            self.status_var.set("Unable to save lootbox as item base.")
            return

        new_index = next(
            (
                item_index
                for item_index, entry in enumerate(self.item_bases)
                if normalize_item_name(entry.get("item_name", "")) == normalize_item_name(lootbox_name)
            ),
            None,
        )
        if new_index is not None:
            self.lootbox_edit_item_base_index = new_index
            self.select_item_base(new_index)
        self.status_var.set(
            f"Updated lootbox item base: {lootbox_name}"
            if editing_index is not None and 0 <= editing_index < len(previous_item_bases)
            else f"Saved lootbox expected value as item base: {lootbox_name}"
        )

    def rename_item_base_references(self, previous_name: str, new_name: str) -> None:
        original_rename_item_base_references(self, previous_name, new_name)
        previous_key = normalize_item_name(previous_name)
        if not previous_key:
            return
        replacement_name = new_name or previous_name
        for entry in self.item_bases:
            if not _is_lootbox_item_base(entry):
                continue
            updated_rows = self.clone_lootbox_items(entry.get("lootbox_items", []))
            for lootbox_item in updated_rows:
                if normalize_item_name(lootbox_item.get("item_name", "")) == previous_key:
                    lootbox_item["item_name"] = replacement_name
            entry["lootbox_items"] = updated_rows
        for item in self.lootbox_editor_items:
            if normalize_item_name(item.get("item_name", "")) == previous_key:
                item["item_name"] = replacement_name
        self.recalculate_stored_lootbox_item_bases()
        self.update_lootbox_metrics()
        popup = getattr(self, "lootbox_popup", None)
        if popup is not None and popup.winfo_exists():
            self.render_lootbox_calculator()

    def get_item_base_usage(self, item_name: str) -> list[str]:
        usages = list(original_get_item_base_usage(self, item_name))
        target_key = normalize_item_name(item_name)
        for entry in self.item_bases:
            if not _is_lootbox_item_base(entry):
                continue
            lootbox_rows = self.clone_lootbox_items(entry.get("lootbox_items", []))
            if any(normalize_item_name(row.get("item_name", "")) == target_key for row in lootbox_rows):
                usage_label = f"Stored Lootbox: {entry.get('item_name', 'Unnamed Lootbox')}"
                if all(normalize_item_name(existing) != normalize_item_name(usage_label) for existing in usages):
                    usages.append(usage_label)
        if any(normalize_item_name(item.get("item_name", "")) == target_key for item in self.lootbox_editor_items):
            lootbox_name = self.lootbox_name_var.get().strip() or "Current Lootbox Draft"
            usage_label = f"Lootbox: {lootbox_name}"
            if all(normalize_item_name(existing) != normalize_item_name(usage_label) for existing in usages):
                usages.append(usage_label)
        return usages

    def clone_item_bases_state(self) -> list[dict[str, str]]:
        cloned: list[dict[str, str]] = []
        for entry in self.item_bases:
            normalized_entry = {
                "item_name": str(entry.get("item_name", "") or "").strip(),
                "item_priority": str(entry.get("item_priority", "") or "").strip(),
                "item_base_value": str(entry.get("item_base_value", "") or "").strip(),
                "item_value": str(entry.get("item_value", "") or "").strip(),
            }
            if _is_lootbox_item_base(entry):
                normalized_entry["item_source"] = "lootbox"
                normalized_entry["lootbox_items"] = self.clone_lootbox_items(entry.get("lootbox_items", []))
            cloned.append(normalized_entry)
        return cloned

    def prepare_item_base_for_save(self, exclude_index: int | None) -> dict[str, str]:
        item_base = original_prepare_item_base_for_save(self, exclude_index)
        if exclude_index is None or not (0 <= exclude_index < len(self.item_bases)):
            return item_base
        existing_entry = self.item_bases[exclude_index]
        if _is_lootbox_item_base(existing_entry):
            item_base["item_source"] = "lootbox"
            item_base["lootbox_items"] = self.clone_lootbox_items(existing_entry.get("lootbox_items", []))
        return item_base

    def load_pack_data(self, select_index: int | None) -> None:
        original_load_pack_data(self, select_index)
        if self.recalculate_stored_lootbox_item_bases():
            original_save_pack_data(self)
        self.update_lootbox_metrics()

    def save_pack_data(self) -> None:
        self.recalculate_stored_lootbox_item_bases()
        original_save_pack_data(self)
        self.update_lootbox_metrics()
        popup = getattr(self, "lootbox_popup", None)
        if popup is not None and popup.winfo_exists():
            self.render_lootbox_calculator()

    PacksPanelMixin._ensure_lootbox_state = _ensure_lootbox_state
    PacksPanelMixin._build_packs_tab = _build_packs_tab
    PacksPanelMixin.render_pack_editor = render_pack_editor
    PacksPanelMixin.render_item_base_manager = render_item_base_manager
    PacksPanelMixin.clone_lootbox_items = clone_lootbox_items
    PacksPanelMixin._lootbox_row_has_content = _lootbox_row_has_content
    PacksPanelMixin.get_lootbox_item_base_value = get_lootbox_item_base_value
    PacksPanelMixin.calculate_item_base_value = calculate_item_base_value
    PacksPanelMixin.recalculate_stored_lootbox_item_bases = recalculate_stored_lootbox_item_bases
    PacksPanelMixin.update_item_base_preview_value = update_item_base_preview_value
    PacksPanelMixin.calculate_lootbox_line_expected_value = calculate_lootbox_line_expected_value
    PacksPanelMixin.calculate_lootbox_expected_value = calculate_lootbox_expected_value
    PacksPanelMixin.calculate_lootbox_probability_total = calculate_lootbox_probability_total
    PacksPanelMixin.update_lootbox_metrics = update_lootbox_metrics
    PacksPanelMixin.clear_lootbox_form = clear_lootbox_form
    PacksPanelMixin.add_lootbox_item = add_lootbox_item
    PacksPanelMixin.remove_lootbox_item = remove_lootbox_item
    PacksPanelMixin.open_new_lootbox_draft = open_new_lootbox_draft
    PacksPanelMixin.edit_selected_lootbox_item_base = edit_selected_lootbox_item_base
    PacksPanelMixin.open_lootbox_calculator = open_lootbox_calculator
    PacksPanelMixin.close_lootbox_calculator = close_lootbox_calculator
    PacksPanelMixin.render_lootbox_calculator = render_lootbox_calculator
    PacksPanelMixin._create_lootbox_item_row = _create_lootbox_item_row
    PacksPanelMixin.save_lootbox_as_item_base = save_lootbox_as_item_base
    PacksPanelMixin.rename_item_base_references = rename_item_base_references
    PacksPanelMixin.get_item_base_usage = get_item_base_usage
    PacksPanelMixin.clone_item_bases_state = clone_item_bases_state
    PacksPanelMixin.prepare_item_base_for_save = prepare_item_base_for_save
    PacksPanelMixin.load_pack_data = load_pack_data
    PacksPanelMixin.save_pack_data = save_pack_data
    PackRepository.load = load
    PackRepository.save = save
    _PATCHED = True















    from tog_app.constants import FORMATION_SLOT_LABELS, FORMATION_SLOT_ORDER, TEAM_OPTIONS
    from tog_app.helpers import character_display_name
    from tog_app.panels.characters import CharactersPanelMixin
    from tog_app.panels.formations import FormationsPanelMixin

    def _capture_canvas_yview(canvas: tk.Canvas | None) -> tuple[float, float] | None:
        if canvas is None or not canvas.winfo_exists():
            return None
        return tuple(float(value) for value in canvas.yview())

    def _restore_canvas_yview(self, canvas: tk.Canvas | None, yview: tuple[float, float] | None) -> None:
        if canvas is None or yview is None:
            return
        start = max(0.0, min(1.0, float(yview[0])))

        def restore() -> None:
            if not canvas.winfo_exists():
                return
            canvas.update_idletasks()
            scrollregion = canvas.bbox("all")
            if scrollregion is not None:
                canvas.configure(scrollregion=scrollregion)
            canvas.yview_moveto(start)

        self.after_idle(restore)

    original_character_refresh_summary = CharactersPanelMixin.refresh_summary

    def _load_character_into_form(self, index: int) -> None:
        if not (0 <= index < len(self.rows)):
            return
        row = self.rows[index]
        for header in self.headers:
            self.variables[header].set(self._get_character_form_display_value(header, row.get(header, "")))
        self.selected_title_var.set(row.get("Name", "") or "Unnamed Character")
        self.update_icon_preview()

    def _reset_character_form_inputs(self) -> None:
        for header in self.headers:
            self.variables[header].set("")
        self.selected_title_var.set("New Character")
        self.update_icon_preview()

    def refresh_summary(self, select_index: int | None) -> None:
        scroll_state = _capture_canvas_yview(getattr(self, "summary_canvas", None))
        original_character_refresh_summary(self, select_index)
        _restore_canvas_yview(self, getattr(self, "summary_canvas", None), scroll_state)

    def on_character_summary_filter_changed(self) -> None:
        self.refresh_summary(select_index=self.selected_index)
        self.update_summary_count()
        self.status_var.set("Updated character summary filters.")

    def on_sort_changed(self, _event: tk.Event | None = None) -> None:
        self.apply_current_sort(save=True)
        self.refresh_summary(select_index=self.selected_index)
        self.update_summary_count()
        if self.selected_index is not None:
            self._load_character_into_form(self.selected_index)
        else:
            self._reset_character_form_inputs()
        self.render_character_action_bar()
        self.status_var.set(f"Applied {self.sort_mode_var.get().lower()}.")

    def select_item(self, index: int) -> None:
        if not (0 <= index < len(self.rows)):
            return

        self.selected_index = index
        row = self.rows[index]
        self._load_character_into_form(index)
        self.refresh_summary(select_index=index)
        self.update_summary_count()
        self.render_character_action_bar()
        self.status_var.set(f"Selected character #{index + 1}: {row.get('Name', '(no name)')}")

    def clear_form(self, keep_status: bool = False) -> None:
        self.selected_index = None
        self._reset_character_form_inputs()
        self.refresh_summary(select_index=None)
        self.update_summary_count()
        self.render_character_action_bar()
        if not keep_status:
            self.status_var.set("Editor cleared. Ready for a new character.")

    original_refresh_formations_list = FormationsPanelMixin.refresh_formations_list
    original_render_formation_editor = FormationsPanelMixin.render_formation_editor

    def refresh_formations_list(self, select_index: int | None) -> None:
        scroll_state = _capture_canvas_yview(getattr(self, "formations_list_canvas", None))
        original_refresh_formations_list(self, select_index)
        _restore_canvas_yview(self, getattr(self, "formations_list_canvas", None), scroll_state)

    def render_formation_editor(
        self,
        preserve_editor_scroll: bool = False,
        preserve_roster_scroll: bool = False,
        reset_roster_scroll: bool = False,
    ) -> None:
        roster_scroll = _capture_canvas_yview(getattr(self, "formations_roster_canvas", None)) if preserve_roster_scroll else None
        original_render_formation_editor(
            self,
            preserve_editor_scroll=preserve_editor_scroll,
            reset_roster_scroll=reset_roster_scroll,
        )
        if preserve_roster_scroll:
            _restore_canvas_yview(self, getattr(self, "formations_roster_canvas", None), roster_scroll)

    def on_formations_roster_canvas_configure(self, event: tk.Event) -> None:
        self.formations_roster_canvas.itemconfigure(self.formations_roster_window, width=event.width)
        self._render_roster_fill_spacer()
        new_layout_key = self.get_roster_layout_key()
        if new_layout_key != self.roster_layout_key:
            self.render_formation_editor(
                preserve_editor_scroll=True,
                preserve_roster_scroll=True,
            )

    def on_team_selection_changed(self, _event: tk.Event | None = None) -> None:
        selected_team = self.team_name_var.get().strip() or TEAM_OPTIONS[0]
        self.sync_active_team_slots()
        self.pending_slot_character = None
        self.pending_slot_origin = None
        self.load_team_slots_into_editor(selected_team)
        self.render_formation_editor(
            preserve_editor_scroll=True,
            preserve_roster_scroll=True,
        )
        self.status_var.set(f"Showing {selected_team} for {self.formation_name_var.get().strip() or 'new formation'}.")

    def on_roster_filter_changed(self, _event: tk.Event | None = None) -> None:
        self.render_formation_editor(
            preserve_editor_scroll=True,
            preserve_roster_scroll=True,
        )

    def clear_formation_slot(self, slot_key: str) -> None:
        current_value = self.formation_slot_keys.get(slot_key, "").strip()
        if not current_value:
            return
        self.formation_slot_keys[slot_key] = ""
        self.formation_slot_vars[slot_key].set("")
        self.render_formation_editor(
            preserve_editor_scroll=True,
            preserve_roster_scroll=True,
        )
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
        self.render_formation_editor(
            preserve_editor_scroll=True,
            preserve_roster_scroll=True,
        )
        self.status_var.set(f"Moved {character_display_name(self.find_character_row(character_name)) or character_name} to {FORMATION_SLOT_LABELS[slot_key]}.")

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
        self.render_formation_editor(
            preserve_editor_scroll=True,
            preserve_roster_scroll=True,
        )
        self.status_var.set(f"Placed {character_display_name(self.find_character_row(character_name)) or character_name} in {FORMATION_SLOT_LABELS[slot_key]}.")

    original_refresh_packs_list = PacksPanelMixin.refresh_packs_list

    def refresh_packs_list(self, select_index: int | None) -> None:
        scroll_state = _capture_canvas_yview(getattr(self, "packs_list_canvas", None))
        original_refresh_packs_list(self, select_index)
        _restore_canvas_yview(self, getattr(self, "packs_list_canvas", None), scroll_state)

    def _refresh_item_catalog_search_views(self) -> None:
        if self.pack_scene_var.get() == "editor":
            scroll_state = _capture_canvas_yview(getattr(self, "packs_editor_canvas", None))
            self.render_pack_catalog_results()
            _restore_canvas_yview(self, getattr(self, "packs_editor_canvas", None), scroll_state)
        popup = getattr(self, "item_base_manager_popup", None)
        if popup is not None and popup.winfo_exists():
            canvas = getattr(self, "item_base_manager_canvas", None)
            scroll_state = _capture_canvas_yview(canvas)
            self.render_item_base_manager_results()
            _restore_canvas_yview(self, canvas, scroll_state)

    def _on_item_catalog_search_changed(self, *_args: object) -> None:
        pending = getattr(self, "_item_catalog_search_after", None)
        if pending is not None:
            try:
                self.after_cancel(pending)
            except tk.TclError:
                pass

        self._item_catalog_search_after = self.after(120, self._refresh_item_catalog_search_views)

    original_runtime_refresh_tower_progress_history = TowerProgressPanelMixin.refresh_tower_progress_history

    def refresh_tower_progress_history(self, select_index: int | None) -> None:
        scroll_state = _capture_canvas_yview(getattr(self, "tower_progress_history_canvas", None))
        original_runtime_refresh_tower_progress_history(self, select_index)
        _restore_canvas_yview(self, getattr(self, "tower_progress_history_canvas", None), scroll_state)

    CharactersPanelMixin._load_character_into_form = _load_character_into_form
    CharactersPanelMixin._reset_character_form_inputs = _reset_character_form_inputs
    CharactersPanelMixin.refresh_summary = refresh_summary
    CharactersPanelMixin.on_character_summary_filter_changed = on_character_summary_filter_changed
    CharactersPanelMixin.on_sort_changed = on_sort_changed
    CharactersPanelMixin.select_item = select_item
    CharactersPanelMixin.clear_form = clear_form

    FormationsPanelMixin.refresh_formations_list = refresh_formations_list
    FormationsPanelMixin.render_formation_editor = render_formation_editor
    FormationsPanelMixin.on_formations_roster_canvas_configure = on_formations_roster_canvas_configure
    FormationsPanelMixin.on_team_selection_changed = on_team_selection_changed
    FormationsPanelMixin.on_roster_filter_changed = on_roster_filter_changed
    FormationsPanelMixin.clear_formation_slot = clear_formation_slot
    FormationsPanelMixin.on_slot_clicked = on_slot_clicked
    FormationsPanelMixin.assign_character_to_slot = assign_character_to_slot

    PacksPanelMixin.refresh_packs_list = refresh_packs_list
    PacksPanelMixin._refresh_item_catalog_search_views = _refresh_item_catalog_search_views
    PacksPanelMixin._on_item_catalog_search_changed = _on_item_catalog_search_changed

    TowerProgressPanelMixin.refresh_tower_progress_history = refresh_tower_progress_history
    _PATCHED = True



    from tog_app.app_window import TogCharacterManager
    from tog_app.constants import BACKGROUND

    original_setup_styles = TogCharacterManager._setup_styles

    def _setup_styles(self) -> None:
        original_setup_styles(self)
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure(
            "TCombobox",
            padding=(12, 7, 12, 7),
            arrowsize=16,
            borderwidth=1,
            relief="flat",
            foreground=TEXT,
            fieldbackground=SURFACE,
            background=SURFACE,
            insertcolor=TEXT,
            arrowcolor=PRIMARY_DARK,
            bordercolor=BORDER,
            lightcolor=BORDER,
            darkcolor=BORDER,
        )
        style.map(
            "TCombobox",
            foreground=[("disabled", TEXT_MUTED), ("readonly", TEXT)],
            fieldbackground=[("disabled", SURFACE_MUTED), ("readonly", SURFACE), ("focus", SURFACE)],
            background=[("readonly", SURFACE), ("active", SURFACE)],
            bordercolor=[("focus", PRIMARY), ("readonly", BORDER)],
            lightcolor=[("focus", PRIMARY), ("readonly", BORDER)],
            darkcolor=[("focus", PRIMARY), ("readonly", BORDER)],
            arrowcolor=[("disabled", TEXT_MUTED), ("active", PRIMARY_DARK), ("focus", PRIMARY_DARK), ("readonly", PRIMARY_DARK)],
        )

        style.configure(
            "TNotebook",
            background=BACKGROUND,
            borderwidth=0,
            tabmargins=(0, 10, 0, 0),
        )
        style.configure(
            "TNotebook.Tab",
            background=BACKGROUND,
            foreground=TEXT_MUTED,
            borderwidth=0,
            padding=(18, 10),
            font=self.status_font,
            focuscolor=BACKGROUND,
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", SURFACE), ("active", SURFACE_MUTED)],
            foreground=[("selected", PRIMARY_DARK), ("active", TEXT)],
            lightcolor=[("selected", PRIMARY_SOFT), ("active", BORDER)],
            darkcolor=[("selected", PRIMARY_SOFT), ("active", BORDER)],
            bordercolor=[("selected", PRIMARY_SOFT), ("active", BORDER)],
            font=[("selected", self.label_font), ("!selected", self.status_font)],
        )

        self.option_add("*TCombobox*Listbox.background", SURFACE)
        self.option_add("*TCombobox*Listbox.foreground", TEXT)
        self.option_add("*TCombobox*Listbox.selectBackground", PRIMARY_SOFT)
        self.option_add("*TCombobox*Listbox.selectForeground", PRIMARY_DARK)
        self.option_add("*TCombobox*Listbox.font", self.body_font)

    TogCharacterManager._setup_styles = _setup_styles
    _PATCHED = True



    PACK_SORT_OPTIONS = ("Value (Descending)", "Name (Ascending)")

    def _build_packs_tab(self) -> None:
        original_build_packs_tab(self)
        self._ensure_lootbox_state()
        if not hasattr(self, "pack_sort_mode_var"):
            self.pack_sort_mode_var = tk.StringVar(value=PACK_SORT_OPTIONS[0])

        packs_header = None
        if getattr(self, "packs_list_scene", None) is not None:
            children = self.packs_list_scene.winfo_children()
            if children:
                packs_header = children[0]

        if packs_header is None or not packs_header.winfo_exists():
            return

        list_actions = None
        for child in packs_header.winfo_children():
            if isinstance(child, tk.Frame):
                buttons = [widget for widget in child.winfo_children() if isinstance(widget, tk.Button)]
                if len(buttons) >= 2:
                    list_actions = child
                    break

        existing_sort = getattr(self, "packs_sort_wrap", None)
        if existing_sort is not None and existing_sort.winfo_exists():
            existing_sort.destroy()

        packs_header.columnconfigure(1, weight=0)
        packs_header.columnconfigure(2, weight=0)

        sort_wrap = tk.Frame(packs_header, bg=SURFACE)
        sort_wrap.grid(row=0, column=1, sticky="e", padx=(0, 12))
        self.packs_sort_wrap = sort_wrap
        tk.Label(
            sort_wrap,
            text="Sort",
            bg=SURFACE,
            fg=TEXT_MUTED,
            font=self.label_font,
        ).pack(anchor="e")
        sort_picker = ttk.Combobox(
            sort_wrap,
            textvariable=self.pack_sort_mode_var,
            values=PACK_SORT_OPTIONS,
            state="readonly",
            width=18,
        )
        sort_picker.pack(anchor="e", pady=(6, 0), ipady=4)
        sort_picker.bind("<<ComboboxSelected>>", self.on_pack_sort_changed)
        self.packs_sort_picker = sort_picker

        if list_actions is not None and list_actions.winfo_exists():
            list_actions.grid_configure(row=0, column=2, sticky="e")

    def get_pack_sort_key(self, pack: dict[str, object]) -> tuple[object, ...]:
        pack_name = normalize_item_name(str(pack.get("pack_name", "") or ""))
        items = self.clone_pack_items(pack.get("items", []))
        total_value = self.calculate_pack_total_value(items)
        price_usd = self.calculate_pack_price_usd(str(pack.get("price_brl", "") or "").strip())
        ratio = total_value / price_usd if price_usd > 0 else 0.0
        sort_mode = self.pack_sort_mode_var.get().strip() if hasattr(self, "pack_sort_mode_var") else PACK_SORT_OPTIONS[0]
        if sort_mode == PACK_SORT_OPTIONS[1]:
            return (pack_name,)
        return (-ratio, -total_value, pack_name)

    def on_pack_sort_changed(self, _event: tk.Event | None = None) -> None:
        self.refresh_packs_list(select_index=self.selected_pack_index)
        sort_mode = self.pack_sort_mode_var.get().strip() if hasattr(self, "pack_sort_mode_var") else PACK_SORT_OPTIONS[0]
        self.status_var.set(f"Sorted packs by {sort_mode.lower()}.")

    PacksPanelMixin._build_packs_tab = _build_packs_tab
    PacksPanelMixin.get_pack_sort_key = get_pack_sort_key
    PacksPanelMixin.on_pack_sort_changed = on_pack_sort_changed
    _PATCHED = True


    from tasks_runtime_patch import apply_tasks_runtime_patch
    apply_tasks_runtime_patch()
