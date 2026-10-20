#!/bin/bash
# PreToolUse(Edit|Write|MultiEdit): 기존 코드 파일 수정 전 callgraph impact 확인을 상기시킨다(차단 안 함). 세션·파일당 1회.
exec /usr/bin/python3 -c '
import json, os, sys, hashlib
try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)
ti = data.get("tool_input") or {}
path = ti.get("file_path") or ""
exts = (".ts",".tsx",".js",".jsx",".mjs",".cjs",".dart",".swift",".kt",".java",".py",".go",".rs",".m",".mm",".c",".cc",".cpp",".h",".hpp",".rb",".php",".cs",".vue",".svelte",".sql")
if not path.endswith(exts) or not os.path.isfile(path):
    sys.exit(0)
sid = str(data.get("session_id") or "nosession")
d = os.path.join(os.environ.get("TMPDIR", "/tmp"), "claude-impact-reminder")
os.makedirs(d, exist_ok=True)
mark = os.path.join(d, hashlib.sha1((sid + "\0" + path).encode()).hexdigest())
if os.path.exists(mark):
    sys.exit(0)
open(mark, "w").close()
print(json.dumps({"hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "additionalContext": "[harness] 기존 심볼을 고치는 수정이면 callgraph impact(mcp__callgraph__impact, 절대 project_path)를 먼저 확인하세요. HIGH면 code-reviewer 리뷰가 필수입니다. 이미 확인했거나 새 코드만 추가하는 경우 무시해도 됩니다."
}}, ensure_ascii=False))
sys.exit(0)
'
