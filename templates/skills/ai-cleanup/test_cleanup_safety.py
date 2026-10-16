"""Non-destructive regression checks: real policy queries, memory-only move I/O."""
import contextlib
import copy
import errno
import io
import json
import os
from pathlib import Path
import stat
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch, mock_open
import tomllib

import ai_cleanup as cleanup
import cleanup_safety as safety


def example_snapshot():
    return {"schema": 2, "identity_sha256": "identity", "content_sha256": "content",
            "root": [1, 2, stat.S_IFREG | 0o600, 3, 100, 100, 1], "parent": [1, 3],
            "newest_mtime_ns": 100, "logical_bytes": 3, "entry_count": 1}


class PolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = tomllib.loads((Path(__file__).parent / "cleanup.example.toml").read_text())

    def test_registered_protected_child_blocks_its_ancestor(self):
        cfg = {"never_touch": {"paths": ["/example/work/recovery"]}}
        self.assertIsNotNone(safety.SharedProtection(cfg).reason("/example/work"))

    @unittest.skipUnless(os.environ.get("CLEANUP_TEST_LIVE_MOLE") == "1", "opt-in read-only Mole integration")
    def test_actual_mole_policy_protects_new_ide_versions(self):
        policy = safety.SharedProtection(self.cfg)
        home = str(Path.home())
        self.assertIsNotNone(policy.reason(home + "/Library/Caches/Google/AndroidStudio2099.1"))
        self.assertIsNotNone(policy.reason(home + "/Library/Application Support/Google/AndroidStudio2099.1"))
        self.assertIsNotNone(policy.reason(home + "/Library/Caches/JetBrains/Idea2099.1"))
        self.assertIsNone(policy.reason("/private/tmp/cleanup-policy-eligible-example"))

    def test_missing_required_shared_rule_holds_cleanup(self):
        cfg = copy.deepcopy(self.cfg)
        cfg["protection"]["required_mole_patterns"].append("/required-but-unregistered-example")
        with patch.object(Path, "read_bytes", return_value=b""), self.assertRaises(safety.SafetyError):
            safety.SharedProtection(cfg).reason("/private/tmp/eligible-example")

    def test_recovery_and_git_state_components_are_protected(self):
        for path in ["/example/LocalHistory/data", "/example/.idea/shelf/change", "/example/.git/index",
                     "/example/User/History/change", "/example/graphify-out/index"]:
            with self.subTest(path=path):
                self.assertTrue(safety.recovery_component(path))

    def test_git_lookup_errors_are_not_treated_as_untracked(self):
        with patch.object(cleanup, "run", return_value=None):
            with self.assertRaises(safety.SafetyError):
                cleanup.git_root("/example/source.txt")


