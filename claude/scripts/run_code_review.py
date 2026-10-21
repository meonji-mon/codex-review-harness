#!/usr/bin/env python3
"""Run only Claude Code's code-reviewer under a separate macOS read-only profile.

Writes private execution records, never backups or cleanup output. No global
settings change, model fallback, write probe, or file deletion is performed.
"""
import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
from urllib.parse import urlparse
import uuid
from model_selection import EFFORTS, picker_settings, read_catalog, select_reviewer


TOOLS = ["Read", "Grep", "Glob"]


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def save(path, data):
    with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "w") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def role_definition(path):
    source = path.read_text()
    front, body = source.split("---", 2)[1:]
    fields = {}
    for line in front.strip().splitlines():
        key, value = line.split(":", 1)
        value = value.strip()
        fields[key] = json.loads(value) if value.startswith('"') or value in ("true", "false") else value
    require(fields["name"] == "code-reviewer", "unexpected role")
    require([word.strip() for word in fields["tools"].split(",")] == TOOLS, "unexpected role tools")
    require(fields["effort"] in EFFORTS and bool(fields["model"]), "unsupported role model/effort")
    allowed = {"name", "description", "model", "effort", "tools", "disallowedTools", "omitClaudeMd", "permissionMode", "color"}
    require(fields.keys() <= allowed, "unsupported role frontmatter")
    return {"code-reviewer": {"description": fields["description"], "model": fields["model"],
            "effort": fields["effort"], "tools": TOOLS, "permissionMode": "plan", "omitClaudeMd": True,
            "disallowedTools": [word.strip() for word in fields["disallowedTools"].split(",")], "prompt": body.strip()}}


def permission_query(pid, path, operation):
    if not Path(path).exists():
        raise ValueError("kernel permission queries require an existing file or directory")
    # Apple WebKit SandboxSPI.h: sandbox_check(pid_t, char*, enum, ...), PATH=1.
    lib = ctypes.CDLL("/usr/lib/libsandbox.1.dylib", use_errno=True)
    check = lib.sandbox_check
    check.restype = ctypes.c_int
    check.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
    no_report = ctypes.c_int.in_dll(lib, "SANDBOX_CHECK_NO_REPORT").value
    result = check(pid, operation.encode(), 1 | no_report, ctypes.c_char_p(os.fsencode(path)))
    if result not in (0, 1):
        raise RuntimeError("kernel permission query unavailable")
    return result


