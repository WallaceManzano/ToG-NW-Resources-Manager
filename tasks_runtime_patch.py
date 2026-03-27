from __future__ import annotations

import json
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk


TASK_TYPE_OPTIONS = ("Goal",)
TASK_FILTER_ALL = "All Goals"
TASK_FILTER_OPTIONS = (TASK_FILTER_ALL,)
TASK_URGENCY_URGENT = "Urgent"
TASK_URGENCY_NOT_URGENT = "Not Urgent"
TASK_URGENCY_COMPLETED = "Completed"
TASK_URGENCY_OPTIONS = (
    TASK_URGENCY_URGENT,
    TASK_URGENCY_NOT_URGENT,
    TASK_URGENCY_COMPLETED,
)
TASK_URGENCY_ORDER = {
    TASK_URGENCY_URGENT: 0,
    TASK_URGENCY_NOT_URGENT: 1,
    TASK_URGENCY_COMPLETED: 2,
}
TASK_URGENCY_ACCENTS = {
    TASK_URGENCY_URGENT: "#C62828",
    TASK_URGENCY_NOT_URGENT: "#F9A825",
    TASK_URGENCY_COMPLETED: "#2E7D32",
}
TASK_URGENCY_BACKGROUNDS = {
    TASK_URGENCY_URGENT: "#FDECEC",
    TASK_URGENCY_NOT_URGENT: "#FFF8E1",
    TASK_URGENCY_COMPLETED: "#EAF7ED",
}


def canonical_task_type(value: str) -> str:
    return TASK_TYPE_OPTIONS[0]


def canonical_task_urgency(value: str) -> str:
    cleaned = " ".join(str(value or "").strip().split())
    if not cleaned:
        return TASK_URGENCY_NOT_URGENT
    normalized = cleaned.casefold()
    aliases = {
        TASK_URGENCY_URGENT.casefold(): TASK_URGENCY_URGENT,
        TASK_URGENCY_NOT_URGENT.casefold(): TASK_URGENCY_NOT_URGENT,
        TASK_URGENCY_COMPLETED.casefold(): TASK_URGENCY_COMPLETED,
        "non urgent": TASK_URGENCY_NOT_URGENT,
        "normal": TASK_URGENCY_NOT_URGENT,
        "done": TASK_URGENCY_COMPLETED,
    }
    return aliases.get(normalized, TASK_URGENCY_NOT_URGENT)


def truncate_task_text(value: str, max_length: int) -> str:
    cleaned = " ".join(str(value or "").strip().split())
    if len(cleaned) <= max_length:
        return cleaned
    return cleaned[: max(0, max_length - 3)].rstrip() + "..."


class TaskRepository:
    def __init__(self, json_path: Path) -> None:
        self.json_path = json_path

    def ensure_file(self) -> None:
        if self.json_path.exists():
            return
        self.json_path.parent.mkdir(parents=True, exist_ok=True)
        self.save([])

    def build_payload(self, tasks: list[dict[str, str]]) -> dict[str, object]:
        return {
            "tasks": [
                {
                    "task_type": canonical_task_type(task.get("task_type", "")),
                    "body": str(task.get("body", "") or "").strip(),
                    "urgency": canonical_task_urgency(task.get("urgency", "")),
                    "character_key": str(task.get("character_key", "") or "").strip(),
                }
                for task in tasks
                if str(task.get("body", "") or "").strip()
            ]
        }

    def _write_payload(self, payload: dict[str, object]) -> None:
        with self.json_path.open("w", encoding="utf-8") as json_file:
            json.dump(payload, json_file, indent=2)

    def load(self) -> list[dict[str, str]]:
        self.ensure_file()
        with self.json_path.open("r", encoding="utf-8-sig") as json_file:
            payload = json.load(json_file)

        if isinstance(payload, dict):
            raw_tasks = payload.get("tasks", [])
        elif isinstance(payload, list):
            raw_tasks = payload
        else:
            raw_tasks = []

        tasks: list[dict[str, str]] = []
        if isinstance(raw_tasks, list):
            for entry in raw_tasks:
                if not isinstance(entry, dict):
                    continue
                body = str(entry.get("body", "") or "").strip()
                if not body:
                    continue
                tasks.append(
                    {
                        "task_type": canonical_task_type(str(entry.get("task_type", "") or entry.get("type", "") or "")),
                        "body": body,
                        "urgency": canonical_task_urgency(str(entry.get("urgency", "") or "")),
                        "character_key": str(entry.get("character_key", "") or entry.get("character", "") or "").strip(),
                    }
                )

        expected_payload = self.build_payload(tasks)
        if payload != expected_payload:
            self._write_payload(expected_payload)
        return tasks

    def save(self, tasks: list[dict[str, str]]) -> None:
        self.json_path.parent.mkdir(parents=True, exist_ok=True)
        self._write_payload(self.build_payload(tasks))