class SnapshotTests(unittest.TestCase):
    def memory_file(self, data, inode=2, mtime=100):
        node = SimpleNamespace(st_uid=safety.os.getuid(), st_dev=1, st_ino=inode,
                               st_mode=stat.S_IFREG | 0o600, st_size=len(data),
                               st_mtime_ns=mtime, st_ctime_ns=100, st_nlink=1)
        parent = SimpleNamespace(st_dev=1, st_ino=3)
        with patch.object(safety.os.path, "islink", return_value=False), \
             patch.object(safety.os, "lstat", return_value=node), \
             patch.object(safety.os, "stat", return_value=parent), \
             patch.object(safety.os, "open", return_value=123), \
             patch.object(safety.os, "fstat", return_value=node), \
             patch.object(safety.os, "read", side_effect=[data, b""]), \
             patch.object(safety.os, "close"):
            return safety.snapshot("/memory/source")

    def test_content_changes_with_identical_metadata_are_detected(self):
        a, b = self.memory_file(b"old"), self.memory_file(b"new")
        self.assertNotEqual(a["identity_sha256"], b["identity_sha256"])
        self.assertNotEqual(a["content_sha256"], b["content_sha256"])

    def test_inode_and_subsecond_metadata_changes_are_detected(self):
        a = self.memory_file(b"old")
        self.assertNotEqual(a["identity_sha256"], self.memory_file(b"old", inode=9)["identity_sha256"])
        self.assertNotEqual(a["identity_sha256"], self.memory_file(b"old", mtime=101)["identity_sha256"])

    def test_symlinks_are_refused_before_reading(self):
        with patch.object(safety.os.path, "islink", return_value=True), patch.object(safety.os, "open") as opened:
            with self.assertRaises(safety.SafetyError):
                safety.snapshot("/memory/link")
            opened.assert_not_called()

    def test_real_source_snapshot_is_read_only(self):
        a = safety.snapshot(__file__)
        b = safety.snapshot(__file__)
        self.assertEqual(a, b)
        self.assertEqual(a["entry_count"], 1)

    def test_recent_empty_subdirectory_is_included_in_tree_age(self):
        def node(inode, mtime):
            return SimpleNamespace(st_uid=safety.os.getuid(), st_dev=1, st_ino=inode,
                                   st_mode=stat.S_IFDIR | 0o700, st_size=64,
                                   st_mtime_ns=mtime, st_ctime_ns=mtime, st_nlink=2)
        nodes = {"/memory/source": node(2, 100), "/memory/source/child": node(3, 999)}
        def scan(path):
            entries = [SimpleNamespace(path="/memory/source/child")] if path == "/memory/source" else []
            return contextlib.nullcontext(iter(entries))
        with patch.object(safety, "canonical", return_value="/memory-parent"), \
             patch.object(safety.os.path, "islink", return_value=False), \
             patch.object(safety.os, "lstat", side_effect=lambda path: nodes[str(path)]), \
             patch.object(safety.os, "stat", return_value=SimpleNamespace(st_dev=1, st_ino=9)), \
             patch.object(safety.os, "scandir", side_effect=scan):
            result = safety.snapshot("/memory/source")
        self.assertEqual(result["newest_mtime_ns"], 999)
        self.assertEqual(result["entry_count"], 2)


class JournalTests(unittest.TestCase):
    def operation(self):
        entry = {"from": "/memory/original", "to": "/memory/trash", "fingerprint": example_snapshot()}
        return {"items": [entry]}, entry

    def test_intent_is_durable_before_transfer_and_commit_follows_verify(self):
        record, entry = self.operation(); events = []; durable = []
        def persist(data):
            durable.append(copy.deepcopy(data)); events.append("persist:" + entry["status"])
        def transfer():
            self.assertEqual(durable[-1]["items"][0]["status"], "intent")
            events.append("transfer")
        done = safety.recorded_transfer(record, entry, persist,
                                        lambda: events.append("recheck"), transfer,
                                        lambda: events.append("verify"))
        self.assertTrue(done)
        self.assertEqual(events, ["persist:intent", "recheck", "transfer", "verify", "persist:moved"])

    def test_intent_write_failure_prevents_transfer(self):
        record, entry = self.operation(); transfer = Mock()
        with self.assertRaises(OSError):
            safety.recorded_transfer(record, entry, Mock(side_effect=OSError("disk full")),
                                     lambda: None, transfer, Mock())
        transfer.assert_not_called()

    def test_changed_source_is_held_after_intent_without_moving(self):
        record, entry = self.operation(); transfer = Mock(); durable = []
        result = safety.recorded_transfer(record, entry, lambda data: durable.append(copy.deepcopy(data)),
                                          lambda: "source changed", transfer, Mock())
        self.assertFalse(result); transfer.assert_not_called()
        self.assertEqual(durable[-1]["items"][0]["status"], "held")

    def test_commit_write_failure_leaves_recoverable_intent(self):
        record, entry = self.operation(); durable = []; transfer = Mock()
        def persist(data):
            if entry["status"] == "moved": raise OSError("journal commit failed")
            durable.append(copy.deepcopy(data))
        with self.assertRaises(OSError):
            safety.recorded_transfer(record, entry, persist, lambda: None, transfer, Mock())
        transfer.assert_called_once()
        saved = durable[-1]["items"][0]
        self.assertEqual(saved["status"], "intent")
        self.assertEqual(safety.restoration_state(saved, None, example_snapshot()), "ready")

    def test_post_move_failure_is_attention_not_success(self):
        record, entry = self.operation(); durable = []
        with self.assertRaises(safety.SafetyError):
            safety.recorded_transfer(record, entry, lambda data: durable.append(copy.deepcopy(data)),
                                     lambda: None, Mock(), Mock(side_effect=safety.SafetyError("hash mismatch")))
        self.assertEqual(durable[-1]["items"][0]["status"], "attention")

    def test_recovery_refuses_conflicts_missing_and_changed_payload(self):
        _, entry = self.operation(); fp = example_snapshot(); changed = copy.deepcopy(fp)
        changed["content_sha256"] = "changed"
        self.assertEqual(safety.restoration_state(entry, fp, fp), "conflict")
        self.assertEqual(safety.restoration_state(entry, None, None), "missing")
        self.assertEqual(safety.restoration_state(entry, None, changed), "changed")
        self.assertEqual(safety.restoration_state(entry, fp, None), "at_original")
        self.assertEqual(safety.restoration_state({"from": "a", "to": "b"}, None, fp), "ready")

    def test_restore_has_its_own_intent_and_does_not_replace_move_history(self):
        record, entry = self.operation(); entry["status"] = "moved"; durable = []
        safety.recorded_transfer(record, entry, lambda data: durable.append(copy.deepcopy(data)),
                                 lambda: None, Mock(), Mock(), restoring=True)
        self.assertEqual(durable[0]["items"][0]["restore_status"], "intent")
        self.assertEqual(entry["restore_status"], "restored")
        self.assertEqual(entry["status"], "moved")

    def test_atomic_record_fsyncs_file_then_replacement_then_directory(self):
        events = []
        class MemoryStream(io.StringIO):
            def fileno(self): return 11
            def flush(self): events.append("flush")
            def close(self): pass
        parent = SimpleNamespace(st_uid=safety.os.getuid(), st_mode=stat.S_IFDIR | 0o700, st_dev=1, st_ino=9)
        with patch.object(Path, "is_symlink", return_value=False), patch.object(Path, "exists", return_value=False), \
             patch.object(safety.os, "open", side_effect=[10, 11]), \
             patch.object(safety.os, "fstat", return_value=parent), \
             patch.object(safety.os, "stat", return_value=parent), \
             patch.object(safety.os, "fdopen", return_value=MemoryStream()), \
             patch.object(safety.os, "fsync", side_effect=lambda fd: events.append("fsync:"+str(fd))), \
             patch.object(safety.os, "replace", side_effect=lambda *a, **k: events.append("replace")), \
             patch.object(safety.os, "close"):
            safety.atomic_record("/memory/restore.json", {"items": [{"status": "intent"}]})
        self.assertEqual(events, ["flush", "fsync:11", "replace", "fsync:10"])


