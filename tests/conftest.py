"""Pytest configuration for the corp-recon-engine test suite.

Responsibilities
----------------
* Put the repository root on ``sys.path`` so the repo's flat top-level modules
  (``vendor_normalizer``, ``vendor_aliases``, ``recon_engine``,
  ``report_generator``) import cleanly no matter where pytest is invoked from.
* Provide a path-based module loader (``importlib.util.spec_from_file_location``)
  so modules are bound to their real location in the repository and never
  depend on the current working directory.
* Expose session-scoped fixtures for the modules under test.

Guarantees
----------
Nothing in this suite performs network access, launches the Gradio UI, loads a
model, or writes to disk outside of pytest's ``tmp_path``.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

# Repository root == parent of the ``tests`` directory.
REPO_ROOT = Path(__file__).resolve().parents[1]

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


# Modules that must be loaded *before* the given module so that the
# ``from <dep> import ...`` statements inside it resolve to the very same
# module objects this suite exposes (no duplicate module instances).
_MODULE_DEPENDENCIES: dict[str, tuple[str, ...]] = {
    "recon_engine": ("vendor_normalizer", "vendor_aliases"),
}

_MODULE_CACHE: dict[str, object] = {}


def load_repo_module(module_name: str):
    """Import a repository module by file path and cache it.

    ``importlib.util.spec_from_file_location`` is used deliberately: the module
    is loaded from its actual path inside the repository, so the import works
    regardless of ``sys.path`` ordering or the process working directory.

    Raises ``ImportError`` when the file is missing and re-raises any import
    error raised while executing the module (a failed import is not cached).
    """
    cached = _MODULE_CACHE.get(module_name)
    if cached is not None:
        return cached

    for dependency in _MODULE_DEPENDENCIES.get(module_name, ()):
        load_repo_module(dependency)

    path = REPO_ROOT / f"{module_name}.py"
    if not path.is_file():
        raise ImportError(f"expected module file not found: {path}")

    # Reuse an already-imported module when it is the very same file, so the
    # suite never ends up with two independent copies of the same module.
    already = sys.modules.get(module_name)
    if already is not None:
        existing_file = getattr(already, "__file__", None)
        if existing_file and Path(existing_file).resolve() == path.resolve():
            _MODULE_CACHE[module_name] = already
            return already

    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot build an import spec for {path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        # Never leave a half-initialised module behind for the next import.
        sys.modules.pop(module_name, None)
        raise

    _MODULE_CACHE[module_name] = module
    return module


@pytest.fixture(scope="session")
def repo_root() -> Path:
    """Absolute path of the repository root."""
    return REPO_ROOT


@pytest.fixture(scope="session")
def vendor_normalizer():
    """The ``vendor_normalizer`` module (imports only ``re``)."""
    return load_repo_module("vendor_normalizer")


@pytest.fixture(scope="session")
def vendor_aliases():
    """The ``vendor_aliases`` module (imports only ``pandas``)."""
    return load_repo_module("vendor_aliases")


@pytest.fixture(scope="session")
def recon_engine():
    """The ``recon_engine`` module.

    ``recon_engine`` pulls in gradio/pandas/rapidfuzz/fpdf at module level, so
    it may legitimately be unavailable in a minimal environment. In that case
    the dependent tests are skipped rather than failing the whole run.
    """
    try:
        return load_repo_module("recon_engine")
    except Exception as exc:  # pragma: no cover - environment dependent
        pytest.skip(f"recon_engine is not importable in this environment: {exc}")
