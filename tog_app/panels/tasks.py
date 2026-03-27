from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import TYPE_CHECKING

from ..constants import *
from ..helpers import *

if TYPE_CHECKING:
    from ..app_window import TogCharacterManager


class TasksPanelMixin:
    def _task_body_text(self) -> str:
        widget = getattr(self, "task_body_text", None)
        if widget is None or not widget.winfo_exists():
            return ""
        return widget.get("1.0", "end-1c").strip()

    def _set_task_body_text(self, value: str) -> None:
        widget = getattr(self, "task_body_text", None)
        if widget is None or not widget.winfo_exists():
            return
        widget.delete("1.0", tk.END)
        if value:
            widget.insert("1.0", value)

    def _task_primary_line(self, body: str) -> str:
        lines = [line.strip() for line in str(body or "").splitlines() if line.strip()]
        if lines:
            return truncate_task_text(lines[0], 72)
        return "Untitled goal"

    def _task_secondary_line(self, body: str) -> str:
        preview = truncate_task_text(body, 180)
        return preview or "No details yet."

    def _task_sort_key(self, task: dict[str, str]) -> tuple[object, ...]:
        return (
            TASK_URGENCY_ORDER.get(canonical_task_urgency(task.get("urgency", "")), 99),
            normalize_character_name(task.get("body", "")),
        )

    def sort_tasks(self) -> None:
        self.tasks.sort(key=self._task_sort_key)

    def clone_tasks(self) -> list[dict[str, str]]:
        return [task.copy() for task in self.tasks]

    def update_task_summary(self) -> None:
        self.task_summary_var.set(f"{len(self.tasks)} goal(s)")

    def _task_matches_filter(self, _task: dict[str, str]) -> bool:
        return True

    def get_filtered_tasks(self) -> list[tuple[int, dict[str, str]]]:
        return [
            (index, task)
            for index, task in enumerate(self.tasks)
            if self._task_matches_filter(task)
        ]

    def _build_task_character_options(self) -> dict[str, str]:
        mapping: dict[str, str] = {"No linked character": ""}
        sorted_rows = sorted(
            self.rows,
            key=lambda row: (
                normalize_character_name(row.get("Name", "")),
                str(row.get("Rarity", "") or "").strip().upper(),
                str(row.get("Color", "") or "").strip().upper(),
            ),
        )
        for row in sorted_rows:
            key = character_version_key(row)
            if not key:
                continue
            l_label = row.get("L", "")
            b_label = row.get("B", "")
            r_label = row.get("R", "")
            base_label = character_display_name(row)
            label = f"{base_label} - {l_label} {b_label} - {r_label}" if l_label else base_label
            if not label:
                label = key
            unique_label = label
            suffix = 2
            while unique_label in mapping and mapping[unique_label] != key:
                unique_label = f"{label} #{suffix}"
                suffix += 1
            mapping[unique_label] = key
        return mapping

    def refresh_task_character_picker_options(self) -> None:
        self.task_character_option_map = self._build_task_character_options()
        picker = getattr(self, "task_character_picker", None)
        if picker is not None and picker.winfo_exists():
            picker.configure(values=tuple(self.task_character_option_map.keys()))
            current_value = self.task_character_var.get().strip()
            if current_value and current_value not in self.task_character_option_map:
                self.task_character_var.set("No linked character")

    def _task_character_label_from_key(self, character_key: str) -> str:
        canonical_key = canonical_character_version_key(character_key)
        for label, value in self.task_character_option_map.items():
            if canonical_character_version_key(value) == canonical_key:
                return label
        row = self.find_character_row(character_key)
        if row is not None:
            display_name = character_display_name(row)
            color_label = display_color_value(row.get("Color", ""))
            return f"{display_name} - {color_label}" if color_label else display_name
        return "No linked character"

    def _task_character_row(self, task: dict[str, str]) -> dict[str, str] | None:
        character_key = str(task.get("character_key", "") or "").strip()
        if not character_key:
            return None
        return self.find_character_row(character_key)

    def _task_character_summary(self, row: dict[str, str] | None) -> str:
        if row is None:
            return "No linked character"
        pieces = [character_display_name(row)]
        color_label = display_color_value(row.get("Color", ""))
        if color_label:
            pieces.append(color_label)
        if row.get("R", ""):
            pieces.append(f"Rev {row.get('R', '')}")
        if row.get("EE", ""):
            pieces.append(f"EE {row.get('EE', '')}")
        return " | ".join(piece for piece in pieces if piece)

    def _render_task_link_preview(self) -> None:
        icon_canvas = getattr(self, "task_link_preview_icon_canvas", None)
        text_frame = getattr(self, "task_link_preview_text_frame", None)
        if icon_canvas is None or text_frame is None or not icon_canvas.winfo_exists() or not text_frame.winfo_exists():
            return

        for child in text_frame.winfo_children():
            child.destroy()

        icon_canvas.delete("all")
        selected_label = self.task_character_var.get().strip()
        character_key = self.task_character_option_map.get(selected_label, "")
        row = self.find_character_row(character_key) if character_key else None
        border = get_color_border(row.get("Color", "") if row else "")
        preview_box = centered_ratio_box(84, 110, 4)
        image_box = inset_box(preview_box, 2)
        image_width, image_height = box_size(image_box)
        center_x, center_y = box_center(image_box)
        icon_canvas.create_rectangle(*preview_box, outline=border, fill=PLACEHOLDER_FILL, width=1)

        if row is not None:
            image = self.get_summary_image(row.get("Icon", ""), image_width, image_height)
            if image is not None:
                icon_canvas.create_image(center_x, center_y, image=image)
                icon_canvas.image = image  # type: ignore[attr-defined]
            else:
                icon_canvas.create_text(center_x, center_y, text="No icon", fill=TEXT_MUTED, font=self.body_font)
            icon_canvas.configure(cursor="hand2")
            icon_canvas.bind("<Button-1>", lambda _event, current=row: self.open_character_popup(current))
        else:
            icon_canvas.image = None  # type: ignore[attr-defined]
            icon_canvas.create_text(center_x, center_y, text="No link", fill=TEXT_MUTED, font=self.body_font)
            icon_canvas.configure(cursor="")
            icon_canvas.unbind("<Button-1>")

        title = self._task_character_summary(row)
        subtitle = "Click the icon to open the character details popup." if row is not None else "Link a character to keep the goal connected to your roster."
        tk.Label(text_frame, text=title, bg=SURFACE, fg=TEXT, font=self.card_title_font, anchor="w", justify="left", wraplength=260).pack(anchor="w")
        tk.Label(text_frame, text=subtitle, bg=SURFACE, fg=TEXT_MUTED, font=self.body_font, anchor="w", justify="left", wraplength=260).pack(anchor="w", pady=(6, 0))

    def _build_tasks_tab(self) -> None:
        self.tasks_tab.columnconfigure(0, weight=3)
        self.tasks_tab.columnconfigure(1, weight=2)
        self.tasks_tab.rowconfigure(0, weight=1)

        self.tasks_summary_panel = self._make_panel(self.tasks_tab)
        self.tasks_summary_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 16))
        self.tasks_summary_panel.columnconfigure(0, weight=1)
        self.tasks_summary_panel.rowconfigure(1, weight=1)

        summary_header = tk.Frame(self.tasks_summary_panel, bg=SURFACE)
        summary_header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 12))
        summary_header.columnconfigure(0, weight=1)

        tk.Label(summary_header, text="Goals", bg=SURFACE, fg=TEXT, font=self.section_font).grid(row=0, column=0, sticky="w")
        tk.Label(summary_header, textvariable=self.task_summary_var, bg=SURFACE, fg=TEXT_MUTED, font=self.body_font).grid(row=1, column=0, sticky="w", pady=(4, 0))

        list_wrap = tk.Frame(self.tasks_summary_panel, bg=SURFACE)
        list_wrap.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))
        list_wrap.columnconfigure(0, weight=1)
        list_wrap.rowconfigure(0, weight=1)

        self.tasks_list_canvas = tk.Canvas(list_wrap, bg=SURFACE, highlightthickness=0, bd=0)
        self.tasks_list_canvas.grid(row=0, column=0, sticky="nsew")
        tasks_scroll = ttk.Scrollbar(list_wrap, orient="vertical", command=self.tasks_list_canvas.yview)
        tasks_scroll.grid(row=0, column=1, sticky="ns")
        self.tasks_list_canvas.configure(yscrollcommand=tasks_scroll.set)

        self.tasks_list_container = tk.Frame(self.tasks_list_canvas, bg=SURFACE)
        self.tasks_list_window = self.tasks_list_canvas.create_window((0, 0), window=self.tasks_list_container, anchor="nw")
        self.tasks_list_container.bind(
            "<Configure>",
            lambda _event: self.tasks_list_canvas.configure(scrollregion=self.tasks_list_canvas.bbox("all")),
        )
        self.tasks_list_canvas.bind(
            "<Configure>",
            lambda event: self.tasks_list_canvas.itemconfigure(self.tasks_list_window, width=event.width),
        )
        self._bind_mousewheel(self.tasks_list_canvas, self.tasks_list_container)

        self.tasks_editor_panel = self._make_panel(self.tasks_tab)
        self.tasks_editor_panel.grid(row=0, column=1, sticky="nsew")
        self.tasks_editor_panel.columnconfigure(0, weight=1)

        editor_header = tk.Frame(self.tasks_editor_panel, bg=SURFACE)
        editor_header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 8))
        editor_header.columnconfigure(0, weight=1)
        tk.Label(editor_header, textvariable=self.task_title_var, bg=SURFACE, fg=TEXT, font=self.section_font).grid(row=0, column=0, sticky="w")
        tk.Label(
            editor_header,
            text="Track urgent goals, slower goals, and completed goals in one place. Link goals to characters when they depend on specific units.",
            bg=SURFACE,
            fg=TEXT_MUTED,
            font=self.body_font,
            wraplength=420,
            justify="left",
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

        self.task_action_bar = tk.Frame(self.tasks_editor_panel, bg=SURFACE)
        self.task_action_bar.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 8))
        self.render_task_action_bar()

        form_card = tk.Frame(self.tasks_editor_panel, bg=SURFACE_MUTED, highlightthickness=1, highlightbackground=BORDER, bd=0, padx=18, pady=18)
        form_card.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 12))
        for column in range(2):
            form_card.columnconfigure(column, weight=1)

        tk.Label(form_card, text="Goal Details", bg=SURFACE_MUTED, fg=TEXT, font=self.section_font).grid(row=0, column=0, columnspan=2, sticky="w")
        self._make_combobox(form_card, "Urgency", self.task_urgency_var, TASK_URGENCY_OPTIONS, 1, 0, columnspan=2)
        self.task_character_picker = self._make_combobox(
            form_card,
            "Linked Character",
            self.task_character_var,
            tuple(self.task_character_option_map.keys()),
            2,
            0,
            columnspan=2,
            on_select=self._on_task_character_selected,
        )

        body_field = tk.Frame(form_card, bg=SURFACE_MUTED)
        body_field.grid(row=3, column=0, columnspan=2, sticky="ew", padx=10, pady=8)
        body_field.columnconfigure(0, weight=1)
        tk.Label(body_field, text="Body", bg=SURFACE_MUTED, fg=TEXT_MUTED, font=self.label_font).grid(row=0, column=0, sticky="w")
        body_shell = tk.Frame(body_field, bg=SURFACE, highlightthickness=1, highlightbackground=BORDER, highlightcolor=PRIMARY, bd=0)
        body_shell.grid(row=1, column=0, sticky="ew", pady=(6, 0))
        body_shell.columnconfigure(0, weight=1)
        self.task_body_text = tk.Text(
            body_shell,
            height=9,
            wrap="word",
            bg=SURFACE,
            fg=TEXT,
            relief="flat",
            bd=0,
            insertbackground=TEXT,
            font=self.body_font,
            padx=10,
            pady=10,
        )
        self.task_body_text.grid(row=0, column=0, sticky="ew")
        body_scroll = ttk.Scrollbar(body_shell, orient="vertical", command=self.task_body_text.yview)
        body_scroll.grid(row=0, column=1, sticky="ns")
        self.task_body_text.configure(yscrollcommand=body_scroll.set)

        tk.Label(
            form_card,
            text="Urgent goals stay at the top in red, not urgent goals stay in yellow, and completed goals move to green at the bottom.",
            bg=SURFACE_MUTED,
            fg=TEXT_MUTED,
            font=self.body_font,
            justify="left",
            wraplength=420,
        ).grid(row=4, column=0, columnspan=2, sticky="w", padx=10, pady=(8, 0))

        link_card = tk.Frame(self.tasks_editor_panel, bg=SURFACE, highlightthickness=1, highlightbackground=BORDER, bd=0, padx=18, pady=18)
        link_card.grid(row=3, column=0, sticky="ew", padx=16, pady=(0, 16))
        link_card.columnconfigure(1, weight=1)
        tk.Label(link_card, text="Linked Character", bg=SURFACE, fg=TEXT, font=self.section_font).grid(row=0, column=0, columnspan=2, sticky="w")
        self.task_link_preview_icon_canvas = tk.Canvas(link_card, width=84, height=110, bg=SURFACE, highlightthickness=0, bd=0)
        self.task_link_preview_icon_canvas.grid(row=1, column=0, sticky="nw", pady=(14, 0))
        self.task_link_preview_text_frame = tk.Frame(link_card, bg=SURFACE)
        self.task_link_preview_text_frame.grid(row=1, column=1, sticky="nsew", padx=(14, 0), pady=(14, 0))

        self.refresh_task_character_picker_options()
        self._render_task_link_preview()

    def render_task_action_bar(self) -> None:
        for child in self.task_action_bar.winfo_children():
            child.destroy()

        if self.selected_task_index is None:
            self.task_action_bar.columnconfigure(0, weight=0)
            self.task_action_bar.columnconfigure(1, weight=1)
            self._make_button(self.task_action_bar, "New Goal", self.clear_task_form, filled=False).grid(row=0, column=0, padx=(0, 10), sticky="w")
            self._make_button(self.task_action_bar, "Create Goal", self.create_task, filled=True).grid(row=0, column=1, sticky="e")
        else:
            for column in range(5):
                self.task_action_bar.columnconfigure(column, weight=0 if column != 3 else 1)
            self._make_button(self.task_action_bar, "New Goal", self.clear_task_form, filled=False).grid(row=0, column=0, padx=(0, 10), sticky="w")
            self._make_button(self.task_action_bar, "Mark Urgent", self.mark_task_urgent, filled=False).grid(row=0, column=1, padx=(0, 10), sticky="w")
            self._make_button(self.task_action_bar, "Mark Completed", self.mark_task_completed, filled=False).grid(row=0, column=2, padx=(0, 10), sticky="w")
            self._make_button(self.task_action_bar, "Update Goal", self.update_task, filled=True).grid(row=0, column=3, sticky="e")
            self._make_button(self.task_action_bar, "Delete Goal", self.delete_task, filled=True, bg=DANGER, active_bg="#B71C1C").grid(row=0, column=4, padx=(10, 0), sticky="e")

    def refresh_tasks_list(self, select_index: int | None) -> None:
        container = getattr(self, "tasks_list_container", None)
        if container is None or not container.winfo_exists():
            return

        for child in container.winfo_children():
            child.destroy()

        if select_index is not None and 0 <= select_index < len(self.tasks):
            self.selected_task_index = select_index
        elif self.selected_task_index is None or not (0 <= self.selected_task_index < len(self.tasks)):
            self.selected_task_index = None

        if not self.tasks:
            empty = tk.Frame(container, bg=SURFACE, pady=48)
            empty.pack(fill="x")
            tk.Label(empty, text="No goals yet", bg=SURFACE, fg=TEXT, font=self.section_font).pack()
            tk.Label(empty, text="Create the first goal to start tracking progress.", bg=SURFACE, fg=TEXT_MUTED, font=self.body_font).pack(pady=(6, 0))
            self._bind_mousewheel(self.tasks_list_canvas, empty)
            self.selected_task_index = None
            return

        filtered_tasks = self.get_filtered_tasks()
        if not filtered_tasks:
            empty = tk.Frame(container, bg=SURFACE, pady=48)
            empty.pack(fill="x")
            tk.Label(empty, text="No goals available", bg=SURFACE, fg=TEXT, font=self.section_font).pack()
            tk.Label(empty, text="Create a goal to populate this list.", bg=SURFACE, fg=TEXT_MUTED, font=self.body_font).pack(pady=(6, 0))
            self._bind_mousewheel(self.tasks_list_canvas, empty)
            return

        for index, task in filtered_tasks:
            self._add_task_card(index, task, index == self.selected_task_index)

    def _add_task_card(self, index: int, task: dict[str, str], selected: bool) -> None:
        urgency = canonical_task_urgency(task.get("urgency", ""))
        accent = TASK_URGENCY_ACCENTS.get(urgency, PRIMARY)
        accent_bg = TASK_URGENCY_BACKGROUNDS.get(urgency, PRIMARY_SOFT)
        bg = PRIMARY_SOFT if selected else SURFACE
        border = accent if selected else BORDER
        card = tk.Frame(self.tasks_list_container, bg=bg, highlightthickness=1, highlightbackground=border, bd=0, padx=14, pady=12, cursor="hand2")
        card.pack(fill="x", padx=4, pady=6)
        card.columnconfigure(0, weight=1)
        card.columnconfigure(1, weight=0)

        badge = tk.Label(card, text=urgency, bg=accent_bg, fg=accent, font=self.label_font, padx=10, pady=4)
        badge.grid(row=0, column=0, sticky="w")

        title = tk.Label(card, text=self._task_primary_line(task.get("body", "")), bg=bg, fg=TEXT, font=self.card_title_font, anchor="w", justify="left", wraplength=520)
        title.grid(row=1, column=0, sticky="ew", pady=(10, 4))

        summary = tk.Label(card, text=self._task_secondary_line(task.get("body", "")), bg=bg, fg=TEXT_MUTED, font=self.body_font, anchor="w", justify="left", wraplength=640)
        summary.grid(row=2, column=0, sticky="ew")

        link_row = tk.Frame(card, bg=bg)
        link_row.grid(row=3, column=0, sticky="ew", pady=(10, 0))
        link_row.columnconfigure(1, weight=1)

        character_row = self._task_character_row(task)
        icon_canvas = tk.Canvas(link_row, width=56, height=72, bg=bg, highlightthickness=0, bd=0)
        icon_canvas.grid(row=0, column=0, sticky="nw")
        preview_box = centered_ratio_box(56, 72, 4)
        image_box = inset_box(preview_box, 2)
        image_width, image_height = box_size(image_box)
        center_x, center_y = box_center(image_box)
        icon_border = get_color_border(character_row.get("Color", "") if character_row else "")
        icon_canvas.create_rectangle(*preview_box, outline=icon_border, fill=PLACEHOLDER_FILL, width=1)

        if character_row is not None:
            image = self.get_summary_image(character_row.get("Icon", ""), image_width, image_height)
            if image is not None:
                icon_canvas.create_image(center_x, center_y, image=image)
                icon_canvas.image = image  # type: ignore[attr-defined]
            else:
                icon_canvas.create_text(center_x, center_y, text="No icon", fill=TEXT_MUTED, font=self.card_meta_font)
            icon_canvas.configure(cursor="hand2")
            icon_canvas.bind("<Button-1>", lambda _event, current=character_row: self.open_character_popup(current))
        else:
            icon_canvas.create_text(center_x, center_y, text="No\nlink", fill=TEXT_MUTED, font=self.card_meta_font, justify="center")

        link_text = tk.Frame(link_row, bg=bg)
        link_text.grid(row=0, column=1, sticky="nsew", padx=(12, 0))
        tk.Label(link_text, text="Linked Character", bg=bg, fg=TEXT_MUTED, font=self.label_font, anchor="w").pack(anchor="w")
        tk.Label(link_text, text=self._task_character_summary(character_row), bg=bg, fg=TEXT, font=self.card_meta_font, anchor="w", justify="left", wraplength=540).pack(anchor="w", pady=(4, 0))

        self._bind_mousewheel(self.tasks_list_canvas, card, badge, title, summary, link_row, link_text, icon_canvas)
        for widget in (card, badge, title, summary, link_row, link_text):
            widget.bind("<Button-1>", lambda _event, idx=index: self.select_task(idx))
        for child in link_text.winfo_children():
            child.bind("<Button-1>", lambda _event, idx=index: self.select_task(idx))

    def refresh_tasks_tab_visuals(self) -> None:
        self.refresh_task_character_picker_options()
        self.refresh_tasks_list(select_index=self.selected_task_index)
        self._render_task_link_preview()

    def on_task_filter_changed(self, _event: tk.Event | None = None) -> None:
        self.refresh_tasks_list(select_index=self.selected_task_index)
        self.update_task_summary()
        self.status_var.set("Updated goals view.")

    def collect_task_data(self) -> dict[str, str]:
        return {
            "task_type": TASK_TYPE_OPTIONS[0],
            "body": self._task_body_text(),
            "urgency": self.task_urgency_var.get().strip(),
            "character_key": self.task_character_var.get().strip(),
        }

    def prepare_task_for_save(self) -> dict[str, str]:
        payload = self.collect_task_data()
        body = str(payload.get("body", "") or "").strip()
        if not body:
            raise ValueError("Goal body is required.")
        urgency = canonical_task_urgency(payload.get("urgency", ""))
        selected_character = str(payload.get("character_key", "") or "").strip()
        character_key = self.task_character_option_map.get(selected_character, "")
        return {
            "task_type": TASK_TYPE_OPTIONS[0],
            "body": body,
            "urgency": urgency,
            "character_key": character_key,
        }

    def save_tasks(self) -> None:
        current_index = self.selected_task_index
        self.sort_tasks()
        self.task_repository.save(self.tasks)
        self.update_task_summary()
        self.refresh_tasks_list(select_index=current_index)
        self._render_task_link_preview()

    def load_tasks(self, select_index: int | None) -> None:
        try:
            self.tasks = self.task_repository.load()
        except Exception as exc:
            messagebox.showerror("Load failed", f"Unable to load goals:\n{exc}")
            self.tasks = []
            self.status_var.set("Failed to load goals.")
            return

        self.sort_tasks()
        self.refresh_task_character_picker_options()
        self.update_task_summary()
        self.refresh_tasks_list(select_index=select_index)
        self.render_task_action_bar()
        if select_index is None or not self.tasks:
            self.clear_task_form(keep_status=True, refresh_list=False)
        else:
            self.select_task(min(select_index, len(self.tasks) - 1))
        self.status_var.set(f"Loaded {len(self.tasks)} goal(s) from {self.tasks_path.name}.")

    def select_task(self, index: int) -> None:
        if not (0 <= index < len(self.tasks)):
            return
        self.selected_task_index = index
        task = self.tasks[index]
        self.task_urgency_var.set(canonical_task_urgency(task.get("urgency", "")))
        self.task_character_var.set(self._task_character_label_from_key(task.get("character_key", "")))
        self._set_task_body_text(task.get("body", ""))
        self.task_title_var.set(self._task_primary_line(task.get("body", "")))
        self.refresh_tasks_list(select_index=index)
        self.render_task_action_bar()
        self._render_task_link_preview()
        self.status_var.set(f"Selected goal #{index + 1}.")

    def clear_task_form(self, keep_status: bool = False, refresh_list: bool = True) -> None:
        self.selected_task_index = None
        self.task_urgency_var.set(TASK_URGENCY_NOT_URGENT)
        self.task_character_var.set("No linked character")
        self._set_task_body_text("")
        self.task_title_var.set("New Goal")
        if refresh_list:
            self.refresh_tasks_list(select_index=None)
        self.render_task_action_bar()
        self._render_task_link_preview()
        if not keep_status:
            self.status_var.set("Goal form cleared. Ready for a new goal.")

    def create_task(self) -> None:
        previous_tasks = self.clone_tasks()
        try:
            task = self.prepare_task_for_save()
            self.tasks.append(task)
            self.save_tasks()
        except Exception as exc:
            self.tasks = previous_tasks
            messagebox.showerror("Create failed", str(exc))
            self.status_var.set("Unable to create goal.")
            return

        new_index = next((idx for idx, existing in enumerate(self.tasks) if existing == task), len(self.tasks) - 1)
        self.select_task(new_index)
        self.status_var.set("Created goal.")

    def update_task(self) -> None:
        if self.selected_task_index is None:
            messagebox.showwarning("No selection", "Select a goal from the list first.")
            return

        previous_tasks = self.clone_tasks()
        index = self.selected_task_index
        try:
            task = self.prepare_task_for_save()
            self.tasks[index] = task
            self.save_tasks()
        except Exception as exc:
            self.tasks = previous_tasks
            messagebox.showerror("Update failed", str(exc))
            self.status_var.set("Unable to update goal.")
            return

        updated_index = next((idx for idx, existing in enumerate(self.tasks) if existing == task), index)
        self.select_task(updated_index)
        self.status_var.set("Updated goal.")

    def delete_task(self) -> None:
        if self.selected_task_index is None:
            messagebox.showwarning("No selection", "Select a goal from the list first.")
            return

        index = self.selected_task_index
        task = self.tasks[index]
        title = self._task_primary_line(task.get("body", ""))
        confirmed = messagebox.askyesno("Delete goal", f"Delete '{title}'?")
        if not confirmed:
            return

        previous_tasks = self.clone_tasks()
        self.tasks.pop(index)
        try:
            self.save_tasks()
        except Exception as exc:
            self.tasks = previous_tasks
            messagebox.showerror("Delete failed", str(exc))
            self.status_var.set("Unable to delete goal.")
            return

        if self.tasks:
            self.select_task(min(index, len(self.tasks) - 1))
        else:
            self.clear_task_form(keep_status=True)
        self.status_var.set(f"Deleted goal: {title}")

    def _set_selected_task_urgency(self, urgency: str) -> None:
        if self.selected_task_index is None:
            messagebox.showwarning("No selection", "Select a goal from the list first.")
            return

        previous_tasks = self.clone_tasks()
        task = self.tasks[self.selected_task_index].copy()
        task["urgency"] = canonical_task_urgency(urgency)
        self.tasks[self.selected_task_index] = task
        try:
            self.save_tasks()
        except Exception as exc:
            self.tasks = previous_tasks
            messagebox.showerror("Update failed", str(exc))
            self.status_var.set("Unable to update goal urgency.")
            return

        updated_index = next((idx for idx, existing in enumerate(self.tasks) if existing == task), self.selected_task_index)
        self.select_task(updated_index)
        self.status_var.set(f"Marked goal as {task['urgency'].lower()}.")

    def mark_task_urgent(self) -> None:
        self._set_selected_task_urgency(TASK_URGENCY_URGENT)

    def mark_task_completed(self) -> None:
        self._set_selected_task_urgency(TASK_URGENCY_COMPLETED)

    def rename_character_in_tasks(self, previous_row: dict[str, str], new_row: dict[str, str]) -> None:
        old_key = character_version_key(previous_row)
        new_key = character_version_key(new_row)
        if not old_key or not new_key or old_key == new_key:
            return

        for task in self.tasks:
            linked_key = str(task.get("character_key", "") or "").strip()
            if not linked_key:
                continue
            linked_row = self.find_character_row(linked_key)
            if self.rows_match_assignment(previous_row, linked_row, old_key, linked_key):
                task["character_key"] = new_key

    def get_character_task_usage(self, character_name: str) -> list[str]:
        target_row = self.find_character_row(character_name)
        if target_row is None and not str(character_name or "").strip():
            return []

        usage: list[str] = []
        for task in self.tasks:
            linked_key = str(task.get("character_key", "") or "").strip()
            if not linked_key:
                continue
            linked_row = self.find_character_row(linked_key)
            if self.rows_match_assignment(target_row, linked_row, character_name, linked_key):
                usage.append(self._task_primary_line(task.get("body", "")))
        return usage

    def refresh_task_links_after_character_data_change(self) -> None:
        self.refresh_task_character_picker_options()
        if hasattr(self, "tasks_list_container") and self.tasks_list_container.winfo_exists():
            self.refresh_tasks_list(select_index=self.selected_task_index)
            self._render_task_link_preview()

    def on_character_rows_loaded(self) -> None:
        self.refresh_task_links_after_character_data_change()

    def on_character_created(self) -> None:
        self.refresh_task_links_after_character_data_change()

    def on_character_updated(self, previous_row: dict[str, str], new_row: dict[str, str]) -> None:
        previous_tasks = self.clone_tasks()
        try:
            self.rename_character_in_tasks(previous_row, new_row)
            self.task_repository.save(self.tasks)
        except Exception as exc:
            self.tasks = previous_tasks
            messagebox.showerror("Goal link update failed", f"Updated the character, but goal links could not be synchronized:\n{exc}")
        self.refresh_task_links_after_character_data_change()

    def ensure_character_can_be_deleted_for_tasks(self, row: dict[str, str]) -> bool:
        usage = self.get_character_task_usage(character_version_key(row))
        if not usage:
            return True
        messagebox.showwarning(
            "Character linked to goals",
            "Remove this character from the following goal(s) before deleting it:\n" + "\n".join(usage),
        )
        return False

    def on_character_deleted(self) -> None:
        self.refresh_task_links_after_character_data_change()

    def _on_task_character_selected(self) -> None:
        self._render_task_link_preview()
