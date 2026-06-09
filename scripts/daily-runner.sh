#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="/Users/jc/Documents/oneday-onebook"
LEGACY_RUNBOOK="$PROJECT_DIR/prompts/cron-daily.md"
STATE_ROOT="${ONEBOOK_STATE_DIR:-$HOME/.oneday-onebook}"
RUN_DATE="${ONEBOOK_DATE:-$(TZ=Asia/Shanghai date +%F)}"
RUN_DIR="$STATE_ROOT/runs/$RUN_DATE"
LOCK_ROOT="$STATE_ROOT/locks"
LOCK_DIR="$LOCK_ROOT/$RUN_DATE.lock"
STATE_FILE="$RUN_DIR/state.json"
FINAL_FILE="$RUN_DIR/final.txt"
PROMPT_FILE="$RUN_DIR/agent-prompt.md"
RUN_LOG="$RUN_DIR/runner.log"
MAX_CHARS="${ONEBOOK_FINAL_MAX_CHARS:-500}"
PYTHON_BIN="${ONEBOOK_PYTHON_BIN:-/usr/bin/python3}"
OPENCLAW_BIN="${ONEBOOK_OPENCLAW_BIN:-$(command -v openclaw || true)}"
OPENCLAW_MODEL_CHAIN="${ONEBOOK_MODEL_CHAIN:-newapi/gpt-5.5 xiaomi/mimo-v2.5-pro}"
RUNNER_PY="$PROJECT_DIR/scripts/openclaw_daily_runner.py"
MODE="${1:-run}"

mkdir -p "$RUN_DIR" "$LOCK_ROOT"

write_state() {
  local status="$1"
  local delivered="${2:-false}"
  local error="${3:-}"
  local final_chars=0
  local final_url=""
  local final_title=""

  if [[ -f "$FINAL_FILE" ]]; then
    final_chars="$(/usr/bin/python3 - "$FINAL_FILE" <<'PY'
from pathlib import Path
import sys
print(len(Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace").strip()))
PY
)"
    final_url="$(/usr/bin/python3 - "$FINAL_FILE" <<'PY'
from pathlib import Path
import re
import sys
text = Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace")
match = re.search(r"https://q787761871-bit\.github\.io/oneday-onebook/\d{4}/\d{2}/\d{2}/\S+/?", text)
print(match.group(0) if match else "")
PY
)"
    final_title="$(/usr/bin/python3 - "$FINAL_FILE" <<'PY'
from pathlib import Path
import re
import sys
text = Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace")
match = re.search(r"《([^》]+)》", text)
print(match.group(1) if match else "")
PY
)"
  fi

  /usr/bin/python3 - "$STATE_FILE" "$RUN_DATE" "$status" "$delivered" "$error" "$final_chars" "$final_url" "$final_title" <<'PY'
import json
import sys
import time
from pathlib import Path

state_path = Path(sys.argv[1])
run_date, status, delivered, error, final_chars, final_url, final_title = sys.argv[2:]
data = {
    "date": run_date,
    "status": status,
    "delivered": delivered == "true",
    "updatedAtMs": int(time.time() * 1000),
    "finalPath": str(state_path.with_name("final.txt")),
    "finalChars": int(final_chars),
    "finalUrl": final_url,
    "finalTitle": final_title,
}
if state_path.exists():
    try:
        previous = json.loads(state_path.read_text(encoding="utf-8"))
        data = {**previous, **data}
    except Exception:
        pass
if status == "running" and "startedAtMs" not in data:
    data["startedAtMs"] = int(time.time() * 1000)
if status == "generated":
    data["generatedAtMs"] = int(time.time() * 1000)
if delivered == "true":
    data["deliveredAtMs"] = int(time.time() * 1000)
if error:
    data["error"] = error
elif "error" in data:
    data.pop("error", None)
state_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY
}

fail() {
  local message="$1"
  write_state "failed" "false" "$message"
  printf 'ERROR: %s\n' "$message" >&2
  exit 1
}

ensure_openclaw_runner() {
  [[ -x "$PYTHON_BIN" ]] || fail "python binary is not executable or not found: $PYTHON_BIN"
  [[ -n "$OPENCLAW_BIN" && -x "$OPENCLAW_BIN" ]] || fail "openclaw binary is not executable or not found"
  [[ -f "$RUNNER_PY" ]] || fail "OpenClaw runner not found: $RUNNER_PY"
}

