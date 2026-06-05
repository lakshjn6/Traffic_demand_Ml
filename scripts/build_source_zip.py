"""
Package all source files into a single submission zip.

Usage:
    python scripts/build_source_zip.py

Output: <repo_root>/submission_source.zip
"""
import zipfile
from pathlib import Path

REPO    = Path(__file__).resolve().parents[1]
SRC_DIR = REPO / "source"
OUT_ZIP = REPO / "submission_source.zip"

# Each tuple: (file on disk, name inside the zip archive)
ENTRIES = [
    (SRC_DIR / "approach.txt",                    "approach.txt"),
    (SRC_DIR / "predict.py",                      "predict.py"),
    (SRC_DIR / "requirements.txt",                "requirements.txt"),
    (SRC_DIR / "README.txt",                      "README.txt"),
    (SRC_DIR / "traffic_demand_solution.ipynb",   "traffic_demand_solution.ipynb"),
    (SRC_DIR / "Presentation.pptx",               "Presentation.pptx"),
]

EXPECTED_NAMES = [arc for _, arc in ENTRIES]


def validate_entries() -> None:
    missing = [str(path) for path, _ in ENTRIES if not path.exists()]
    if missing:
        raise SystemExit(
            "The following files are missing — run any generation scripts first:\n"
            + "\n".join(f"  {m}" for m in missing)
        )


def build_zip() -> None:
    validate_entries()

    with zipfile.ZipFile(OUT_ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
        for path, arcname in ENTRIES:
            zf.write(path, arcname=arcname)
            size_kb = path.stat().st_size / 1024
            print(f"  + {arcname:<45} ({size_kb:,.1f} KB)")

    # Verify archive integrity
    with zipfile.ZipFile(OUT_ZIP, "r") as zf:
        names = zf.namelist()
        assert names == EXPECTED_NAMES, f"Manifest mismatch:\n  got: {names}"
        for name in EXPECTED_NAMES:
            assert zf.getinfo(name).file_size > 0, f"Empty entry: {name}"

    total_kb = OUT_ZIP.stat().st_size / 1024
    print(f"\n✓  {OUT_ZIP.name}  ({total_kb:,.1f} KB total)")
    print("   Contents:", names)


if __name__ == "__main__":
    build_zip()
