# ToG Character Manager

This project adds a Python desktop application for managing CSV items stored in [characters.csv](/C:/ToG/characters.csv).

## What it does

- Creates new items
- Reads and lists existing items
- Updates selected items
- Deletes items
- Imports the `Icon` field from an `http` or `https` PNG image URL
- Saves downloaded PNG icons into `imported_icons/` and stores the relative file path back into the CSV
- Shows each character in a material-style summary card with its icon when available
- Shows a blank rectangle placeholder when a character has no icon
- Uses the `Color` code for borders: `R` red, `G` green, `B` blue, `Y` yellow, `D` dark purple
- Uses local star image assets from `assets/` to render the `L` and `B` star rating in the summary
- Always uses the local `characters.csv` file and does not allow switching to another CSV in the UI

## Files

- [app.py](/C:/ToG/app.py): Tkinter desktop application with a material-inspired layout
- `assets/`: local star images used by the summary cards
- [characters.csv](/C:/ToG/characters.csv): the fixed CSV file used by the app

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
5. Click `Create` or `Update` to write the row into the CSV.
