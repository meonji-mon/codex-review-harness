#!/bin/bash
# PreToolUse(Bash): force-push, reset --hard, git clean -f, backup/* 브랜치 삭제를 막는다.
exec /usr/bin/python3 -c '
import json, re, shlex, sys
try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)
cmd = (data.get("tool_input") or {}).get("command") or ""
if "git" not in cmd:
    sys.exit(0)
reasons = []
for seg in re.split(r"&&|\|\||;|\||\n|\$\(|`", cmd):
    try:
        t = shlex.split(seg)
    except ValueError:
        t = seg.split()
    if "git" not in t:
        continue
    t = t[t.index("git") + 1:]
    # skip global options like -C dir, -c k=v
    while t and t[0].startswith("-"):
        t = t[2:] if t[0] in ("-C", "-c") else t[1:]
    if not t:
        continue
    sub, args = t[0], t[1:]
    if sub == "push":
        if any(a in ("-f", "--force", "--force-with-lease", "--force-if-includes") or a.startswith("--force-with-lease=") or (re.match(r"^-[a-zA-Z]*f[a-zA-Z]*$", a)) for a in args) \
           or any(a.startswith("+") for a in args):
            reasons.append("force-push")
        if ("--delete" in args or "-d" in args) and any(re.search(r"(^|/|:)backup/", a) for a in args):
            reasons.append("backup/* 원격 브랜치 삭제")
        if any(re.match(r"^:(refs/heads/)?backup/", a) for a in args):
            reasons.append("backup/* 원격 브랜치 삭제")
    elif sub == "reset" and "--hard" in args:
        reasons.append("git reset --hard")
    elif sub == "clean" and any(a == "--force" or re.match(r"^-[a-zA-Z]*f", a) for a in args):
        reasons.append("git clean -f")
    elif sub == "branch" and any(a in ("-d", "-D", "--delete") or re.match(r"^-[a-zA-Z]*[dD]", a) for a in args) \
         and any(re.match(r"^(refs/heads/|origin/)?backup/", a) for a in args):
        reasons.append("backup/* 브랜치 삭제")
    elif sub == "update-ref" and "-d" in args and any("backup/" in a for a in args):
        reasons.append("backup/* ref 삭제")
if reasons:
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": "Git 보호 규칙(~/.claude/CLAUDE.md): " + ", ".join(dict.fromkeys(reasons)) + " 은(는) 차단됩니다. 우회하지 말고 사용자에게 보고하세요."
    }}, ensure_ascii=False))
sys.exit(0)
'
