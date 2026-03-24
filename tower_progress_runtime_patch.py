
from __future__ import annotations

import base64
import io
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
        PRIMARY,
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
    from tog_app.helpers import display_tower_mode_label, parse_int
    from tog_app.panels.tower_progress import TowerProgressPanelMixin

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

    def prepare_tower_progress_entry_for_save(self, captured_at_override: str | None = None) -> dict[str, object]:
        payload = self.collect_tower_progress_data()
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
            entry = self.prepare_tower_progress_entry_for_save()
            self.tower_progress_entries.append(entry)
            self.save_tower_progress_entries()
        except Exception as exc:
            self.tower_progress_entries = previous_entries
            messagebox.showerror("Create failed", str(exc))
            self.status_var.set("Unable to save tower snapshot.")
            return

        new_index = self.tower_progress_entries.index(entry)
        self.select_tower_progress_entry(new_index)
        self.status_var.set(f"Saved tower snapshot for {self.format_tower_progress_timestamp(str(entry.get('captured_at', '') or ''))}.")

    def update_tower_progress_entry(self) -> None:
        if self.selected_tower_progress_index is None:
            messagebox.showwarning("No selection", "Select a tower snapshot first.")
            return

        previous_entries = self.clone_tower_progress_entries()
        index = self.selected_tower_progress_index
        existing_entry = self.tower_progress_entries[index]
        try:
            entry = self.prepare_tower_progress_entry_for_save(str(existing_entry.get("captured_at", "") or ""))
            self.tower_progress_entries[index] = entry
            self.save_tower_progress_entries()
        except Exception as exc:
            self.tower_progress_entries = previous_entries
            messagebox.showerror("Update failed", str(exc))
            self.status_var.set("Unable to update tower snapshot.")
            return

        updated_index = self.tower_progress_entries.index(entry)
        self.select_tower_progress_entry(updated_index)
        self.status_var.set("Updated tower snapshot.")

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
            caption = f"Showing {', '.join(display_tower_mode_label(mode_key) for mode_key in visible_mode_keys)} across {len(all_points)} point(s)."

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

        locator = mdates.AutoDateLocator(minticks=3, maxticks=6)
        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator))

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

    _PATCHED = True

