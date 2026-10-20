# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Security

- **Removed the AGPL-3.0 PyMuPDF dependency.** The OCR fallback path
  imported PyMuPDF (`fitz`) at module level while this repository was
  published under the MIT licence. PyMuPDF is AGPL-3.0, so the licence a
  recipient was given did not match the behaviour of the code they
  received. The renderer is now `pypdfium2` (BSD-3-Clause OR Apache-2.0),
  which provides the same page-to-bitmap operation with no external
  binary dependency. The dependency table re-derived from PyPI metadata
  now contains no strong-copyleft dependency.

### Added

- **Licence gate.** `tests/test_licence_audit.py` fails the build when a
  strong-copyleft dependency is declared or imported in this
  permissively licensed repository, and when a weak-copyleft dependency's
  licence notice is missing. The gate was mutation-proven: it was
  observed failing with the original `import fitz` restored and again
  with `pymupdf` reintroduced into the manifest.
- **`THIRD_PARTY_NOTICES.md`.** The notice that `fpdf2` (LGPL-3.0-only)
  requires now travels with the software.
- **`licence-check` CI job.** The licence gate runs on every push and on
  every pull request, and is a required status check.

## [1.0.0] — 2026-10-20

### Added

- **Real CI test gate.** The Python workflow ran `pytest -q || echo "No tests yet"`,
  which installs no pytest and always exits zero. It is replaced with a
  pinned `pytest==8.3.3` installation and an unconditional `pytest -q`.
  The suite has 266 tests.
- **Dependency pin guard** (`scripts/pin_guard.py`), wired as a required
  `pin-check` status check. It fails the build on a pre-release version
  specifier or a toolchain version that has drifted from the validated pins.

### Changed

- **Launcher scripts are location-independent.** The launchers resolved
  their own directory from a hardcoded absolute path, so the project could
  not run from a fresh clone. They now derive it from the script location.
- **Ruff rule set pinned** to `E4,E7,E9,F` with `ruff==0.17.1`, so the lint
  gate cannot drift with upstream defaults.
- **README author credit** added: Conrad CJ Wilson.

### Fixed

- Dead assignments and an incorrect `requirements.txt` corrected.

### Security

- Secret scanning and push protection enabled at the repository level.

## [0.1.0]

- Initial release: PDF extraction, fuzzy vendor matching and reconciliation reporting

[1.0.0]: https://github.com/cjps4linux-creator/corp-recon-engine/releases/tag/v1.0.0
