"""Validate patch application against synthetic repositories, without the upstream checkout."""
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location("prepare_touch", Path(__file__).resolve().parents[1] / "scripts/prepare-touch.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class PatchTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="codex-touch-patch-test-")
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.project = self.root / "project"
        self.source = self.root / "source"
        self.source.mkdir()
        (self.project / "src").mkdir(parents=True)
        (self.project / "scripts").mkdir()
        (self.project / "scripts/prepare-lock.py").write_text("# Synthetic lock validation stub.\n")
        self.git("init", "-q")
        (self.source / "input.rs").write_text("before\n")
        self.git("add", "input.rs")
        self.git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", "base")
        commit = self.git("rev-parse", "HEAD").decode().strip()
        (self.project / "upstream.json").write_text(json.dumps({"commit": commit}))
        (self.source / "input.rs").write_text("after\n")
        (self.source / "new.rs").write_text("new module\n")
        self.git("add", "-N", "new.rs")
        (self.project / "src/async-question-touch.patch").write_bytes(self.git("diff", "HEAD"))
        self.git("reset", "-q")
        self.git("restore", "input.rs")
        (self.source / "new.rs").unlink()
        self.original_project = module.PROJECT
        module.PROJECT = self.project
        self.addCleanup(setattr, module, "PROJECT", self.original_project)

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.source), *args])

    def test_apply_check_and_repeat_preserve_real_index(self):
        index = (self.source / ".git/index").read_bytes()
        module.prepare(self.source)
        module.prepare(self.source, check=True)
        module.prepare(self.source)
        self.assertEqual((self.source / "input.rs").read_text(), "after\n")
        self.assertEqual((self.source / "new.rs").read_text(), "new module\n")
        self.assertEqual((self.source / ".git/index").read_bytes(), index)

    def test_check_is_read_only(self):
        with self.assertRaises(ValueError):
            module.prepare(self.source, check=True)
        self.assertEqual((self.source / "input.rs").read_text(), "before\n")
        self.assertFalse((self.source / "new.rs").exists())

    def test_modified_target_is_not_overwritten(self):
        (self.source / "input.rs").write_text("user changes\n")
        with self.assertRaisesRegex(ValueError, "Local edits"):
            module.prepare(self.source)
        self.assertEqual((self.source / "input.rs").read_text(), "user changes\n")
        self.assertFalse((self.source / "new.rs").exists())

    def test_preexisting_new_path_is_not_overwritten(self):
        (self.source / "new.rs").write_text("user module\n")
        with self.assertRaisesRegex(ValueError, "already exists"):
            module.prepare(self.source)
        self.assertEqual((self.source / "input.rs").read_text(), "before\n")
        self.assertEqual((self.source / "new.rs").read_text(), "user module\n")

    def test_unrelated_file_rejected(self):
        (self.source / "unrelated").write_text("keep\n")
        with self.assertRaisesRegex(ValueError, "Unrelated"):
            module.prepare(self.source)
        self.assertEqual((self.source / "input.rs").read_text(), "before\n")

    def test_wrong_commit_rejected(self):
        (self.project / "upstream.json").write_text(json.dumps({"commit": "0"*40}))
        with self.assertRaisesRegex(ValueError, "commit"):
            module.prepare(self.source)


if __name__ == "__main__":
    unittest.main()