def launch(config_path, arguments):
    cfg = json.loads(Path(config_path).read_text())
    env = dict(os.environ)
    if urlparse(env.get("ANTHROPIC_BASE_URL", "")).hostname not in {"localhost", "127.0.0.1", "::1"}:
        raise RuntimeError("OpenCodex loopback route required; no native fallback")
    # Preserve normal ocx authentication, including existing subscription auth.
    # Never copy credentials, create placeholder keys, or select an account.
    for key in ("CLAUDE_CODE_EFFORT_LEVEL", "CLAUDE_CODE_SUBAGENT_MODEL", "CLAUDE_CODE_SUBAGENT_MODEL_FORCE"):
        env.pop(key, None)  # Per-run role selections; never change the parent's environment.
    env.update({"CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1", "PYTHONDONTWRITEBYTECODE": "1"})
    command = ["/usr/bin/sandbox-exec", "-f", cfg["profile"], cfg["claude"], *arguments]
    child = subprocess.Popen(command, env=env, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr)
    try:
        time.sleep(0.1)
        permissions = {"read_repo": permission_query(child.pid, cfg["probe"], "file-read-data"),
                       "write_repo": permission_query(child.pid, cfg["probe"], "file-write-data"),
                       "create_repo": permission_query(child.pid, cfg["repo"], "file-write-create"),
                       "write_main_settings": permission_query(child.pid, cfg["main_settings"], "file-write-data"),
                       "write_runtime_state": permission_query(child.pid, cfg["state"], "file-write-create")}
        require(permissions == {"read_repo": 0, "write_repo": 1, "create_repo": 1, "write_main_settings": 1, "write_runtime_state": 0}, "unexpected kernel permissions: " + str(permissions))
        save(Path(cfg["run"]) / "kernel-permissions.json", {"pid": child.pid, "permissions": permissions,
             "profile_sha256": digest(cfg["profile"]), "claude_executable": cfg["claude"],
             "credential_values_recorded": False, "write_probe_executed": False})
        return child.wait()
    except BaseException:
        if child.poll() is None:
            child.terminate()
            child.wait()
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path)
    parser.add_argument("--brief", type=Path)
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--reviewer-model", help="Explicit model/route from --list-models; never substituted")
    parser.add_argument("--reviewer-effort", choices=EFFORTS, help="Override this reviewer only; actual delivery remains unverified")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--list-models", action="store_true", help="Read configured model metadata only; no model call")
    mode.add_argument("--print-model-picker", action="store_true", help="Print a user-settings snippet; no changes or model call")
    mode.add_argument("--show-selection", action="store_true", help="Preview reviewer settings without running a model")
    parser.add_argument("--claude", default=shutil.which("claude"))
    parser.add_argument("--timeout", type=int, default=1200)
    args = parser.parse_args()
    if args.list_models or args.print_model_picker:
        catalog = read_catalog()
        print(json.dumps(picker_settings(catalog) if args.print_model_picker else catalog, ensure_ascii=False, indent=2))
        return 0
    role = Path(__file__).resolve().parents[1] / "agents/code-reviewer.md"
    definition = select_reviewer(role_definition(role), args.reviewer_model, args.reviewer_effort)
    if args.show_selection:
        selected = definition["code-reviewer"]
        print(json.dumps({"requested_model": selected["model"], "requested_effort": selected["effort"],
                          "tools": selected["tools"], "runtime_verified": False}, ensure_ascii=False, indent=2))
        return 0
    if not all((args.repo, args.brief, args.run_dir)):
        parser.error("--repo, --brief and --run-dir are required for execution")
    if sys.platform != "darwin" or not Path("/usr/bin/sandbox-exec").is_file():
        parser.error("verified macOS sandbox support required")
    if not args.claude or not shutil.which("ocx"):
        parser.error("Claude Code and ocx are required")
    repo = args.repo.resolve(); run = args.run_dir.resolve()
    if run == repo or repo in run.parents:
        parser.error("private run records must be outside the worktree")
    run.mkdir(mode=0o700, parents=True, exist_ok=False)
    (run / "state").mkdir(mode=0o700)
    (run / "bin").mkdir(mode=0o700)
    session_id = str(uuid.uuid4())
    state = run / "state"
    workspace = state / ("workspace-" + session_id)
    workspace.mkdir(mode=0o700)
    native_config = Path(os.environ.get("CLAUDE_CONFIG_DIR", str(Path.home() / ".claude"))).resolve()
    runtime_namespace = "^" + re.escape(str(native_config / "projects")) + "/[^/]*" + session_id + "(/.*)?$"
    codex_home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))).resolve()
    role_text = definition["code-reviewer"]["prompt"].replace("${CODEX_HOME_DIR}", str(codex_home)).replace("${USER_HOME}", str(Path.home()))
    definition["code-reviewer"]["prompt"] = role_text
    save(run / "agents.json", definition)
    contract = codex_home / "review/reviewer-contract.md"
    method = codex_home / "review/code-reviewer.md"
    tracked = subprocess.check_output(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"], cwd=repo).decode().split("\0")
    snapshot = {name: digest(repo / name) for name in tracked if name and (repo / name).is_file()}
    packet = {"run_id": session_id, "role": "code-reviewer", "mode": "evidence-only", "repo": str(repo),
              "brief": args.brief.read_text(), "files_sha256": snapshot, "contract_ref": str(contract),
              "method_ref": str(method), "requested_model": definition["code-reviewer"]["model"],
              "requested_effort": definition["code-reviewer"]["effort"],
              "explicit_overrides": {"model": args.reviewer_model is not None, "effort": args.reviewer_effort is not None}}
    save(run / "packet.json", packet)
    protected = [Path.home() / ".claude/settings.json", codex_home / "config.toml", contract, method, role, run / "packet.json", run / "agents.json"]
    before = {str(path): digest(path) for path in protected}
    probe = str(repo / next(iter(snapshot))) if snapshot else str(repo)
    require(permission_query(os.getpid(), probe, "file-write-data") == 0, "main permission unexpectedly restricted")
    profile = '(version 1)\n(allow default)\n(deny file-write* (require-not (require-any (subpath ' + json.dumps(str(state)) + ') (regex ' + json.dumps(runtime_namespace) + '))))\n'
    (run / "readonly.sb").write_text(profile)
    cfg = {"run": str(run), "repo": str(repo), "state": str(state), "profile": str(run / "readonly.sb"),
           "claude": str(Path(args.claude).resolve()), "probe": probe, "main_settings": str(Path.home() / ".claude/settings.json")}
    save(run / "launch.json", cfg)
    shim = run / "bin/claude"
    shim.write_text("#!" + sys.executable + "\nimport runpy,sys\nsys.path.insert(0," + repr(str(Path(__file__).parent)) + ")\nsys.argv=[" + repr(str(Path(__file__))) + ", '--launch', " + repr(str(run / "launch.json")) + "]+sys.argv[1:]\nrunpy.run_path(" + repr(str(Path(__file__))) + ",run_name='__main__')\n")
    shim.chmod(0o700)
    dispatcher = ("You are a read-only review dispatcher. Invoke Agent exactly once with subagent_type=code-reviewer. "
                  "Give that fresh subagent only the fixed packet path, SHA256 and run ID from the user message. "
                  "Do not copy parent reasoning or conclusions, invoke other roles, or review/modify files yourself. "
                  "Wait for that original code-reviewer and return its complete result and limits unchanged.")
    command = ["ocx", "claude", "--restricted", "--setting-sources", "", "--settings", '{"disableAllHooks":true}', "--agents", str(run / "agents.json"),
               "--model", "ocx-claude-native--gpt-6.1-sol", "--effort", "low", "--tools", ",".join(["Agent", *TOOLS]),
               "--allowedTools", "Agent(code-reviewer)", *TOOLS, "--system-prompt", dispatcher,
               "--permission-mode", "plan", "--permission-prompts", "none", "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}',
               "--disable-slash-commands", "--no-chrome", "--session-id", session_id, "--forward-subagent-text",
               "--add-dir", str(repo), "--add-dir", str(run), "--add-dir", str(contract.parent), "--print", "--verbose", "--output-format", "stream-json"]
    prompt = "Dispatch only code-reviewer. It must read this entire fixed packet and the full referenced contract/method before reviewing. Packet: " + str(run / "packet.json") + "; SHA256: " + digest(run / "packet.json") + "; run_id: " + session_id
    started = int(time.time() * 1000)
    print(json.dumps({"phase": "start", "run": str(run), "session_id": session_id, "role": "code-reviewer"}), flush=True)
    env = {**os.environ, "PATH": str(run / "bin") + os.pathsep + os.environ.get("PATH", ""),
           "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1", "PYTHONDONTWRITEBYTECODE": "1"}
    result = subprocess.run(command, input=prompt, text=True, capture_output=True, cwd=workspace, env=env, timeout=args.timeout)
    (run / "stdout.jsonl").write_text(result.stdout)
    (run / "stderr.log").write_text(result.stderr)
    unchanged = all(digest(path) == sha for path, sha in before.items()) and all((repo / name).is_file() and digest(repo / name) == sha for name, sha in snapshot.items())
    report = {"phase": "execution_complete", "exit_code": result.returncode, "session_id": session_id, "started_ms": started,
              "ended_ms": int(time.time() * 1000), "snapshot_unchanged": unchanged, "protected_before": before,
              "main_write_permission": permission_query(os.getpid(), probe, "file-write-data"),
              "kernel_record_exists": (run / "kernel-permissions.json").is_file(),
              "scope": "execution only; actual routing/effort, full contract reads and product verdict require recorded evidence"}
    save(run / "execution.json", report)
    print(json.dumps({key: report[key] for key in ("phase", "exit_code", "session_id", "snapshot_unchanged", "kernel_record_exists")}), flush=True)
    return 0 if result.returncode == 0 and unchanged and report["kernel_record_exists"] else 1


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--launch":
        raise SystemExit(launch(sys.argv[2], sys.argv[3:]))
    raise SystemExit(main())
