from patch import apply_runtime_patches

apply_runtime_patches()

from startup_perf_patch import apply_startup_perf_patch

apply_startup_perf_patch()

from tog_app import TogCharacterManager


if __name__ == "__main__":
    app = TogCharacterManager()
    app.mainloop()
