from .runtime_patch import apply_runtime_patches as apply_runtime_patch
from .tower_progress_runtime_patch import apply_runtime_patches as apply_tower_progress_runtime_patches


def apply_runtime_patches() -> None:
    apply_tower_progress_runtime_patches()
    apply_runtime_patch()


__all__ = ["apply_runtime_patches"]
