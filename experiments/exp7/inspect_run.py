import json
import sys
from pathlib import Path

run_id = sys.argv[1]
path = Path("backend/logs/acceptance-runs") / f"{run_id}.json"
data = json.loads(path.read_text(encoding="utf-8"))
print("status", data.get("promptVersion"), "attempts", data.get("attempts"),
      "tokens", data.get("promptTokens"), data.get("completionTokens"))
for attempt in data.get("rawAttempts") or []:
    print("=" * 30, "attempt", attempt["attempt"], (attempt.get("checks") or {}).get("messages"))
    raw = attempt.get("rawOutput") or ""
    print(raw[:4000])