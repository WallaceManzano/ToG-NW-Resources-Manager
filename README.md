# ToG Character Manager

This project adds a Python desktop application for managing characters stored in [characters.json](/C:/ToG/characters.json) plus saved teams/formations stored in [formations.json](/C:/ToG/formations.json).

## What it does

- Organizes the app into `Characters` and `Formations` tabs
- Creates, reads, updates, and deletes characters
- Imports the `Icon` field from an `http` or `https` PNG image URL
- Saves downloaded PNG icons into `imported_icons/` and stores the relative file path back into the CSV
- Shows each character in a material-style summary card with its icon when available
- Shows a blank rectangle placeholder when a character has no icon
- Uses the `Color` code for borders: `R` red, `G` green, `B` blue, `Y` yellow, `D` dark purple
- Uses local star image assets from `assets/` to render the `L` and `B` star rating in the summary
- Uses the local `characters.json` file for character storage and will import legacy `characters.csv` data automatically if needed
- Supports custom sorting in the summary by `LB`, `Rarity`, or `Color` using the app-specific order rules
- Creates, updates, and deletes saved formations inside teams
- Opens formation editing in a dedicated scene after clicking an existing formation or creating a new one
- Lets each formation choose one of five teams: `Team 1` to `Team 5`
- Limits each team to 1 to 5 formations
- Limits each formation to 1 to 5 characters in fixed `Front 1-3` and `Back 1-2` slots
- Shows roster cards with icon, `L`, `B`, and rarity
- Lets you drag a character from the roster into a formation slot
- Opens a popup with the character's full information when you click a roster card
- Ensures a character can only belong to one team, while still allowing that character in multiple formations from the same team

## Files

- [app.py](/C:/ToG/app.py): Tkinter desktop application with a material-inspired layout
- `assets/`: local star images used by the summary cards
- [characters.json](/C:/ToG/characters.json): the fixed JSON file used by the app
- [characters.csv](/C:/ToG/characters.csv): legacy CSV source kept only for migration/backup
- [formations.json](/C:/ToG/formations.json): saved team formations

## Run

1. Install Python 3.11+ for Windows.
2. Open PowerShell in `C:\ToG`.
3. Run:

```powershell
py app.py
```

If `py` is not available, use:

```powershell
python app.py
```

## Optional image preview support

The app works without extra packages. If you want smoother PNG thumbnail scaling and preview rendering, install Pillow:

```powershell
py -m pip install Pillow
```

## How icon import works

1. Paste an image URL into the `Icon` field.
2. Click `Import PNG URL`.
3. The app accepts only `image/png` responses and downloads the file into `imported_icons/`.
4. The `Icon` field is replaced with the saved relative path.
5. Click `Create` or `Update` to write the row into the JSON store.

## How formations work

1. Open the `Formations` tab.
2. Click `New Formation` or open an existing formation from the saved list.
3. Choose `Team 1` to `Team 5` and enter a formation name.
4. Click a roster card to inspect the full character details.
5. Drag characters from the roster into the `Front` and `Back` slots.
6. Click `Create` to save a new formation or `Update` to edit the selected one.

The app stores formations in `formations.json` and keeps team rules validated when you save.
