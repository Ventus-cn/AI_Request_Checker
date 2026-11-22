import json
import sys
from pathlib import Path

import httpx2

root = Path(__file__).resolve().parent
samples = json.loads((root / "testset.json").read_text(encoding="utf-8"))["samples"]
sample_id = sys.argv[1] if len(sys.argv) > 1 else "AC-02"
version = sys.argv[2] if len(sys.argv) > 2 else "original"
mode = sys.argv[3] if len(sys.argv) > 3 else "model"
sample = next(s for s in samples if s["id"] == sample_id)
response = httpx2.post(
    "http://localhost:8080/api/acceptance/runs",
    json={"text": sample["text"], "promptVersion": version, "mode": mode},
    timeout=180,
)
print("HTTP", response.status_code)
data = response.json()
print("runId", data.get("runId"), "status", data.get("status"), "ms", data.get("durationMs"),
      "tokens", (data.get("usage") or {}).get("totalTokens"))
print("error:", data.get("error"))
report = data.get("report") or {}
print("summary:", report.get("summary"))
print("kind:", report.get("requirementKind"))
for ac in (report.get("acceptanceCriteria") or []):
    print("AC", ac.get("id"), ac.get("title"), "|", ac.get("given"), "/", ac.get("when"), "/", ac.get("then"))
    print("   quote:", ac.get("sourceQuote"))
for ts in (report.get("testSamples") or []):
    print("TS", ts.get("id"), ts.get("kind"), ts.get("input"), "->", ts.get("expected"))
print("questions:", report.get("openQuestions"))