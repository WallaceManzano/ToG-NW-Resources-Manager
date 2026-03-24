from tower_progress_runtime_patch import apply_runtime_patches

apply_runtime_patches()

from tog_app import TogCharacterManager


if __name__ == "__main__":
    app = TogCharacterManager()
    app.mainloop()
