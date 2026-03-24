# ToG Character Manager

This is a for-fun Python desktop project for managing data from `Tower of God: New World`.

Its current goal is to help manage:

- characters
- formations
- resources (`TODO`)
- tower progress history

## What The App Does

- Organizes the UI into `Characters`, `Formations`, `Packs Value`, `Gacha Simulation`, and `Tower Progress` tabs
- Stores character data in [characters.json](db/characters.json)
- Stores formation data in [formations.json](db/formations.json)
- Stores tower floor snapshots in [tower_progress.json](db/tower_progress.json)
- Creates, reads, updates, and deletes characters
- Imports character icons from `http` or `https` PNG or WebP URLs
- Saves downloaded icons into `imported_icons/`
- Shows character summary cards with icon, rarity, color, stars, and stats
- Supports sorting characters by `LB`, `Rarity`, or `Color`
- Creates, updates, and deletes formations
- Opens formation editing in a dedicated scene
- Lets each formation manage `Team 1` to `Team 5`
- Records dated floor snapshots for tracked tower modes and charts their evolution over time
- Lets you drag characters from the roster into formation slots
- Shows saved formation previews with team member icons
- Opens a popup with full character information from the formation roster

## Project Structure

- [app.py](app.py): small launcher
- [tog_app/app_window.py](tog_app/app_window.py): main app window
- [tog_app/constants.py](tog_app/constants.py): shared constants
- [tog_app/helpers.py](tog_app/helpers.py): shared helper functions
- [tog_app/repositories.py](tog_app/repositories.py): JSON persistence
- [tog_app/panels/characters.py](tog_app/panels/characters.py): Characters tab/panel logic
- [tog_app/panels/formations.py](tog_app/panels/formations.py): Formations tab/panel logic
- [characters.json](db/characters.json): character store
- [formations.json](db/formations.json): formation store
- [tower_progress.json](db/tower_progress.json): tower progress snapshot store
- `assets/`: local visual assets
- `imported_icons/`: downloaded icon files

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

## Optional Pillow Support

The app works without extra packages. If you want smoother image scaling and reliable WebP previews, install Pillow:

```powershell
py -m pip install Pillow
```

## How Icon Import Works

1. Paste an image URL into the `Icon` field.
2. Click `Import Image URL`.
3. The app accepts `image/png` and `image/webp` responses and downloads the file into `imported_icons/` with the matching extension.
4. The `Icon` field is replaced with the saved relative path.
5. Click `Create` or `Update` to save the character.

## How Formations Work

1. Open the `Formations` tab.
2. Click `New Formation` or open an existing saved formation.
3. Choose the team you want to edit from `Team 1` to `Team 5`.
4. Drag characters from the roster into the board slots.
5. Click `Create` for a new formation or `Update` for an existing one.

The app validates formation rules when saving and keeps formations in `db/formations.json`.