class PipelineTests(unittest.TestCase):
    def test_restore_conflict_is_unresolved_and_does_not_transfer(self):
        fp = example_snapshot()
        entry = {"from": "/memory/original", "to": "/memory/trash/ai-cleanup-memory/files/payload", "fingerprint": fp}
        cfg = {"trash_dir": "/memory/trash", "trash_fallback_dir": "/memory/fallback"}
        with patch.object(cleanup.os.path, "exists", return_value=True), \
             patch.object(cleanup.os.path, "lexists", return_value=True), \
             patch.object(cleanup.os.path, "islink", return_value=False), \
             patch.object(cleanup, "journal_lock", return_value=contextlib.nullcontext()), \
             patch('builtins.open', mock_open(read_data=json.dumps({"items": [entry]}))), \
             patch.object(cleanup, "snapshot", return_value=fp), patch.object(cleanup, "log"), \
             patch.object(cleanup, "recorded_transfer") as transfer, contextlib.redirect_stdout(io.StringIO()) as output:
            result = cleanup.restore(cfg, SimpleNamespace(id="memory"))
        self.assertEqual(result, 4)
        self.assertFalse(json.loads(output.getvalue())["ok"])
        transfer.assert_not_called()

    def test_legacy_restore_preserves_history_and_commits_verified_result(self):
        original = "/memory/original"; payload = "/memory/trash/ai-cleanup-memory/files/payload"
        fp = example_snapshot(); state = {original: None, payload: fp}; durable = []
        entry = {"from": original, "to": payload, "size": 3, "category": "scratch"}
        cfg = {"trash_dir": "/memory/trash", "trash_fallback_dir": "/memory/fallback"}
        def relocate(src, dst, expected):
            self.assertIsNone(state[dst]); state[dst] = state[src]; state[src] = None
        with patch.object(cleanup.os.path, "exists", return_value=True), \
             patch.object(cleanup.os.path, "lexists", side_effect=lambda p: state.get(p) is not None), \
             patch.object(cleanup.os.path, "islink", return_value=False), patch.object(cleanup.os, "makedirs"), \
             patch.object(cleanup, "journal_lock", return_value=contextlib.nullcontext()), \
             patch('builtins.open', mock_open(read_data=json.dumps({"items": [entry]}))), \
             patch.object(cleanup, "snapshot", side_effect=lambda p, **kw: copy.deepcopy(state[str(p)])), \
             patch.object(cleanup, "rename_exclusive", side_effect=relocate), \
             patch.object(cleanup, "atomic_record", side_effect=lambda p, data: durable.append(copy.deepcopy(data))), \
             patch.object(cleanup, "log"), contextlib.redirect_stdout(io.StringIO()) as output:
            result = cleanup.restore(cfg, SimpleNamespace(id="memory"))
        self.assertEqual(result, 0)
        self.assertEqual(json.loads(output.getvalue())["restored"], 1)
        self.assertEqual([x["items"][0]["restore_status"] for x in durable], ["intent", "restored"])
        self.assertIn("unavailable", durable[-1]["items"][0]["legacy_identity_evidence"])

    def test_overlapping_destination_is_refused_before_journal_creation(self):
        with patch.object(cleanup, "journal_lock") as locked:
            with self.assertRaises(safety.SafetyError):
                cleanup.move_items({}, [{"path": "/memory/trash/run/source"}], "/memory/trash/run")
            locked.assert_not_called()

    def test_move_boundary_rechecks_source_after_journal_intent(self):
        item = {"path": "/memory/source", "size": 3, "category": "scratch", "fingerprint": example_snapshot()}
        durable = []
        with patch.object(cleanup, "journal_lock", return_value=contextlib.nullcontext()), \
             patch.object(cleanup.os, "makedirs"), \
             patch.object(cleanup.os.path, "exists", return_value=False), \
             patch.object(cleanup.os.path, "islink", return_value=False), \
             patch.object(cleanup, "check_item", side_effect=[None, "changed after first check"]), \
             patch.object(cleanup, "atomic_record", side_effect=lambda path, data: durable.append(copy.deepcopy(data))), \
             patch.object(cleanup, "rename_exclusive") as rename:
            moved, skipped = cleanup.move_items({}, [item], "/memory/trash/run")
        self.assertEqual(moved, []); self.assertEqual(len(skipped), 1)
        rename.assert_not_called()
        self.assertEqual([r["items"][0]["status"] for r in durable], ["intent", "held"])

    def test_old_plans_and_changed_policy_are_held(self):
        item = {"path": "/memory/source", "action": "trash"}
        with patch.object(cleanup, "protection_reason", return_value=None):
            self.assertIn("legacy", cleanup.check_item({}, item))
            item.update(fingerprint=example_snapshot(), policy_revision="old")
            with patch.object(cleanup, "protection", return_value=SimpleNamespace(revision=lambda: "new")):
                self.assertIn("protection changed", cleanup.check_item({}, item))

    def test_auto_reports_old_trash_without_permanent_deletion(self):
        cfg = {"auto": {}}
        args = SimpleNamespace(dry_run=False, force=False)
        output = io.StringIO()
        with patch.object(cleanup, "last_auto_run", return_value=None), \
             patch.object(cleanup, "plan", return_value=("/memory/plan", {"items": [], "plan_id": "memory"})), \
             patch.object(cleanup, "trash_root", return_value=("/memory/trash", None)), \
             patch.object(cleanup, "old_trash_candidates", return_value=[{"path": "old", "size": 1}]), \
             patch.object(cleanup, "log"), \
             patch.object(cleanup.shutil, "rmtree", side_effect=AssertionError("permanent deletion forbidden")), \
             patch.object(cleanup.os, "remove", side_effect=AssertionError("deletion forbidden")), \
             contextlib.redirect_stdout(output):
            self.assertEqual(cleanup.auto(cfg, args), 0)
        result = json.loads(output.getvalue())
        self.assertFalse(result["permanent_deletion_performed"])
        self.assertEqual(result["emptied"], [])
        self.assertEqual(len(result["old_trash_candidates"]), 1)


if __name__ == "__main__":
    unittest.main()
