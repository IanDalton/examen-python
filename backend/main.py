import json
import os
import shutil
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

    def pytest_runtest_logreport(self, report):  # type: ignore[override]
        if report.when == "call":
            entry = {
                "nodeid": report.nodeid,
                "outcome": report.outcome,
            }
            if report.failed:
                entry["message"] = str(report.longrepr)
            self.results.append(entry)


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

    collector = PytestResultCollector()

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        shutil.copytree(TESTS_DIR, tmp_path / "tests")
        shutil.copyfile(stored_path, tmp_path / "bookbyte.py")

        with ChangeCwd(tmp_path):
            exit_code = pytest.main(["-q", "tests"], plugins=[collector])

    total = len(collector.results)
    passed = sum(1 for r in collector.results if r["outcome"] == "passed")
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
