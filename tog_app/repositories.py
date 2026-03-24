from __future__ import annotations

import json
from pathlib import Path

from .constants import DEFAULT_HEADERS, FORMATION_SLOT_ORDER, TEAM_OPTIONS, TOWER_TRACKED_MODES
from .helpers import (
    canonical_character_field_label,
    canonical_character_field_value,
    canonical_tower_mode_key,
    display_tower_mode_label,
    empty_team_map,
    normalize_team_entry,
    parse_int,
    storage_character_headers,
    storage_character_row,
    storage_character_version_key,
)


class CharacterRepository:
    def __init__(self, json_path: Path) -> None:
        self.json_path = json_path
        self.headers = list(DEFAULT_HEADERS)

    def ensure_file(self) -> None:
        if self.json_path.exists():
            return
        self.json_path.parent.mkdir(parents=True, exist_ok=True)
        self._write_payload(self.build_payload([]))

    def build_payload(self, rows: list[dict[str, str]]) -> dict[str, object]:
        return {
            "headers": storage_character_headers(),
            "rows": [storage_character_row(row) for row in rows],
        }

    def _write_payload(self, payload: dict[str, object]) -> None:
        with self.json_path.open("w", encoding="utf-8") as json_file:
            json.dump(payload, json_file, indent=2)

    def load(self) -> list[dict[str, str]]:
        self.ensure_file()
        with self.json_path.open("r", encoding="utf-8-sig") as json_file:
            payload = json.load(json_file)

        if isinstance(payload, dict):
            raw_rows = payload.get("rows", [])
        elif isinstance(payload, list):
            raw_rows = payload
        else:
            raw_rows = []

        rows: list[dict[str, str]] = []
        if isinstance(raw_rows, list):
            for row in raw_rows:
                if not isinstance(row, dict):
                    continue
                normalized_source = {
                    canonical_character_field_label(str(key)): canonical_character_field_value(str(key), str(value or ""))
                    for key, value in row.items()
                }
                normalized = {
                    header: normalized_source.get(header, "")
                    for header in DEFAULT_HEADERS
                }
                if any(normalized.values()):
                    rows.append(normalized)

        self.headers = list(DEFAULT_HEADERS)
        expected_payload = self.build_payload(rows)
        if payload != expected_payload:
            self._write_payload(expected_payload)
        return rows

    def save(self, rows: list[dict[str, str]]) -> None:
        self.json_path.parent.mkdir(parents=True, exist_ok=True)
        self._write_payload(self.build_payload(rows))


class FormationRepository:
    def __init__(self, json_path: Path) -> None:
        self.json_path = json_path

    def ensure_file(self) -> None:
        if self.json_path.exists():
            return
        self.json_path.parent.mkdir(parents=True, exist_ok=True)
        self.save([])

    def build_payload(self, formations: list[dict[str, object]]) -> list[dict[str, object]]:
        payload = []
        for entry in formations:
            teams = entry.get("teams", {})
            payload.append(
                {
                    "formation_name": str(entry.get("formation_name", "") or "").strip(),
                    "teams": {
                        team_name: {
                            "Note": str(
                                teams.get(team_name, {}).get("Note", "") or ""
                            ).strip(),
                            **{
                                slot_key: storage_character_version_key(
                                    str(teams.get(team_name, {}).get(slot_key, "") or "").strip()
                                )
                                for slot_key in FORMATION_SLOT_ORDER
                            },
                        }
                        for team_name in TEAM_OPTIONS
                    },
                }
            )
        return payload

    def _write_payload(self, payload: list[dict[str, object]]) -> None:
        with self.json_path.open("w", encoding="utf-8") as json_file:
            json.dump(payload, json_file, indent=2)

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
                    normalized_teams[team_name] = normalize_team_entry(
                        raw_teams.get(team_name, {})
                    )
            else:
                legacy_team_name = (
                    str(entry.get("team_name", "") or TEAM_OPTIONS[0]).strip()
                    or TEAM_OPTIONS[0]
                )
                normalized_teams[legacy_team_name] = normalize_team_entry(
                    entry.get("slots", {})
                )

            formations.append(
                {
                    "formation_name": str(entry.get("formation_name", "") or "").strip(),
                    "teams": normalized_teams,
                }
            )

        expected_payload = self.build_payload(formations)
        if raw_data != expected_payload:
            self._write_payload(expected_payload)
        return formations

    def save(self, formations: list[dict[str, object]]) -> None:
        self.json_path.parent.mkdir(parents=True, exist_ok=True)
        self._write_payload(self.build_payload(formations))