state_value() {
  local key="$1"
  [[ -f "$STATE_FILE" ]] || return 0
  /usr/bin/python3 - "$STATE_FILE" "$key" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
key = sys.argv[2]
try:
    data = json.loads(path.read_text(encoding="utf-8"))
except Exception:
    sys.exit(0)
value = data.get(key)
if isinstance(value, bool):
    print("true" if value else "false")
elif value is not None:
    print(value)
PY
}

validate_final() {
  [[ -s "$FINAL_FILE" ]] || fail "final.txt is empty or missing"

  local chars
  chars="$(/usr/bin/python3 - "$FINAL_FILE" <<'PY'
from pathlib import Path
import sys
print(len(Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace").strip()))
PY
)"
  [[ "$chars" -le "$MAX_CHARS" ]] || fail "final.txt is too long: ${chars} chars > ${MAX_CHARS}"

  /usr/bin/python3 - "$FINAL_FILE" <<'PY' || fail "final.txt is missing a book title in 《》"
from pathlib import Path
import re
import sys
text = Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace")
sys.exit(0 if re.search(r"《[^》]+》", text) else 1)
PY
  /usr/bin/python3 - "$FINAL_FILE" <<'PY' || fail "final.txt is missing a valid onebook Pages URL"
from pathlib import Path
import re
import sys
text = Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace")
pattern = r"https://q787761871-bit\.github\.io/oneday-onebook/\d{4}/\d{2}/\d{2}/\S+/?"
sys.exit(0 if re.search(pattern, text) else 1)
PY
}

print_final() {
  validate_final
  /bin/cat "$FINAL_FILE"
}

mark_delivered() {
  validate_final
  write_state "generated" "true"
  print_final
}

if [[ "$MODE" == "--status" || "$MODE" == "status" ]]; then
  if [[ -f "$STATE_FILE" ]]; then
    /bin/cat "$STATE_FILE"
  else
    printf '{"date":"%s","status":"missing","delivered":false}\n' "$RUN_DATE"
  fi
  exit 0
fi

if [[ "$MODE" == "--mark-delivered" || "$MODE" == "mark-delivered" ]]; then
  mark_delivered
  exit 0
fi

if [[ "$MODE" == "--dry-run" || "$MODE" == "dry-run" ]]; then
  if [[ -f "$FINAL_FILE" ]]; then
    print_final
  else
    printf 'DRY_RUN: would generate onebook daily for %s using %s\n' "$RUN_DATE" "$LEGACY_RUNBOOK"
  fi
  exit 0
fi

if [[ ! -f "$FINAL_FILE" && -s "$FINAL_FILE.tmp" ]]; then
  /bin/mv "$FINAL_FILE.tmp" "$FINAL_FILE"
  validate_final
  write_state "generated" "false"
fi

if [[ "$(state_value status)" == "generated" && "$(state_value delivered)" == "false" ]]; then
  print_final
  exit 0
fi

if [[ "$(state_value delivered)" == "true" ]]; then
  fail "today is already marked delivered; refusing duplicate generation"
fi

if ! /bin/mkdir "$LOCK_DIR" 2>/dev/null; then
  fail "another onebook daily runner is active for $RUN_DATE: $LOCK_DIR"
fi
trap '/bin/rmdir "$LOCK_DIR" 2>/dev/null || true' EXIT

[[ -f "$LEGACY_RUNBOOK" ]] || fail "legacy runbook not found: $LEGACY_RUNBOOK"
ensure_openclaw_runner

write_state "running" "false"

set +e
"$PYTHON_BIN" "$RUNNER_PY" \
  --date "$RUN_DATE" \
  --project-dir "$PROJECT_DIR" \
  --private-root "/Users/jc/myclaude/memory-work" \
  --run-dir "$RUN_DIR" \
  --final-file "$FINAL_FILE.tmp" \
  --prompt-file "$PROMPT_FILE" \
  --openclaw-bin "$OPENCLAW_BIN" \
  --model-chain "$OPENCLAW_MODEL_CHAIN" \
  > "$RUN_LOG" 2>&1
runner_status=$?
set -e

if [[ "$runner_status" -ne 0 ]]; then
  fail "OpenClaw onebook runner failed with exit code $runner_status; see $RUN_LOG"
fi

[[ -s "$FINAL_FILE.tmp" ]] || fail "OpenClaw onebook runner produced no final message; see $RUN_LOG"
/bin/mv "$FINAL_FILE.tmp" "$FINAL_FILE"
validate_final
write_state "generated" "false"
print_final
