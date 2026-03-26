# Tower of God: New World Account Manager

`Tower of God: New World Account Manager` is a desktop app built with Python and Tkinter for tracking multiple `Tower of God: New World` resources in one place.

It currently combines five tools in a single UI:

- character collection management
- multi-team formation building
- pack value analysis
- gacha Monte Carlo simulation
- tower progress history tracking

## Main Features

### Characters

- Create, update, and delete character entries
- Store character data in `db/characters.json`
- Track icon, rarity, color, name, `L`, `B`, `Revolution`, `EE`, `Rapport`, gear slots, and IW fields
- Import character icons directly from `http` or `https` PNG/WebP URLs
- Save imported icons into `imported_icons/`
- Preview imported or local icons inside the editor
- Show character summary cards with icon, rarity, color, stars, IW info, and quick stats
- Sort the roster by `LB`, `Rarity`, or `Color`
- Filter the summary by rarity, color, `L`, and `Revolution`
- Normalize character color and `L` values for storage/display
- Prevent deleting a character that is still used in a formation
- Automatically update formation references when a character version is edited

### Formations

- Create, update, and delete saved formations
- Store formations in `db/formations.json`
- Use a dedicated editor scene separate from the saved formations list
- Give each formation up to five teams: `Team 1` through `Team 5`
- Save team-specific notes for each team
- Build formations on a 5-slot board: `Front 1`, `Front 2`, `Front 3`, `Back 1`, `Back 2`
- Drag characters from the roster into formation slots
- Click occupied slots to move, swap, or clear characters
- Filter the roster by color and rarity while editing
- Show saved formation previews with team member icons
- Open a popup with the full character sheet from roster cards
- Validate that:
  - the formation name is unique
  - every assigned character exists in the Characters tab
  - a team cannot contain duplicate characters
  - a character cannot appear in more than one team inside the same formation
  - at least one character is assigned before saving

### Packs Value

- Create, update, and delete saved packs
- Store pack data and shared item-base data in `db/packs.json`
- Maintain a shared item-base catalog used by every pack
- Create, update, and delete item-base entries with:
  - item name
  - priority
  - base value
  - computed item value
- Search the shared item catalog from both the pack editor and the item-base manager
- Add catalog items to a pack from the catalog view
- Increase the amount automatically when adding the same item again
- Edit item quantities directly in the pack editor
- Remove items from a pack
- Create lootbox-backed item-base entries from the `New Lootbox` flow in `Global Item Base`
- Build lootboxes from shared item-base entries with:
  - selected item-base item
  - drop probability
  - drop amount
  - live expected-value calculation
- Save a lootbox expected value as an item-base entry
- Reopen stored lootboxes from `Global Item Base` with `Edit Lootbox`
- Update stored lootbox items, amounts, and probabilities
- Recalculate lootbox-backed item-base values automatically when their source item-base values change
- Use lootbox-backed item-base entries inside normal packs just like any other catalog item
- Calculate pack metrics live:
  - total pack value
  - price converted from BRL to USD
  - value per USD
- Sort pack cards by their computed value efficiency
- Prevent deleting an item-base entry while it is still used by any pack
- Prevent deleting an item-base entry while it is still used by a stored lootbox definition
- Rename item-base references across packs when an item-base name changes
- Rename item-base references inside stored lootbox definitions when an item-base name changes

### Gacha Simulation

- Run Monte Carlo simulations from the `Gacha Simulation` tab
- Configure:
  - simulation mode
  - number of trials
  - target copies
  - base rate
  - pity pull limit
  - hard pity on/off
  - available pulls for budget mode
- Support two simulation modes:
  - `Fixed Pull Budget`
  - `Pull Until Maxed`
- Run the simulation on a background thread so the UI stays responsive
- Summarize results with averages, medians, percentiles, and best/worst outcomes
- Show success chance in fixed-budget mode
- Render a histogram for either pull cost or copies obtained
- Mark mean and median on the histogram
- Clear results without leaving the tab

### Tower Progress

- Create, update, and delete dated tower snapshots
- Store tower progress in `db/tower_progress.json`
- Track floor history for:
  - `Adventure`
  - `Hard Adventure`
- Accept timestamps in ISO format or local-style `dd/mm/yyyy` inputs
- Keep a chronological snapshot history
- Filter the history and chart by tower mode
- Show delta changes versus the previous snapshot in the history list
- Show the latest recorded floors in a quick summary card
- Draw a time-series chart of tower evolution over time
- Highlight the selected snapshot in the chart/history flow

## Data Files

- `db/characters.json`: character roster
- `db/formations.json`: saved formations and all team assignments
- `db/packs.json`: shared item-base catalog and saved packs
- `db/tower_progress.json`: saved tower snapshots
- `imported_icons/`: downloaded character icons
- `assets/`: local color/star assets used by the UI

The repositories auto-create missing JSON files on first load.

## Project Structure

- `app.py`: launcher
- `tower_progress_runtime_patch.py`: runtime patch entry used before app startup
- `tog_app/app_window.py`: main Tk application shell and tab wiring
- `tog_app/constants.py`: shared constants, UI colors, options, and file paths
- `tog_app/helpers.py`: normalization, parsing, and display helpers
- `tog_app/repositories.py`: JSON persistence layer
- `tog_app/mcsim.py`: gacha simulation engine
- `tog_app/panels/characters.py`: Characters tab
- `tog_app/panels/formations.py`: Formations tab
- `tog_app/panels/packs.py`: Packs Value tab
- `tog_app/panels/gacha.py`: Gacha Simulation tab
- `tog_app/panels/tower_progress.py`: Tower Progress tab

## Run

1. Install Python 3.11+ on Windows.
2. Open PowerShell in `C:\Dev\ToG`.
3. Run:

```powershell
py app.py
```

If `py` is not available, use:

```powershell
python app.py
```

## Optional Pillow Support

The app works without extra packages, but Pillow improves image loading/scaling, especially for imported WebP icons.

```powershell
py -m pip install Pillow
```

## Typical Workflows

### Import a Character Icon

1. Open the `Characters` tab.
2. Paste a PNG or WebP image URL into the `Icon` field.
3. Click `Import Image URL`.
4. Save the character with `Create` or `Update`.

### Build a Formation

1. Open the `Formations` tab.
2. Click `New Formation`.
3. Choose the team to edit from `Team 1` to `Team 5`.
4. Drag characters from the roster into the board slots.
5. Save with `Create` or `Update`.

### Evaluate a Pack

1. Open `Packs Value`.
2. Use `Manage Item Base` to create shared catalog items if needed.
3. Create a new pack and enter the BRL price.
4. Add items from the catalog and adjust their amounts.
5. Review total value, USD conversion, and value-per-USD before saving.

### Create or Edit a Lootbox

1. Open `Packs Value`.
2. Click `Manage Item Base`.
3. Use `New Lootbox` in the header to create a new lootbox, or select a lootbox-backed item base and click `Edit Lootbox`.
4. Add lootbox rows using shared item-base entries, then set the drop probability and item amount for each row.
5. Save the lootbox as an item-base entry or update the existing lootbox-backed item base.
6. Reuse that lootbox item base inside normal packs.

### Track Tower Progress

1. Open `Tower Progress`.
2. Enter a capture date/time and the floors for each tracked mode.
3. Save the snapshot.
4. Use the history cards and chart to compare progress over time.