def apply_tasks_runtime_patch() -> None:
    from tog_app import repositories
    from tog_app.app_window import TogCharacterManager
    from tog_app.constants import (
        BACKGROUND,
        BASE_DIR,
        BORDER,
        DANGER,
        PLACEHOLDER_FILL,
        PREVIEW_ICON_HEIGHT,
        PREVIEW_ICON_WIDTH,
        PRIMARY,
        PRIMARY_DARK,
        PRIMARY_SOFT,
        SURFACE,
        SURFACE_MUTED,
        TEXT,
        TEXT_MUTED,
    )
    from tog_app.helpers import (
        box_center,
        box_size,
        canonical_character_version_key,
        centered_ratio_box,
        character_display_name,
        character_version_key,
        display_color_value,
        get_color_border,
        inset_box,
        normalize_character_name,
    )

    if getattr(TogCharacterManager, "_tasks_runtime_patch_applied", False):
        return

    repositories.TaskRepository = TaskRepository
    default_tasks_path = BASE_DIR / "db" / "tasks.json"

    original_app_init = TogCharacterManager.__init__
    original_build_layout = TogCharacterManager._build_layout
    original_on_tab_changed = TogCharacterManager.on_tab_changed
    original_load_rows = TogCharacterManager.load_rows
    original_create_row = TogCharacterManager.create_row
    original_update_row = TogCharacterManager.update_row
    original_delete_row = TogCharacterManager.delete_row

    def _ensure_tasks_state(self) -> None:
        if getattr(self, "_tasks_state_ready", False):
            return
        self.tasks_path = default_tasks_path
        self.task_repository = TaskRepository(self.tasks_path)
        self.tasks = []
        self.task_summary_var = tk.StringVar(value="0 goals")
        self.task_title_var = tk.StringVar(value="New Goal")
        self.task_type_var = tk.StringVar(value=TASK_TYPE_OPTIONS[0])
        self.task_filter_var = tk.StringVar(value=TASK_FILTER_OPTIONS[0])
        self.task_urgency_var = tk.StringVar(value=TASK_URGENCY_NOT_URGENT)
        self.task_character_var = tk.StringVar(value="No linked character")
        self.selected_task_index = None
        self.task_character_option_map = {"No linked character": ""}
        self.task_body_text = None
        self.task_character_picker = None
        self.task_link_preview_icon_canvas = None
        self.task_link_preview_text_frame = None
        self._tasks_state_ready = True

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

    def _task_matches_filter(self, task: dict[str, str]) -> bool:
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
        self._ensure_tasks_state()
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

    def _build_layout(self) -> None:
        self._ensure_tasks_state()
        original_build_layout(self)
        if not hasattr(self, "tasks_tab") or not self.tasks_tab.winfo_exists():
            self.tasks_tab = tk.Frame(self.notebook, bg=BACKGROUND)
            self.notebook.insert(0, self.tasks_tab, text="Goals")
            self._build_tasks_tab()
            self.notebook.select(self.tasks_tab)

    def __init__(self) -> None:
        original_app_init(self)
        self._ensure_tasks_state()
        self.load_tasks(select_index=None)

    def on_tab_changed(self, event: tk.Event | None = None) -> None:
        selected_tab = self.notebook.select() if hasattr(self, "notebook") else ""
        if hasattr(self, "tasks_tab") and selected_tab == str(self.tasks_tab):
            self.after_idle(self.refresh_tasks_tab_visuals)
        original_on_tab_changed(self, event)

    def load_rows(self, select_index: int | None) -> None:
        original_load_rows(self, select_index)
        if getattr(self, "_tasks_state_ready", False):
            self.refresh_task_character_picker_options()
            if hasattr(self, "tasks_list_container") and self.tasks_list_container.winfo_exists():
                self.refresh_tasks_list(select_index=self.selected_task_index)
                self._render_task_link_preview()

    def create_row(self) -> None:
        previous_count = len(self.rows)
        original_create_row(self)
        if len(self.rows) != previous_count:
            self.refresh_task_character_picker_options()
            self.refresh_tasks_list(select_index=self.selected_task_index)
            self._render_task_link_preview()

    def update_row(self) -> None:
        previous_row = self.rows[self.selected_index].copy() if self.selected_index is not None and 0 <= self.selected_index < len(self.rows) else None
        previous_tasks = self.clone_tasks()
        original_update_row(self)
        if previous_row is None or self.selected_index is None or not (0 <= self.selected_index < len(self.rows)):
            self.refresh_task_character_picker_options()
            self.refresh_tasks_list(select_index=self.selected_task_index)
            self._render_task_link_preview()
            return
        try:
            self.rename_character_in_tasks(previous_row, self.rows[self.selected_index])
            self.task_repository.save(self.tasks)
        except Exception as exc:
            self.tasks = previous_tasks
            messagebox.showerror("Goal link update failed", f"Updated the character, but goal links could not be synchronized:\n{exc}")
        self.refresh_task_character_picker_options()
        self.refresh_tasks_list(select_index=self.selected_task_index)
        self._render_task_link_preview()

    def delete_row(self) -> None:
        if self.selected_index is not None and 0 <= self.selected_index < len(self.rows):
            row = self.rows[self.selected_index]
            usage = self.get_character_task_usage(character_version_key(row))
            if usage:
                messagebox.showwarning(
                    "Character linked to goals",
                    "Remove this character from the following goal(s) before deleting it:\n" + "\n".join(usage),
                )
                return
        original_delete_row(self)
        self.refresh_task_character_picker_options()
        self.refresh_tasks_list(select_index=self.selected_task_index)
        self._render_task_link_preview()

    def _on_task_character_selected(self) -> None:
        self._render_task_link_preview()

    TogCharacterManager._ensure_tasks_state = _ensure_tasks_state
    TogCharacterManager._task_body_text = _task_body_text
    TogCharacterManager._set_task_body_text = _set_task_body_text
    TogCharacterManager._task_primary_line = _task_primary_line
    TogCharacterManager._task_secondary_line = _task_secondary_line
    TogCharacterManager._task_sort_key = _task_sort_key
    TogCharacterManager.sort_tasks = sort_tasks
    TogCharacterManager.clone_tasks = clone_tasks
    TogCharacterManager.update_task_summary = update_task_summary
    TogCharacterManager._task_matches_filter = _task_matches_filter
    TogCharacterManager.get_filtered_tasks = get_filtered_tasks
    TogCharacterManager._build_task_character_options = _build_task_character_options
    TogCharacterManager.refresh_task_character_picker_options = refresh_task_character_picker_options
    TogCharacterManager._task_character_label_from_key = _task_character_label_from_key
    TogCharacterManager._task_character_row = _task_character_row
    TogCharacterManager._task_character_summary = _task_character_summary
    TogCharacterManager._render_task_link_preview = _render_task_link_preview
    TogCharacterManager._on_task_character_selected = _on_task_character_selected
    TogCharacterManager._build_tasks_tab = _build_tasks_tab
    TogCharacterManager.render_task_action_bar = render_task_action_bar
    TogCharacterManager.refresh_tasks_list = refresh_tasks_list
    TogCharacterManager._add_task_card = _add_task_card
    TogCharacterManager.refresh_tasks_tab_visuals = refresh_tasks_tab_visuals
    TogCharacterManager.on_task_filter_changed = on_task_filter_changed
    TogCharacterManager.collect_task_data = collect_task_data
    TogCharacterManager.prepare_task_for_save = prepare_task_for_save
    TogCharacterManager.save_tasks = save_tasks
    TogCharacterManager.load_tasks = load_tasks
    TogCharacterManager.select_task = select_task
    TogCharacterManager.clear_task_form = clear_task_form
    TogCharacterManager.create_task = create_task
    TogCharacterManager.update_task = update_task
    TogCharacterManager.delete_task = delete_task
    TogCharacterManager._set_selected_task_urgency = _set_selected_task_urgency
    TogCharacterManager.mark_task_urgent = mark_task_urgent
    TogCharacterManager.mark_task_completed = mark_task_completed
    TogCharacterManager.rename_character_in_tasks = rename_character_in_tasks
    TogCharacterManager.get_character_task_usage = get_character_task_usage
    TogCharacterManager._build_layout = _build_layout
    TogCharacterManager.__init__ = __init__
    TogCharacterManager.on_tab_changed = on_tab_changed
    TogCharacterManager.load_rows = load_rows
    TogCharacterManager.create_row = create_row
    TogCharacterManager.update_row = update_row
    TogCharacterManager.delete_row = delete_row
    TogCharacterManager._tasks_runtime_patch_applied = True
