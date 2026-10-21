#!/usr/bin/env python3
"""Supplementary hook checks. Never execute the command being inspected."""
import json
import os
import re
import shlex
import sys


class Unsupported(ValueError):
    pass


def tokens(command):
    if not isinstance(command, str) or not command.strip() or len(command) > 65536:
        raise Unsupported("missing or oversized command")
    if "$(" in command or "`" in command:
        raise Unsupported("command substitution needs manual inspection")
    lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|<>()\n")
    lexer.whitespace = " \t\r"
    lexer.whitespace_split = True
    lexer.commenters = "#"
    try:
        return list(lexer)
    except ValueError as error:
        raise Unsupported("unparsed shell quoting") from error


def executable(word):
    return os.path.basename(word)


def separator(word):
    return bool(word) and all(char in ";&|<>()\n" for char in word)


def git_args(words, readonly=False):
    index = 0
    value_options = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--super-prefix", "--config-env"}
    safe = {"--no-pager", "--no-optional-locks", "--literal-pathspecs"}
    while index < len(words) and words[index].startswith("-"):
        word = words[index]
        if word in value_options:
            if readonly and word != "-C":
                raise Unsupported("Git configuration overrides are not read-only inputs")
            if index + 1 >= len(words):
                raise Unsupported("incomplete Git global option")
            index += 2
        elif word.startswith(("-C", "-c", "--git-dir=", "--work-tree=", "--namespace=", "--config-env=")):
            if readonly and not word.startswith("-C"):
                raise Unsupported("Git configuration overrides are not read-only inputs")
            index += 1
        elif word in safe or not readonly:
            index += 1
        else:
            raise Unsupported("unsupported Git global option")
    if index == len(words):
        raise Unsupported("missing Git subcommand")
    return words[index], words[index + 1:]


def readonly_reason(command):
    words = tokens(command)
    if not words or any(separator(word) for word in words):
        return "compound commands and redirections are not allowed"
    if any("$" in word for word in words):
        return "shell expansion is not allowed"
    name = executable(words[0])
    if name in {"pwd", "ls", "cat", "head", "tail", "wc", "grep"}:
        return None
    if name == "git":
        try:
            sub, args = git_args(words[1:], readonly=True)
        except Unsupported as error:
            return str(error)
        if sub not in {"status", "diff", "log", "show", "ls-files", "rev-parse", "rev-list", "cat-file", "merge-base", "check-ignore", "count-objects"}:
            return "Git writes are not allowed"
        if any(arg.startswith(("--output", "--ext-diff", "--textconv", "--exec", "--paginate")) for arg in args):
            return "Git output/external-command options are not allowed"
        return None
    # Includes gh: field flags and GraphQL can imply writes without -X.
    return "only the documented local read-command allowlist is accepted"


def protected_backup(arg):
    return bool(re.match(r"^(?:refs/heads/|origin/)?backup/", arg))


def git_segment_reason(words, depth=0):
    if not words:
        return None
    if depth > 4:
        raise Unsupported("nested shell command")
    while words and (words[0] in {"command", "builtin", "exec", "--"} or re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", words[0])):
        words = words[1:]
    if not words:
        return None
    if executable(words[0]) == "env":
        words = words[1:]
        while words and (words[0].startswith("-") or re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", words[0])):
            words = words[2:] if words[0] in {"-u", "--unset", "-C", "--chdir"} else words[1:]
        return git_segment_reason(words, depth + 1)
    if words and executable(words[0]) in {"sh", "bash", "zsh"}:
        for index, word in enumerate(words[1:], 1):
            if word.startswith("-") and "c" in word[1:] and index + 1 < len(words):
                return git_reason(words[index + 1], depth + 1)
        return None
    if not words or executable(words[0]) != "git":
        return None
    sub, args = git_args(words[1:])
    if sub == "push":
        if any(arg in {"--force", "--force-with-lease", "--force-if-includes", "--mirror", "--prune"}
               or arg.startswith("--force-with-lease=") or re.match(r"^-[A-Za-z]*f[A-Za-z]*$", arg)
               or arg.startswith("+") for arg in args):
            return "force/pruning push"
        deleting = any(arg in {"-d", "--delete"} or arg.startswith("--delete=") for arg in args)
        if deleting and any(protected_backup(arg.split("=", 1)[-1]) for arg in args):
            return "backup/* remote deletion"
        if any(re.match(r"^:(?:refs/heads/)?backup/", arg) for arg in args):
            return "backup/* remote deletion"
    elif sub == "reset" and any(arg == "--hard" or arg.startswith("--hard=") for arg in args):
        return "git reset --hard"
    elif sub == "clean" and any(arg == "--force" or re.match(r"^-[A-Za-z]*f", arg) for arg in args):
        return "git clean -f"
    elif sub == "branch":
        deleting = any(arg == "--delete" or re.match(r"^-[A-Za-z]*[dD]", arg) for arg in args)
        if deleting and any(protected_backup(arg) for arg in args):
            return "backup/* local deletion"
    elif sub == "update-ref" and "-d" in args and any("backup/" in arg for arg in args):
        return "backup/* ref deletion"
    return None


def git_reason(command, depth=0):
    if not isinstance(command, str) or not command.strip():
        raise Unsupported("missing command")
    if not re.search(r"\bgit\b", command):
        return None
    segment = []
    for part in tokens(command) + [";"]:
        if separator(part):
            reason = git_segment_reason(segment, depth)
            if reason:
                return reason
            segment = []
        else:
            segment.append(part)
    return None


def main():
    try:
        data = json.load(sys.stdin)
        if not isinstance(data, dict) or not isinstance(data.get("tool_input"), dict):
            raise Unsupported("invalid hook input")
        command = data["tool_input"].get("command")
        mode = sys.argv[1]
        reason = readonly_reason(command) if mode == "readonly" else git_reason(command) if mode == "git" else "unknown guard mode"
    except (ValueError, TypeError, IndexError, KeyError) as error:
        reason = "guard could not validate input: " + str(error)
    if reason:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": reason}}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
