"""mesh_paths — canonical runtime resolver for mesh volume roots.

WHY: the agent-mesh volume is the SAME underlying disk but mounted at different
paths per container — `/mnt/agent-mesh/mesh` on host + voice/openclaw containers,
`/mesh` on webtop desktop containers. Any fleet helper that writes receipts /
ledger / blackboard MUST resolve the root at runtime, or it silently writes to a
dead path on whichever container it didn't hardcode for. (This generalizes the
inline `_mesh_ledger_root()` fix in complete_task.py, josh-desktop 2026-06-13,
after that exact bug ate both convergence writes on the webtop.)

Usage:
    from mesh_paths import mesh_root, ledger_root, receipts_dir, blackboard_root
    receipts_dir().mkdir(parents=True, exist_ok=True)   # correct on ANY container
"""
from pathlib import Path

# probe order: host/voice mount first, then webtop. Same disk, different mountpoint.
_CANDIDATES = (Path("/mnt/agent-mesh/mesh"), Path("/mesh"))
_HOST_DEFAULT = Path("/mnt/agent-mesh/mesh")


def mesh_root() -> Path:
    """The agent-mesh root on THIS container. Falls back to host default."""
    for p in _CANDIDATES:
        if p.exists():
            return p
    return _HOST_DEFAULT


def ledger_root() -> Path:
    return mesh_root() / "LEDGER"


def receipts_dir() -> Path:
    return ledger_root() / "receipts"


def blackboard_root() -> Path:
    return mesh_root() / "BLACKBOARD"


def which_container() -> str:
    """Diagnostic: which mount won (for smoke output / logging)."""
    for p in _CANDIDATES:
        if p.exists():
            return f"{p} (exists)"
    return f"{_HOST_DEFAULT} (default — neither candidate present)"


if __name__ == "__main__":
    print("mesh_root     :", mesh_root())
    print("ledger_root   :", ledger_root())
    print("receipts_dir  :", receipts_dir())
    print("blackboard    :", blackboard_root())
    print("resolved via  :", which_container())
