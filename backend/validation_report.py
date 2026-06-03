from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "docs" / "dependency_validation_report.md"

MODULES = [
    "flask",
    "flask_cors",
    "PyPDF2",
    "dotenv",
    "requests",
    "ibm_watsonx_ai",
    "bcrypt",
    "reportlab",
]


def main() -> int:
    results = []
    failed = False
    for module in MODULES:
        try:
            imported = importlib.import_module(module)
            version = getattr(imported, "__version__", "installed")
            results.append((module, "OK", version))
        except Exception as exc:
            failed = True
            results.append((module, "FAIL", str(exc)))

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Dependency Validation Report",
        "",
        f"Python: `{sys.version.split()[0]}`",
        "",
        "| Module | Status | Version / Detail |",
        "| --- | --- | --- |",
    ]
    lines.extend(f"| `{name}` | {status} | {detail} |" for name, status, detail in results)
    lines.extend(
        [
            "",
            "## Runtime Notes",
            "",
            "- Local fallback classification works with `USE_WATSONX=false`.",
            "- Watsonx classification requires valid `WATSONX_API_KEY` and `WATSONX_PROJECT_ID`.",
            "- Recruiter APIs require login via `/api/auth/login`.",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"report": str(REPORT_PATH), "failed": failed}, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
