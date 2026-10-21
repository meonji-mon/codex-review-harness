"""Selection previews and metadata only: no login, inference, or file mutation."""
import contextlib
import io
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import model_selection as selection
import run_code_review as runner


def catalog():
    models = ["ocx-claude-native--gpt-6-astra", "ocx-claude-native--gpt-6.1-sol",
              "claude-sonnet-5-5", "claude-opus-5-5", "ocx-claude-xai--grok-4.7", "ocx-claude-combo--laya-auto"]
    return {"available": models, "models": [{"id": model, "label": model,
            "review_eligible": selection.review_eligible(model), "instruction_only": "grok" in model} for model in models]}


def role():
    return runner.role_definition(ROOT / "agents/code-reviewer.md")


class SelectionTests(unittest.TestCase):
    def test_user_can_select_sol_sonnet_or_opus_without_changing_permissions(self):
        original = role()
        for model in ["ocx-claude-native--gpt-6.1-sol", "claude-sonnet-5-5", "claude-opus-5-5"]:
            with self.subTest(model=model):
                chosen = selection.select_reviewer(original, model, "medium", catalog())["code-reviewer"]
                self.assertEqual(chosen["model"], model)
                self.assertEqual(chosen["effort"], "medium")
                self.assertEqual(chosen["tools"], ["Read", "Grep", "Glob"])
                self.assertEqual(chosen["disallowedTools"], original["code-reviewer"]["disallowedTools"])
        self.assertEqual(original["code-reviewer"]["model"], "ocx-claude-native--gpt-6-astra")

    def test_model_and_effort_are_independent_and_defaults_survive(self):
        original = role()
        chosen = selection.select_reviewer(original, effort="max", catalog=catalog())["code-reviewer"]
        self.assertEqual(chosen["model"], original["code-reviewer"]["model"])
        self.assertEqual(chosen["effort"], "max")
        chosen = selection.select_reviewer(original, model="claude-sonnet-5-5", catalog=catalog())["code-reviewer"]
        self.assertEqual(chosen["effort"], original["code-reviewer"]["effort"])

    def test_unknown_model_is_not_silently_substituted(self):
        with self.assertRaises(ValueError):
            selection.select_reviewer(role(), model="unavailable-model", catalog=catalog())

    def test_instruction_only_and_automatic_routes_cannot_be_code_reviewers(self):
        for model in ["ocx-claude-xai--grok-4.7", "ocx-claude-combo--laya-auto"]:
            with self.subTest(model=model), self.assertRaises(ValueError):
                selection.select_reviewer(role(), model=model, catalog=catalog())

    def test_non_effort_workflow_or_unsupported_level_is_rejected(self):
        for level in ["ultra", "ultracode", "unknown"]:
            with self.subTest(level=level), self.assertRaises(ValueError):
                selection.select_reviewer(role(), effort=level, catalog=catalog())

    def test_picker_adds_choices_without_fabricated_capabilities_or_defaults(self):
        result = selection.picker_settings(catalog())
        self.assertEqual(set(result), {"modelPicker"})
        self.assertFalse(result["modelPicker"]["replaceBuiltInOptions"])
        for row in result["modelPicker"]["options"]:
            self.assertEqual(set(row), {"model", "label"})
        self.assertIn("instruction writing only", next(row["label"] for row in result["modelPicker"]["options"] if "grok" in row["model"]))

    def test_catalog_queries_metadata_not_a_model(self):
        data={"available": ["gpt-6-astra"], "aliases": [{"id": "ocx-claude-native--gpt-6-astra", "display_name": "Astra"}]}
        with patch.object(selection.subprocess, "run", return_value=SimpleNamespace(returncode=0, stdout=json.dumps(data))) as call:
            result=selection.read_catalog()
        self.assertEqual(call.call_args.args[0], ["ocx", "claude", "config", "status", "--json"])
        self.assertFalse(result["runtime_model_effort_verified"])

    def test_cli_preview_never_launches_a_model_or_creates_run_state(self):
        args=["run_code_review.py", "--reviewer-model", "claude-sonnet-5-5", "--reviewer-effort", "max", "--show-selection"]
        with patch.object(sys, "argv", args), patch.object(selection, "read_catalog", return_value=catalog()), \
             patch.object(selection.subprocess, "run", side_effect=AssertionError("no process/model call allowed")), \
             patch.object(Path, "mkdir", side_effect=AssertionError("no run state allowed")), \
             contextlib.redirect_stdout(io.StringIO()) as out:
            result=runner.main()
        shown=json.loads(out.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(shown["requested_model"], "claude-sonnet-5-5")
        self.assertEqual(shown["requested_effort"], "max")
        self.assertEqual(shown["tools"], ["Read", "Grep", "Glob"])
        self.assertFalse(shown["runtime_verified"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
