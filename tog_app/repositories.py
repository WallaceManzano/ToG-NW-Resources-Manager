from __future__ import annotations

import json
from pathlib import Path

from .constants import DEFAULT_HEADERS, FORMATION_SLOT_ORDER, TEAM_OPTIONS
from .helpers import empty_team_map


class CharacterRepository:
    def __init__(self, json_path: Path) -> None:
        self.json_path = json_path
        self.headers = list(DEFAULT_HEADERS)

    def ensure_file(self) -> None:
        if self.json_path.exists():
            return
        self.json_path.parent.mkdir(parents=True, exist_ok=True)
        with self.json_path.open("w", encoding="utf-8") as json_file:
            json.dump({"headers": self.headers, "rows": []}, json_file, indent=2)

    def load(self) -> list[dict[str, str]]:
        self.ensure_file()
        with self.json_path.open("r", encoding="utf-8-sig") as json_file:
            payload = json.load(json_file)

        if isinstance(payload, dict):
            file_headers = payload.get("headers", [])
            raw_rows = payload.get("rows", [])
        elif isinstance(payload, list):
            file_headers = self.headers
            raw_rows = payload
        else:
            file_headers = self.headers
            raw_rows = []

        if isinstance(file_headers, list) and file_headers:
            self.headers = [
                "IW Type" if str(header) == "Type" else str(header)
                for header in file_headers
            ]
        else:
            self.headers = list(DEFAULT_HEADERS)

        rows: list[dict[str, str]] = []
        if isinstance(raw_rows, list):
            for row in raw_rows:
                if not isinstance(row, dict):
                    continue
                normalized = {
                    header: str(
                        row.get(header, row.get("Type", "") if header == "IW Type" else "")
                        or ""
                    ).strip()
                    for header in self.headers
                }
                if any(normalized.values()):
                    rows.append(normalized)

        self.headers = list(DEFAULT_HEADERS)
        return rows

    def save(self, rows: list[dict[str, str]]) -> None:
        self.json_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "headers": self.headers,
            "rows": [
                {header: str(row.get(header, "") or "") for header in self.headers}
                for row in rows
            ],
        }
        with self.json_path.open("w", encoding="utf-8") as json_file:
            json.dump(payload, json_file, indent=2)


class FormationRepository:
    def __init__(self, json_path: Path) -> None:
        self.json_path = json_path

    def ensure_file(self) -> None:
        if self.json_path.exists():
            return
        self.json_path.parent.mkdir(parents=True, exist_ok=True)
        self.save([])

    def load(self) -> list[dict[str, object]]:
        self.ensure_file()
        with self.json_path.open("r", encoding="utf-8-sig") as json_file:
            raw_data = json.load(json_file)

        if not isinstance(raw_data, list):
            return []

        formations: list[dict[str, object]] = []
        for entry in raw_data:
            if not isinstance(entry, dict):
                continue

            normalized_teams = empty_team_map()
            raw_teams = entry.get("teams")
            if isinstance(raw_teams, dict):
                for team_name in TEAM_OPTIONS:
                    team_slots = raw_teams.get(team_name, {})
                    normalized_teams[team_name] = {
                        slot_key: str(team_slots.get(slot_key, "") or "").strip()
                        for slot_key in FORMATION_SLOT_ORDER
                    }
            else:
                legacy_team_name = (
                    str(entry.get("team_name", "") or TEAM_OPTIONS[0]).strip()
                    or TEAM_OPTIONS[0]
                )
                legacy_slots = entry.get("slots", {})
                normalized_teams[legacy_team_name] = {
                    slot_key: str(legacy_slots.get(slot_key, "") or "").strip()
                    for slot_key in FORMATION_SLOT_ORDER
                }

            formations.append(
                {
                    "formation_name": str(entry.get("formation_name", "") or "").strip(),
                    "teams": normalized_teams,
                }
            )
        return formations

    def save(self, formations: list[dict[str, object]]) -> None:
        self.json_path.parent.mkdir(parents=True, exist_ok=True)
        payload = []
        for entry in formations:
            teams = entry.get("teams", {})
            payload.append(
                {
                    "formation_name": str(entry.get("formation_name", "") or "").strip(),
                    "teams": {
                        team_name: {
                            slot_key: str(
                                teams.get(team_name, {}).get(slot_key, "") or ""
                            ).strip()
                            for slot_key in FORMATION_SLOT_ORDER
                        }
                        for team_name in TEAM_OPTIONS
                    },
                }
            )

        with self.json_path.open("w", encoding="utf-8") as json_file:
            json.dump(payload, json_file, indent=2)
