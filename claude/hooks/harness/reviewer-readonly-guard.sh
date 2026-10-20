#!/bin/bash
# 읽기 전용 서브에이전트(Bash)용: 파일/Git/원격 쓰기 명령을 막는다. 프롬프트 지시의 보조 장치.
exec /usr/bin/python3 -c '
import json, re, sys
try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)
cmd = (data.get("tool_input") or {}).get("command") or ""
pat = [
 r"(^|[\s;&|(])(rm|rmdir|mv|cp|touch|mkdir|chmod|chown|ln|truncate|dd|tee|install|trash)\s",
 r"(^|[^0-9&>])>{1,2}\s*(?!&|/dev/null)[^\s]",
 r"\bsed\s+(-[a-zA-Z]*i|--in-place)",
 r"\bperl\s+-[a-zA-Z]*i",
 r"\bgit\s+(-C\s+\S+\s+)?(add|commit|push|pull|merge|rebase|reset|checkout|switch|restore|clean|stash|branch\s+-[dDmM]|tag|cherry-pick|revert|am|apply|rm|mv|gc|prune|fetch|worktree|config|update-ref|filter-branch)\b",
 r"\b(npm|pnpm|yarn|bun|pip3?|brew|gem|cargo|pod|flutter\s+pub|dart\s+pub)\s+(i|add|install|remove|uninstall|update|upgrade|ci|get)\b",
 r"\b(gh|vercel|supabase|firebase|eas|fastlane|xcrun\s+altool|curl\s+.*-X\s*(POST|PUT|PATCH|DELETE))\b.*",
 r"\b(prettier|eslint|dart\s+format|swiftformat|black|ruff)\b.*(--write|--fix|\s-w\b)",
]
if any(re.search(p, cmd) for p in pat):
    if re.match(r"^\s*gh\s+(pr|issue|run|api)\s+(view|list|diff|checks|status)\b", cmd) or re.match(r"^\s*gh\s+api\s+(?!.*-X)(?!.*--method)", cmd):
        sys.exit(0)
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
        "permissionDecisionReason": "읽기 전용 역할입니다. 쓰기/설치/Git 변경/원격 쓰기 명령은 실행할 수 없습니다. 필요한 검사는 메인에게 요청하세요."}}, ensure_ascii=False))
sys.exit(0)
'
