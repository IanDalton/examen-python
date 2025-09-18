import importlib
import json
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path
from typing import List

import pytest
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse


BASE_DIR = Path(__file__).resolve().parent.parent
TESTS_DIR = BASE_DIR / "tests"
SUBMISSIONS_DIR = BASE_DIR / "submissions"
LOG_FILE = BASE_DIR / "backend" / "failure_log.json"

SUBMISSIONS_DIR.mkdir(exist_ok=True)

app = FastAPI(title="Exam Autograder")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _slugify(value: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "-" for ch in value).strip("-") or "student"


class PytestResultCollector:
    def __init__(self) -> None:
        self.results: List[dict] = []

    def _append_report(self, *, nodeid: str, outcome: str, message: str | None, phase: str) -> None:
        entry = {"nodeid": nodeid, "outcome": outcome}
        if phase != "call":
            entry["phase"] = phase
        if message:
            entry["message"] = message
        self.results.append(entry)

    def pytest_runtest_logreport(self, report):  # type: ignore[override]
        if report.when != "call" and report.passed:
            return
        message = str(report.longrepr) if report.failed and report.longrepr else None
        self._append_report(
            nodeid=report.nodeid,
            outcome=report.outcome,
            message=message,
            phase=report.when,
        )

    def pytest_collectreport(self, report):  # type: ignore[override]
        if report.failed:
            message = str(report.longrepr) if report.longrepr else None
            nodeid = getattr(report, "nodeid", None) or str(report.fspath)
            self._append_report(
                nodeid=nodeid,
                outcome="failed",
                message=message,
                phase="collect",
            )


class ChangeCwd:
    def __init__(self, new_cwd: Path) -> None:
        self.new_cwd = new_cwd
        self.old_cwd = Path.cwd()

    def __enter__(self):
        os.chdir(self.new_cwd)

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.chdir(self.old_cwd)


def _load_failure_log() -> dict:
    if LOG_FILE.exists():
        try:
            return json.loads(LOG_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {"failures": {}}


def _update_failure_log(failed_results: List[dict]) -> dict:
    data = _load_failure_log()
    failures = data.setdefault("failures", {})
    for item in failed_results:
        node = item["nodeid"]
        entry = failures.setdefault(node, {"count": 0, "last_message": ""})
        entry["count"] += 1
        entry["last_message"] = item.get("message", "")
    LOG_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return data


def _reset_pytest_state() -> None:
    temp_dir = tempfile.gettempdir()
    for name, module in list(sys.modules.items()):
        path = getattr(module, "__file__", None)
        if not path:
            continue
        if path.startswith(temp_dir) or path.endswith("bookbyte.py"):
            sys.modules.pop(name, None)
    sys.modules.pop("bookbyte", None)
    importlib.invalidate_caches()


@app.post("/api/submit")
async def submit_exam(student_name: str = Form(...), file: UploadFile = File(...)):
    if not TESTS_DIR.exists():
        raise HTTPException(status_code=500, detail="Test suite not found on server")

    filename = Path(file.filename or "")
    if filename.suffix != ".py":
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos .py")

    safe_name = _slugify(student_name)
    timestamp = int(time.time())
    stored_name = f"{timestamp}_{safe_name}{filename.suffix}"
    stored_path = SUBMISSIONS_DIR / stored_name

    content = await file.read()
    stored_path.write_bytes(content)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        shutil.copytree(TESTS_DIR, tmp_path / "tests")
        shutil.copyfile(stored_path, tmp_path / "bookbyte.py")

        _reset_pytest_state()
        collector = PytestResultCollector()

        with ChangeCwd(tmp_path):
            exit_code = pytest.main(["-q", "tests", "--maxfail=0"], plugins=[collector])

    test_reports = [r for r in collector.results if r.get("phase", "call") == "call"]
    total = len(test_reports)
    passed = sum(1 for r in test_reports if r["outcome"] == "passed")
    failed = [r for r in collector.results if r["outcome"] != "passed"]
    score = 100.0 * passed / total if total else 0.0

    log_snapshot = _update_failure_log(failed)

    return JSONResponse(
        {
            "student": student_name,
            "stored_file": stored_name,
            "score": round(score, 2),
            "total_tests": total,
            "passed": passed,
            "failed": len(failed),
            "results": collector.results,
            "failure_log": log_snapshot,
            "exit_code": exit_code,
        }
    )


@app.get("/api/logs")
async def get_failure_log():
    return JSONResponse(_load_failure_log())
