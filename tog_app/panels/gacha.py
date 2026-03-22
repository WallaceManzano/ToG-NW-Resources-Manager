from __future__ import annotations

import math
import threading
import tkinter as tk
from collections import Counter
from tkinter import messagebox, ttk
from typing import TYPE_CHECKING


from ..constants import *
from ..helpers import *

if TYPE_CHECKING:
    from ..app_window import TogCharacterManager


GACHA_MODE_MAX = "Pull Until Maxed"
GACHA_MODE_BUDGET = "Fixed Pull Budget"
GACHA_MODE_OPTIONS = (GACHA_MODE_BUDGET, GACHA_MODE_MAX)


class GachaPanelMixin:
    def _build_gacha_tab(self) -> None:
        self.gacha_tab.columnconfigure(0, weight=1)
        self.gacha_tab.rowconfigure(0, weight=1)

        shell = self._make_panel(self.gacha_tab)
        shell.grid(row=0, column=0, sticky="nsew")
        shell.columnconfigure(0, weight=1)
        shell.rowconfigure(0, weight=1)

        self.gacha_canvas = tk.Canvas(shell, bg=SURFACE, highlightthickness=0, bd=0)
        self.gacha_canvas.grid(row=0, column=0, sticky="nsew")
        gacha_scroll = ttk.Scrollbar(shell, orient="vertical", command=self.gacha_canvas.yview)
        gacha_scroll.grid(row=0, column=1, sticky="ns")
        self.gacha_canvas.configure(yscrollcommand=gacha_scroll.set)

        self.gacha_content = tk.Frame(self.gacha_canvas, bg=SURFACE)
        self.gacha_window = self.gacha_canvas.create_window((0, 0), window=self.gacha_content, anchor="nw")
        self.gacha_content.bind(
            "<Configure>",
            lambda _event: self.gacha_canvas.configure(scrollregion=self.gacha_canvas.bbox("all")),
        )
        self.gacha_canvas.bind("<Configure>", self.on_gacha_canvas_configure)
        self._bind_mousewheel(self.gacha_canvas, self.gacha_content)

        self.gacha_content.configure(padx=20, pady=20)
        self.gacha_content.columnconfigure(0, weight=1)

        header = tk.Frame(self.gacha_content, bg=SURFACE)
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)
        tk.Label(
            header,
            text="Gacha Simulation",
            bg=SURFACE,
            fg=TEXT,
            font=self.section_font,
        ).grid(row=0, column=0, sticky="w")
        tk.Label(
            header,
            text=(
                "Estimate the pull cost to fully max a Unity character, or the copies you expect to get "
                "from a fixed ticket budget."
            ),
            bg=SURFACE,
            fg=TEXT_MUTED,
            font=self.body_font,
            justify="left",
            wraplength=940,
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

        controls_card = tk.Frame(
            self.gacha_content,
            bg=SURFACE_MUTED,
            highlightthickness=1,
            highlightbackground=BORDER,
            bd=0,
            padx=18,
            pady=18,
        )
        controls_card.grid(row=1, column=0, sticky="ew", pady=(16, 12))
        for column in range(3):
            controls_card.columnconfigure(column, weight=1)

        tk.Label(
            controls_card,
            text="Simulation Settings",
            bg=SURFACE_MUTED,
            fg=TEXT,
            font=self.section_font,
        ).grid(row=0, column=0, columnspan=3, sticky="w")

        mode_field = tk.Frame(controls_card, bg=SURFACE_MUTED)
        mode_field.grid(row=1, column=0, sticky="ew", padx=10, pady=(14, 8))
        mode_field.columnconfigure(0, weight=1)
        tk.Label(
            mode_field,
            text="Mode",
            bg=SURFACE_MUTED,
            fg=TEXT_MUTED,
            font=self.label_font,
        ).grid(row=0, column=0, sticky="w")
        mode_picker = ttk.Combobox(
            mode_field,
            textvariable=self.gacha_mode_var,
            values=GACHA_MODE_OPTIONS,
            state="readonly",
            width=18,
        )
        mode_picker.grid(row=1, column=0, sticky="ew", pady=(6, 0), ipady=4)
        mode_picker.bind("<<ComboboxSelected>>", self.on_gacha_settings_changed)

        self._create_gacha_input(controls_card, "Base Rate (%)", self.gacha_rate_var, 1, 1)
        self._create_gacha_input(controls_card, "Target Copies", self.gacha_target_copies_var, 1, 2)
        self._create_gacha_input(controls_card, "Trials", self.gacha_trials_var, 2, 0)
        self._create_gacha_input(controls_card, "Pity Pull", self.gacha_pity_limit_var, 2, 1)
        self.gacha_budget_field = self._create_gacha_input(
            controls_card,
            "Available Pulls",
            self.gacha_available_pulls_var,
            2,
            2,
        )

        options_row = tk.Frame(controls_card, bg=SURFACE_MUTED)
        options_row.grid(row=3, column=0, columnspan=3, sticky="ew", padx=10, pady=(10, 0))
        options_row.columnconfigure(0, weight=1)
        self.gacha_hard_pity_check = tk.Checkbutton(
            options_row,
            text="Hard pity",
            variable=self.gacha_hard_pity_var,
            command=self.on_gacha_settings_changed,
            bg=SURFACE_MUTED,
            fg=TEXT,
            activebackground=SURFACE_MUTED,
            activeforeground=TEXT,
            selectcolor=SURFACE,
            font=self.body_font,
            anchor="w",
        )
        self.gacha_hard_pity_check.grid(row=0, column=0, sticky="w")

        tk.Label(
            controls_card,
            textvariable=self.gacha_mode_note_var,
            bg=SURFACE_MUTED,
            fg=TEXT_MUTED,
            font=self.body_font,
            justify="left",
            wraplength=900,
        ).grid(row=4, column=0, columnspan=3, sticky="w", padx=10, pady=(10, 0))

        actions = tk.Frame(controls_card, bg=SURFACE_MUTED)
        actions.grid(row=5, column=0, columnspan=3, sticky="e", padx=10, pady=(16, 0))
        self.gacha_run_button = self._make_button(
            actions,
            "Simulate",
            self.run_gacha_simulation,
            filled=True,
        )
        self.gacha_run_button.pack(side="left")
        self.gacha_clear_button = self._make_button(
            actions,
            "Clear Results",
            self.clear_gacha_results,
            filled=False,
        )
        self.gacha_clear_button.pack(side="left", padx=(8, 0))

        results_card = tk.Frame(
            self.gacha_content,
            bg=SURFACE,
            highlightthickness=1,
            highlightbackground=BORDER,
            bd=0,
            padx=18,
            pady=18,
        )
        results_card.grid(row=2, column=0, sticky="ew", pady=(0, 12))
        results_card.columnconfigure(0, weight=1)

        tk.Label(
            results_card,
            text="Results",
            bg=SURFACE,
            fg=TEXT,
            font=self.section_font,
        ).grid(row=0, column=0, sticky="w")
        tk.Label(
            results_card,
            textvariable=self.gacha_overview_var,
            bg=SURFACE,
            fg=PRIMARY_DARK,
            font=self.card_title_font,
            justify="left",
            wraplength=920,
        ).grid(row=1, column=0, sticky="w", pady=(6, 0))
        tk.Label(
            results_card,
            textvariable=self.gacha_config_var,
            bg=SURFACE,
            fg=TEXT_MUTED,
            font=self.body_font,
            justify="left",
            wraplength=920,
        ).grid(row=2, column=0, sticky="w", pady=(6, 0))

        self.gacha_metrics_grid = tk.Frame(results_card, bg=SURFACE)
        self.gacha_metrics_grid.grid(row=3, column=0, sticky="ew", pady=(16, 0))
        self.gacha_metrics_grid.columnconfigure(0, weight=1)


        self.gacha_mode_var.trace_add("write", self._on_gacha_mode_trace)
        self._update_gacha_controls()
        self.render_gacha_results()
        self._bind_gacha_mousewheel()

    def _create_gacha_input(
        self,
        parent: tk.Misc,
        label: str,
        variable: tk.StringVar,
        row: int,
        column: int,
    ) -> tk.Frame:
        field = tk.Frame(parent, bg=SURFACE_MUTED)
        field.grid(row=row, column=column, sticky="ew", padx=10, pady=8)
        field.columnconfigure(0, weight=1)

        tk.Label(
            field,
            text=label,
            bg=SURFACE_MUTED,
            fg=TEXT_MUTED,
            font=self.label_font,
        ).grid(row=0, column=0, sticky="w")
        tk.Entry(
            field,
            textvariable=variable,
            bg=SURFACE,
            fg=TEXT,
            relief="flat",
            bd=0,
            insertbackground=TEXT,
            highlightthickness=1,
            highlightbackground=BORDER,
            highlightcolor=PRIMARY,
            font=self.body_font,
        ).grid(row=1, column=0, sticky="ew", pady=(6, 0), ipady=8)
        return field

    def _bind_gacha_mousewheel(self) -> None:
        widgets: list[tk.Widget] = []

        def collect(widget: tk.Widget) -> None:
            widgets.append(widget)
            for child in widget.winfo_children():
                collect(child)

        collect(self.gacha_content)
        self._bind_mousewheel(self.gacha_canvas, *widgets)

    def _on_gacha_mode_trace(self, *_args: object) -> None:
        self._update_gacha_controls()

    def on_gacha_settings_changed(self, _event: tk.Event | None = None) -> None:
        self._update_gacha_controls()

    def _update_gacha_controls(self) -> None:
        budget_mode = self.gacha_mode_var.get().strip() == GACHA_MODE_BUDGET
        if budget_mode:
            self.gacha_budget_field.grid()
        else:
            self.gacha_budget_field.grid_remove()

        if self.gacha_hard_pity_var.get():
            pity_text = "Hard pity: both natural target pulls and guaranteed pity pulls reset the counter."
        else:
            pity_text = "Carry pity: only the guaranteed pity pull resets the counter."

        if budget_mode:
            mode_text = "The run stops when the available pull budget is exhausted."
        else:
            mode_text = "The run stops only after the target copy count has been reached."

        self.gacha_mode_note_var.set(f"{pity_text} {mode_text}")

    def on_gacha_canvas_configure(self, event: tk.Event) -> None:
        self.gacha_canvas.itemconfigure(self.gacha_window, width=event.width)

    def on_gacha_histogram_resize(self, _event: tk.Event) -> None:
        self.draw_gacha_histogram()

    def refresh_gacha_tab_visuals(self) -> None:
        self.draw_gacha_histogram()

    def run_gacha_simulation(self) -> None:
        try:
            config = self.collect_gacha_config()
        except ValueError as exc:
            messagebox.showerror("Invalid simulation settings", str(exc))
            self.status_var.set("Unable to run gacha simulation.")
            return

        self.gacha_overview_var.set("Running simulation...")
        self.gacha_config_var.set(
            f"{config['num_trials']:,} trial(s) at {config['unity_rate'] * 100:.2f}% base rate."
        )
        self.gacha_chart_caption_var.set("Simulation in progress...")
        self.draw_gacha_histogram()
        self.gacha_run_button.configure(state="disabled")
        self.gacha_clear_button.configure(state="disabled")
        self.status_var.set(f"Running gacha simulation with {config['num_trials']:,} trial(s)...")
        self.update_idletasks()
        request_id = getattr(self, "gacha_request_id", 0) + 1
        self.gacha_request_id = request_id
        self.gacha_pending_result = None
        self.gacha_worker = threading.Thread(
            target=self._run_gacha_simulation_worker,
            args=(request_id, config),
            daemon=True,
        )
        self.gacha_worker.start()
        self.after(80, lambda req_id=request_id: self._poll_gacha_simulation(req_id))

    def _run_gacha_simulation_worker(self, request_id: int, config: dict[str, object]) -> None:
        try:
            from ..mcsim import monte_carlo_simulation, summarize_results

            results = monte_carlo_simulation(
                num_trials=int(config["num_trials"]),
                copies_needed=int(config["copies_needed"]),
                unity_rate=float(config["unity_rate"]),
                pity_limit=int(config["pity_limit"]),
                hard_pity=bool(config["hard_pity"]),
                available_pulls=config["available_pulls"],
            )
            summary = summarize_results(
                results,
                copies_needed=int(config["copies_needed"]),
                available_pulls=config["available_pulls"],
            )
        except Exception as exc:
            self.gacha_pending_result = {
                "request_id": request_id,
                "config": config,
                "error": str(exc),
            }
            return

        self.gacha_pending_result = {
            "request_id": request_id,
            "config": config,
            "results": results,
            "summary": summary,
        }

    def _poll_gacha_simulation(self, request_id: int) -> None:
        if getattr(self, "gacha_request_id", 0) != request_id:
            return

        pending_result = getattr(self, "gacha_pending_result", None)
        if pending_result is None or pending_result.get("request_id") != request_id:
            self.after(80, lambda req_id=request_id: self._poll_gacha_simulation(req_id))
            return

        self.gacha_pending_result = None
        self._finish_gacha_simulation(pending_result)

    def _finish_gacha_simulation(self, payload: dict[str, object]) -> None:
        try:
            error = str(payload.get("error", "") or "")
            if error:
                messagebox.showerror("Simulation failed", error)
                self.gacha_results = []
                self.gacha_summary = {}
                self.gacha_last_config = None
                self.gacha_overview_var.set("Simulation failed. Adjust the settings and try again.")
                self.gacha_config_var.set("")
                self.gacha_chart_caption_var.set("No histogram available.")
                self.render_gacha_results()
                self.status_var.set("Gacha simulation failed.")
                return

            config = payload["config"]
            results = payload["results"]
            summary = payload["summary"]
            self.gacha_results = results
            self.gacha_summary = summary
            self.gacha_last_config = config
            self.render_gacha_results()
            mode_label = "fixed-budget" if config["available_pulls"] is not None else "pull-until-maxed"
            self.status_var.set(
                f"Finished gacha simulation: {int(config['num_trials']):,} trial(s) in {mode_label} mode."
            )
        finally:
            self.gacha_run_button.configure(state="normal")
            self.gacha_clear_button.configure(state="normal")
            self.gacha_worker = None

    def clear_gacha_results(self) -> None:
        if str(self.gacha_run_button.cget("state")) == "disabled":
            self.status_var.set("Wait for the current gacha simulation to finish.")
            return

        self.gacha_request_id = getattr(self, "gacha_request_id", 0) + 1
        self.gacha_pending_result = None
        self.gacha_worker = None
        self.gacha_results = []
        self.gacha_summary = {}
        self.gacha_last_config = None
        self.gacha_overview_var.set("Choose settings and run a simulation.")
        self.gacha_config_var.set("No simulation has been run yet.")
        self.gacha_chart_caption_var.set("The histogram will appear here after a simulation finishes.")
        self.render_gacha_results()
        self.status_var.set("Cleared gacha simulation results.")

    def collect_gacha_config(self) -> dict[str, object]:
        mode = self.gacha_mode_var.get().strip() or GACHA_MODE_MAX
        num_trials = parse_int(self.gacha_trials_var.get())
        copies_needed = parse_int(self.gacha_target_copies_var.get())
        pity_limit = parse_int(self.gacha_pity_limit_var.get())
        rate_percent = parse_float(self.gacha_rate_var.get())

        if num_trials <= 0:
            raise ValueError("Trials must be a positive whole number.")
        if copies_needed <= 0:
            raise ValueError("Target copies must be a positive whole number.")
        if pity_limit < 0:
            raise ValueError("Pity pull must be a positive whole number.")
        if rate_percent < 0 or rate_percent > 100:
            raise ValueError("Base rate must be between 0 and 100 percent.")

        available_pulls: int | None = None
        if mode == GACHA_MODE_BUDGET:
            available_pulls = parse_int(self.gacha_available_pulls_var.get())
            if available_pulls < 0:
                raise ValueError("Available pulls cannot be negative.")

        return {
            "mode": mode,
            "num_trials": num_trials,
            "copies_needed": copies_needed,
            "pity_limit": pity_limit,
            "unity_rate": rate_percent / 100,
            "hard_pity": bool(self.gacha_hard_pity_var.get()),
            "available_pulls": available_pulls,
        }

    def render_gacha_results(self) -> None:
        for child in self.gacha_metrics_grid.winfo_children():
            child.destroy()

        if not self.gacha_last_config or not self.gacha_summary:
            self.gacha_overview_var.set("Choose settings and run a simulation.")
            self.gacha_config_var.set("No simulation has been run yet.")
            self.gacha_chart_caption_var.set("The histogram will appear here after a simulation finishes.")
            self._render_gacha_empty_state()
            self._bind_gacha_mousewheel()
            self.draw_gacha_histogram()
            return

        config = self.gacha_last_config
        summary = self.gacha_summary
        rate_percent = float(config["unity_rate"]) * 100
        copies_needed = int(config["copies_needed"])
        hard_pity_text = "natural pulls reset pity" if bool(config["hard_pity"]) else "natural pulls keep pity progress"

        if config["available_pulls"] is None:
            self.gacha_overview_var.set(
                "Average cost to fully max the unit: "
                f"{format_decimal(float(summary['average_pulls']))} pulls. "
                f"Half of runs finish by {summary['median_pulls']} pulls, and 90% finish by {summary['p90_pulls']} pulls."
            )
            self.gacha_config_var.set(
                f"{int(config['num_trials']):,} trial(s) | Target copies: {copies_needed} | "
                f"Base rate: {rate_percent:.2f}% | Pity: {config['pity_limit']} | {hard_pity_text}"
            )
            metrics = [
                ("Average Pulls", format_decimal(float(summary["average_pulls"])), True),
                ("Median Pulls", str(summary["median_pulls"]), False),
                ("10th Percentile", str(summary["p10_pulls"]), False),
                ("25th Percentile", str(summary["p25_pulls"]), False),
                ("75th Percentile", str(summary["p75_pulls"]), False),
                ("90th Percentile", str(summary["p90_pulls"]), False),
                ("99th Percentile", str(summary["p99_pulls"]), False),
                ("Best Case", str(summary["best_pulls"]), False),
                ("Worst Case", str(summary["worst_pulls"]), False),
            ]
            self._render_gacha_metric_section("Pull Cost", metrics)
        else:
            available_pulls = int(config["available_pulls"])
            success_rate = float(summary["success_rate"]) * 100
            self.gacha_overview_var.set(
                f"With {available_pulls} pulls, you average {format_decimal(float(summary['average_copies']))} copies. "
                f"The chance to reach {copies_needed} copies is {success_rate:.2f}%."
            )
            self.gacha_config_var.set(
                f"{int(config['num_trials']):,} trial(s) | Pull budget: {available_pulls} | "
                f"Target copies: {copies_needed} | Base rate: {rate_percent:.2f}% | "
                f"Pity: {config['pity_limit']} | {hard_pity_text}"
            )
            metrics = [
                ("Average Copies", format_decimal(float(summary["average_copies"])), True),
                ("Median Copies", str(summary["median_copies"]), False),
                ("Chance To Max", f"{success_rate:.2f}%", False),
                ("10th Percentile", str(summary["p10_copies"]), False),
                ("25th Percentile", str(summary["p25_copies"]), False),
                ("75th Percentile", str(summary["p75_copies"]), False),
                ("99th Percentile", str(summary["p99_copies"]), False),
                ("Best Copies", str(summary["best_copies"]), False),
                ("Worst Copies", str(summary["worst_copies"]), False),
            ]
            self._render_gacha_metric_section("Copies Gained", metrics)

        self._bind_gacha_mousewheel()
        self.draw_gacha_histogram()

    def _render_gacha_empty_state(self) -> None:
        empty = tk.Frame(
            self.gacha_metrics_grid,
            bg=SURFACE_MUTED,
            highlightthickness=1,
            highlightbackground=BORDER,
            bd=0,
            padx=16,
            pady=18,
        )
        empty.grid(row=0, column=0, sticky="ew")
        tk.Label(
            empty,
            text="No simulation results yet",
            bg=SURFACE_MUTED,
            fg=TEXT,
            font=self.card_title_font,
        ).pack(anchor="w")
        tk.Label(
            empty,
            text="Set the gacha parameters above, then run the Monte Carlo simulation to populate these metrics.",
            bg=SURFACE_MUTED,
            fg=TEXT_MUTED,
            font=self.body_font,
            justify="left",
            wraplength=880,
        ).pack(anchor="w", pady=(6, 0))

    def _render_gacha_metric_section(
        self,
        title: str,
        metrics: list[tuple[str, str, bool]],
    ) -> None:
        section = tk.Frame(self.gacha_metrics_grid, bg=SURFACE)
        section.grid(row=0, column=0, sticky="ew")
        section.columnconfigure(0, weight=1)

        tk.Label(
            section,
            text=title,
            bg=SURFACE,
            fg=TEXT,
            font=self.section_font,
        ).grid(row=0, column=0, sticky="w")

        grid = tk.Frame(section, bg=SURFACE)
        grid.grid(row=1, column=0, sticky="ew", pady=(12, 0))
        column_count = 3
        for column in range(column_count):
            grid.columnconfigure(column, weight=1)

        for index, (label, value, accent) in enumerate(metrics):
            self._create_gacha_metric_tile(
                grid,
                label,
                value,
                row=index // column_count,
                column=index % column_count,
                accent=accent,
            )

    def _create_gacha_metric_tile(
        self,
        parent: tk.Misc,
        title: str,
        value: str,
        row: int,
        column: int,
        accent: bool = False,
    ) -> None:
        tile = tk.Frame(
            parent,
            bg=SURFACE_MUTED,
            highlightthickness=1,
            highlightbackground=BORDER,
            bd=0,
            padx=12,
            pady=10,
        )
        tile.grid(row=row, column=column, sticky="ew", padx=6, pady=6)
        tk.Label(
            tile,
            text=title,
            bg=SURFACE_MUTED,
            fg=TEXT_MUTED,
            font=self.label_font,
        ).pack(anchor="w")
        tk.Label(
            tile,
            text=value,
            bg=SURFACE_MUTED,
            fg=PRIMARY_DARK if accent else TEXT,
            font=self.section_font if accent else self.card_title_font,
        ).pack(anchor="w", pady=(6, 0))

    def draw_gacha_histogram(self) -> None:
        canvas = getattr(self, "gacha_histogram_canvas", None)
        if canvas is None or not canvas.winfo_exists():
            return

        canvas.delete("all")
        width = max(480, canvas.winfo_width())
        height = max(300, canvas.winfo_height())
        canvas.configure(width=width, height=height)

        if not self.gacha_results or not self.gacha_last_config:
            canvas.create_text(
                width // 2,
                height // 2,
                text="Run a simulation to draw the histogram.",
                fill=TEXT_MUTED,
                font=self.body_font,
            )
            return

        values, metric_name = self.get_gacha_histogram_values()
        if not values:
            canvas.create_text(
                width // 2,
                height // 2,
                text="No data available for the histogram.",
                fill=TEXT_MUTED,
                font=self.body_font,
            )
            return

        budget_mode = self.gacha_last_config["available_pulls"] is not None
        bins = self.build_gacha_histogram_bins(values, budget_mode)
        if not bins:
            canvas.create_text(
                width // 2,
                height // 2,
                text="No histogram bins could be generated.",
                fill=TEXT_MUTED,
                font=self.body_font,
            )
            return

        plot_left = 56
        plot_top = 28
        plot_right = width - 24
        plot_bottom = height - 52
        plot_width = max(1, plot_right - plot_left)
        plot_height = max(1, plot_bottom - plot_top)

        canvas.create_rectangle(plot_left, plot_top, plot_right, plot_bottom, outline=BORDER, fill=SURFACE)

        max_count = max(bin_info["count"] for bin_info in bins)
        bar_gap = 6 if len(bins) <= 12 else 4
        total_gap = bar_gap * max(0, len(bins) - 1)
        bar_width = max(8, (plot_width - total_gap) / max(1, len(bins)))

        bar_positions: list[dict[str, float]] = []
        for index, bin_info in enumerate(bins):
            x0 = plot_left + index * (bar_width + bar_gap)
            x1 = min(plot_right, x0 + bar_width)
            ratio = (bin_info["count"] / max_count) if max_count else 0
            y0 = plot_bottom - (ratio * plot_height)
            canvas.create_rectangle(x0, y0, x1, plot_bottom, outline=PRIMARY_DARK, fill=PRIMARY_SOFT)
            bar_positions.append(
                {
                    "x0": x0,
                    "x1": x1,
                    "start": float(bin_info["start"]),
                    "end": float(bin_info["end"]),
                }
            )

        for tick_ratio, tick_value in ((0.0, 0), (0.5, round(max_count / 2)), (1.0, max_count)):
            y = plot_bottom - (tick_ratio * plot_height)
            canvas.create_line(plot_left - 4, y, plot_left, y, fill=BORDER)
            canvas.create_text(
                plot_left - 10,
                y,
                text=str(tick_value),
                fill=TEXT_MUTED,
                font=self.card_meta_font,
                anchor="e",
            )

        label_step = 1 if len(bins) <= 12 else max(2, math.ceil(len(bins) / 6))
        for index, bin_info in enumerate(bins):
            if index % label_step != 0 and index != len(bins) - 1:
                continue
            x = bar_positions[index]["x0"] + ((bar_positions[index]["x1"] - bar_positions[index]["x0"]) / 2)
            canvas.create_text(
                x,
                plot_bottom + 16,
                text=bin_info["label"],
                fill=TEXT_MUTED,
                font=self.card_meta_font,
                anchor="n",
            )

        mean_value = (
            float(self.gacha_summary["average_copies"])
            if budget_mode
            else float(self.gacha_summary["average_pulls"])
        )
        median_value = (
            float(self.gacha_summary["median_copies"])
            if budget_mode
            else float(self.gacha_summary["median_pulls"])
        )
        mean_x = self._get_gacha_histogram_line_x(bar_positions, mean_value, plot_left, plot_right)
        median_x = self._get_gacha_histogram_line_x(bar_positions, median_value, plot_left, plot_right)
        canvas.create_line(mean_x, plot_top, mean_x, plot_bottom, fill=PRIMARY_DARK, width=2, dash=(6, 4))
        canvas.create_line(median_x, plot_top, median_x, plot_bottom, fill=DANGER, width=2, dash=(2, 4))

        canvas.create_text(
            plot_left,
            plot_top - 10,
            text=f"{metric_name} distribution",
            fill=TEXT,
            font=self.card_title_font,
            anchor="w",
        )
        canvas.create_line(plot_right - 184, plot_top - 10, plot_right - 156, plot_top - 10, fill=PRIMARY_DARK, width=2, dash=(6, 4))
        canvas.create_text(plot_right - 148, plot_top - 10, text="Mean", fill=TEXT_MUTED, font=self.card_meta_font, anchor="w")
        canvas.create_line(plot_right - 92, plot_top - 10, plot_right - 64, plot_top - 10, fill=DANGER, width=2, dash=(2, 4))
        canvas.create_text(plot_right - 56, plot_top - 10, text="Median", fill=TEXT_MUTED, font=self.card_meta_font, anchor="w")

        canvas.create_text(
            plot_left,
            plot_bottom + 38,
            text=metric_name,
            fill=TEXT_MUTED,
            font=self.card_meta_font,
            anchor="w",
        )
        self.gacha_chart_caption_var.set(
            f"{metric_name} histogram across {len(self.gacha_results):,} trial(s). Dashed line = mean, dotted line = median."
        )

    def get_gacha_histogram_values(self) -> tuple[list[int], str]:
        budget_mode = self.gacha_last_config is not None and self.gacha_last_config["available_pulls"] is not None
        if budget_mode:
            return [int(result["copies"]) for result in self.gacha_results], "Copies Obtained"
        return [int(result["pulls"]) for result in self.gacha_results], "Total Pulls"

    def build_gacha_histogram_bins(
        self,
        values: list[int],
        budget_mode: bool,
    ) -> list[dict[str, int | str]]:
        if not values:
            return []

        minimum = min(values)
        maximum = max(values)
        if budget_mode:
            counts = Counter(values)
            return [
                {
                    "start": current,
                    "end": current,
                    "count": counts.get(current, 0),
                    "label": str(current),
                }
                for current in range(minimum, maximum + 1)
            ]

        span = max(1, maximum - minimum + 1)
        bin_count = min(24, max(8, math.ceil(math.sqrt(len(values)) / 2)))
        bin_count = min(bin_count, span)
        bin_size = max(1, math.ceil(span / max(1, bin_count)))
        counts = [0 for _ in range(math.ceil(span / bin_size))]
        for value in values:
            index = min((value - minimum) // bin_size, len(counts) - 1)
            counts[index] += 1

        bins: list[dict[str, int | str]] = []
        for index, count in enumerate(counts):
            start = minimum + index * bin_size
            end = min(maximum, start + bin_size - 1)
            label = str(start) if start == end else f"{start}-{end}"
            bins.append({"start": start, "end": end, "count": count, "label": label})
        return bins

    def _get_gacha_histogram_line_x(
        self,
        bar_positions: list[dict[str, float]],
        value: float,
        plot_left: int,
        plot_right: int,
    ) -> float:
        if not bar_positions:
            return float(plot_left)

        for bar in bar_positions:
            if bar["start"] <= value <= bar["end"]:
                span = max(1.0, bar["end"] - bar["start"])
                ratio = 0.5 if span == 1.0 and bar["start"] == bar["end"] else (value - bar["start"]) / span
                return bar["x0"] + ((bar["x1"] - bar["x0"]) * ratio)

        if value < bar_positions[0]["start"]:
            return float(plot_left)
        return float(plot_right)






