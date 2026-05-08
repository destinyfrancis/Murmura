"""OASIS compatibility check.

This module validates whether the environment can run the OASIS simulation
engine. The result is intentionally conservative: if the compatible Python
binary cannot import ``oasis``, Step 3 should be disabled instead of allowing a
workflow to complete with an empty action timeline.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from backend.app.utils.logger import get_logger

logger = get_logger("oasis_compatibility")

SIMULATION_ENGINE_AVAILABLE: bool = True
OASIS_UNAVAILABLE_REASON: str = ""
OASIS_PYTHON_PATH: str = sys.executable
OASIS_IMPORTABLE: bool = False


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent.parent


def _is_supported_python(python_bin: Path) -> bool:
    """Return whether *python_bin* is Python 3.10 or 3.11."""
    try:
        result = subprocess.run(
            [
                str(python_bin),
                "-c",
                "import sys; raise SystemExit(0 if sys.version_info[:2] in ((3, 10), (3, 11)) else 1)",
            ],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except Exception:
        return False
    return result.returncode == 0


def _find_compatible_python() -> Path:
    """Find the Python binary used by the OASIS subprocess runner."""
    venv_python = _project_root() / ".venv311" / "bin" / "python"
    if venv_python.exists() and _is_supported_python(venv_python):
        return venv_python

    major, minor = sys.version_info[:2]
    if major == 3 and minor in (10, 11):
        return Path(sys.executable)

    for version in ("3.11", "3.10"):
        found = shutil.which(f"python{version}")
        if found and _is_supported_python(Path(found)):
            return Path(found)

    return Path(sys.executable)


def _probe_oasis_import(python_bin: Path) -> tuple[bool, str]:
    """Return whether *python_bin* can import the OASIS package."""
    code = (
        "import importlib.util, sys; "
        "ok = importlib.util.find_spec('oasis') is not None; "
        "sys.exit(0 if ok else 7)"
    )
    try:
        result = subprocess.run(
            [str(python_bin), "-c", code],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except Exception as exc:  # noqa: BLE001
        return False, f"oasis_probe_failed:{exc.__class__.__name__}"
    if result.returncode == 0:
        return True, ""
    detail = (result.stderr or result.stdout or "oasis package not importable").strip()
    return False, detail[:200]


def _detect_oasis_compatibility(
    *,
    version_info: tuple[int, int] | None = None,
    python_bin: Path | None = None,
    import_probe: Callable[[Path], tuple[bool, str]] = _probe_oasis_import,
) -> dict[str, Any]:
    """Pure detection helper, kept injectable for focused tests."""
    major, minor = version_info or sys.version_info[:2]
    candidate = python_bin or _find_compatible_python()
    candidate_supported = (
        (major == 3 and minor in (10, 11)) if version_info is not None else _is_supported_python(candidate)
    )
    if not candidate_supported:
        return {
            "available": False,
            "reason": f"python_{major}_{minor}_unsupported" if version_info is not None else "python_unsupported",
            "python_path": str(candidate),
            "oasis_importable": False,
        }

    importable, detail = import_probe(candidate)
    if not importable:
        return {
            "available": False,
            "reason": "oasis_missing",
            "detail": detail,
            "python_path": str(candidate),
            "oasis_importable": False,
        }

    return {
        "available": True,
        "reason": "",
        "python_path": str(candidate),
        "oasis_importable": True,
    }


def check_oasis_compatibility() -> None:
    """Check if the current environment can import and run OASIS."""
    global OASIS_IMPORTABLE, OASIS_PYTHON_PATH, OASIS_UNAVAILABLE_REASON, SIMULATION_ENGINE_AVAILABLE

    result = _detect_oasis_compatibility()
    SIMULATION_ENGINE_AVAILABLE = bool(result["available"])
    OASIS_UNAVAILABLE_REASON = str(result.get("reason") or "")
    OASIS_PYTHON_PATH = str(result.get("python_path") or sys.executable)
    OASIS_IMPORTABLE = bool(result.get("oasis_importable"))

    if not SIMULATION_ENGINE_AVAILABLE:
        logger.warning(
            "OASIS simulation engine unavailable: reason=%s python=%s detail=%s",
            OASIS_UNAVAILABLE_REASON,
            OASIS_PYTHON_PATH,
            str(result.get("detail") or "")[:160],
        )


def get_capabilities() -> dict[str, Any]:
    """Return backend capabilities for the frontend."""
    reason = OASIS_UNAVAILABLE_REASON
    return {
        "simulation": SIMULATION_ENGINE_AVAILABLE,
        "simulation_available": SIMULATION_ENGINE_AVAILABLE,
        "reason": reason,
        "python_path": OASIS_PYTHON_PATH,
        "oasis_importable": OASIS_IMPORTABLE,
        "kg_generation": True,  # Always available
        "report_generation": True,  # LLM-based, Python independent
    }


def ensure_oasis_available() -> None:
    """Raise a clear runtime error when Step 3 cannot run."""
    if not SIMULATION_ENGINE_AVAILABLE:
        raise RuntimeError(f"simulation_engine_unavailable:{OASIS_UNAVAILABLE_REASON or 'unknown'}")


# Run the check on import
check_oasis_compatibility()
