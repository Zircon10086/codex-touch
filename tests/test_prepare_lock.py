"""Ensure release-version preparation cannot update external dependencies."""

import hashlib
import importlib.util
import tempfile
import tomllib
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "prepare_lock", Path(__file__).resolve().parents[1] / "scripts/prepare-lock.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

ORIGINAL = b'''version = 4

[[package]]
name = "local"
version = "0.0.0"
dependencies = ["external"]

[[package]]
name = "external"
version = "0.0.0"
source = "registry+https://github.com/rust-lang/crates.io-index"
checksum = "fixed"
'''


class PrepareLockTests(unittest.TestCase):
    def test_external_dependency_is_unchanged(self):
        before = tomllib.loads(ORIGINAL.decode())
        after = tomllib.loads(module.normalize_local_versions(ORIGINAL, "0.169.0").decode())
        self.assertEqual(after["package"][0]["version"], "0.169.0")
        self.assertEqual(after["package"][0]["dependencies"], before["package"][0]["dependencies"])
        self.assertEqual(after["package"][1], before["package"][1])

    def test_prepare_check_and_idempotence(self):
        expected = module.normalize_local_versions(ORIGINAL, "0.169.0")
        pin = {
            "lockfile_upstream_sha256": hashlib.sha256(ORIGINAL).hexdigest(),
            "lockfile_build_sha256": hashlib.sha256(expected).hexdigest(),
        }
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "Cargo.lock"
            path.write_bytes(ORIGINAL)
            with self.assertRaises(ValueError):
                module.prepare(path, pin, "0.169.0", check_only=True)
            self.assertEqual(path.read_bytes(), ORIGINAL)
            self.assertTrue(module.prepare(path, pin, "0.169.0"))
            self.assertFalse(module.prepare(path, pin, "0.169.0", check_only=True))
            self.assertFalse(module.prepare(path, pin, "0.169.0"))

    def test_rejects_unknown_input_and_wrong_output_hash(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "Cargo.lock"
            path.write_bytes(ORIGINAL)
            for original_hash in ["0" * 64, hashlib.sha256(ORIGINAL).hexdigest()]:
                with self.assertRaises(ValueError):
                    module.prepare(path, {
                        "lockfile_upstream_sha256": original_hash,
                        "lockfile_build_sha256": "1" * 64,
                    }, "0.169.0")
                self.assertEqual(path.read_bytes(), ORIGINAL)


if __name__ == "__main__":
    unittest.main()
