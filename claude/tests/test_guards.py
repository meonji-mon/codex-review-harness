"""Regression inputs are inspected as strings, never executed as shell commands."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("harness_guard", ROOT / "hooks/harness/guard.py")
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


class ReadonlyTests(unittest.TestCase):
    def test_plain_local_reads_remain_available(self):
        for command in ["pwd", "/bin/cat 'file with spaces'", "head -n 5 file", "git --no-optional-locks -C /example diff --no-ext-diff --no-textconv", "/usr/bin/git log -3"]:
            with self.subTest(command=command):
                self.assertIsNone(guard.readonly_reason(command))

    def test_interpreters_and_mutating_commands_are_rejected(self):
        for command in ["python3 -c 'open(\"file\",\"w\").write(\"data\")'", "node -e 'process.exit()'", "git add file", "/usr/bin/git -C /example commit -m x", "rm file", "cat file > other"]:
            with self.subTest(command=command):
                self.assertIsNotNone(guard.readonly_reason(command))

    def test_implicit_post_graphql_and_read_prefix_bypasses_are_rejected(self):
        for command in ["gh api repos/example/repo/issues -f title=x", "gh api graphql -f query=mutation", "gh pr view 1; rm file", "gh pr view 1 && git push --force", "cat file\nrm file", "cat file | python3 script.py"]:
            with self.subTest(command=command):
                self.assertIsNotNone(guard.readonly_reason(command))

    def test_git_external_configuration_and_output_writes_are_rejected(self):
        for command in ["git -c core.pager=command log", "git diff --output=file", "git show --textconv HEAD", "git diff --ext-diff"]:
            with self.subTest(command=command):
                self.assertIsNotNone(guard.readonly_reason(command))


class GitTests(unittest.TestCase):
    def test_absolute_paths_global_options_and_wrappers_cannot_hide_force(self):
        for command in ["git push --force", "/usr/bin/git push -f", "/usr/bin/git --git-dir /example/.git push --force-with-lease", "command /usr/bin/git -C /example push +main", "env LANG=C /usr/bin/git push --mirror", "bash -lc '/usr/bin/git push --force'", "git status; /usr/bin/git push -f", "git status\n/usr/bin/git push -f"]:
            with self.subTest(command=command):
                self.assertIsNotNone(guard.git_reason(command))

    def test_destructive_and_backup_deletion_spellings_are_rejected(self):
        for command in ["/usr/bin/git reset --hard", "git clean -xdf", "git branch -D backup/user", "git branch -rd origin/backup/user", "git push origin --delete backup/user", "git push origin :refs/heads/backup/user", "git update-ref -d refs/heads/backup/user", "git push origin --prune"]:
            with self.subTest(command=command):
                self.assertIsNotNone(guard.git_reason(command))

    def test_ordinary_main_work_and_owned_branch_operations_are_not_newly_blocked(self):
        for command in ["git status", "git add -- file", "git commit -m 'ordinary change'", "git push origin main", "git branch -d codex/merged", "git push origin --delete codex/merged", "python3 script.py", "echo '/usr/bin/git push --force'"]:
            with self.subTest(command=command):
                self.assertIsNone(guard.git_reason(command))

    def test_ambiguous_substitution_is_not_silently_accepted(self):
        with self.assertRaises(guard.Unsupported):
            guard.git_reason('$(command -v git) push -f')


class HookProtocolTests(unittest.TestCase):
    def call(self, name, payload):
        result = subprocess.run(["/bin/bash", str(ROOT / "hooks/harness" / name)], input=payload, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout) if result.stdout else None

    def test_actual_hook_protocol_denies_invalid_input_and_dangerous_strings(self):
        for name in ["git-guard.sh", "reviewer-readonly-guard.sh"]:
            for payload in ["not JSON", "{}", json.dumps({"tool_input": {"command": "/usr/bin/git push --force"}})]:
                with self.subTest(name=name, payload=payload):
                    response = self.call(name, payload)
                    self.assertEqual(response["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_actual_hook_protocol_accepts_a_read_without_running_it(self):
        self.assertIsNone(self.call("reviewer-readonly-guard.sh", json.dumps({"tool_input": {"command": "cat /example/this-file-does-not-exist"}})))


if __name__ == "__main__":
    unittest.main(verbosity=2)