class PackRepository:
    def __init__(self, json_path: Path) -> None:
        self.json_path = json_path

    def ensure_file(self) -> None:
        if self.json_path.exists():
            return
        self.json_path.parent.mkdir(parents=True, exist_ok=True)
        self.save([], [])

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
                if any(normalized.values()):
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
            "item_bases": [
                {
                    "item_name": str(entry.get("item_name", "") or "").strip(),
                    "item_priority": str(entry.get("item_priority", "") or "").strip(),
                    "item_base_value": str(entry.get("item_base_value", "") or "").strip(),
                    "item_value": str(entry.get("item_value", "") or "").strip(),
                }
                for entry in item_bases
            ],
            "packs": [],
        }

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


class TowerProgressRepository:
    def __init__(self, json_path: Path) -> None:
        self.json_path = json_path

    def ensure_file(self) -> None:
        if self.json_path.exists():
            return
        self.json_path.parent.mkdir(parents=True, exist_ok=True)
        self.save([])

    def build_payload(self, entries: list[dict[str, object]]) -> dict[str, object]:
        payload_entries: list[dict[str, object]] = []
        for entry in entries:
            raw_floors = entry.get("floors", {})
            floors = raw_floors if isinstance(raw_floors, dict) else {}
            payload_entries.append(
                {
                    "captured_at": str(entry.get("captured_at", "") or "").strip(),
                    "floors": {
                        str(mode["key"]): max(0, parse_int(str(floors.get(str(mode["key"]), 0) or "0")))
                        for mode in TOWER_TRACKED_MODES
                    },
                }
            )
        return {
            "modes": [
                {
                    "key": str(mode["key"]),
                    "label": display_tower_mode_label(str(mode["key"])),
                }
                for mode in TOWER_TRACKED_MODES
            ],
            "entries": payload_entries,
        }

    def _write_payload(self, payload: dict[str, object]) -> None:
        with self.json_path.open("w", encoding="utf-8") as json_file:
            json.dump(payload, json_file, indent=2)

    def load(self) -> list[dict[str, object]]:
        self.ensure_file()
        with self.json_path.open("r", encoding="utf-8-sig") as json_file:
            payload = json.load(json_file)

        if isinstance(payload, dict):
            raw_entries = payload.get("entries", [])
        elif isinstance(payload, list):
            raw_entries = payload
        else:
            raw_entries = []

        entries: list[dict[str, object]] = []
        if isinstance(raw_entries, list):
            for entry in raw_entries:
                if not isinstance(entry, dict):
                    continue

                raw_floors = entry.get("floors", {})
                normalized_floors = {
                    str(mode["key"]): 0
                    for mode in TOWER_TRACKED_MODES
                }

                if isinstance(raw_floors, dict):
                    for key, value in raw_floors.items():
                        canonical_key = canonical_tower_mode_key(str(key))
                        if canonical_key in normalized_floors:
                            normalized_floors[canonical_key] = max(0, parse_int(str(value or "0")))
                else:
                    for mode in TOWER_TRACKED_MODES:
                        mode_key = str(mode["key"])
                        normalized_floors[mode_key] = max(0, parse_int(str(entry.get(mode_key, 0) or "0")))

                entries.append(
                    {
                        "captured_at": str(entry.get("captured_at", "") or "").strip(),
                        "floors": normalized_floors,
                    }
                )

        expected_payload = self.build_payload(entries)
        if payload != expected_payload:
            self._write_payload(expected_payload)
        return entries

    def save(self, entries: list[dict[str, object]]) -> None:
        self.json_path.parent.mkdir(parents=True, exist_ok=True)
        self._write_payload(self.build_payload(entries))
