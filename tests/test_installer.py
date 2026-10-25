"""Exercise installation against temporary fake runtimes, never the user's Steam files."""
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[1] / "guest/install_fex.py"
spec = importlib.util.spec_from_file_location("install_fex", SCRIPT)
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.target = self.root / "Steam/FEX-Emu"
        self.stage = self.root / "stage"
        self.state = self.root / "state"
        self.tools = self.root / "tools"
        self.tools.mkdir()
        self.pgrep = self.tools / "pgrep"
        self.pgrep.write_text("#!/bin/sh\nexit 1\n")
        self.pgrep.chmod(0o755)
        self.env = dict(os.environ, FEX_TOOL_DIR=str(self.target), STAGE=str(self.stage),
                        STATE_DIR=str(self.state), PATH=str(self.tools) + os.pathsep + os.environ["PATH"])
        for root, label in ((self.target, "original"), (self.stage, "patched")):
            for rel in installer.FILES:
                path = root / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(label + " " + rel)
                path.chmod(0o755 if rel.startswith("usr/bin/") else 0o644)
        self.unrelated = self.target / "unrelated-file"
        self.unrelated.write_text("leave this alone")

    def run_installer(self, action="install", ok=True):
        result = subprocess.run([sys.executable, str(SCRIPT), action], env=self.env, capture_output=True, text=True)
        self.assertEqual(result.returncode == 0, ok, result.stdout + result.stderr)
        return result

    def assert_runtime(self, root, label):
        for rel in installer.FILES:
            self.assertEqual((root / rel).read_text(), label + " " + rel)
        self.assertTrue(os.access(root / "usr/bin/FEX", os.X_OK))

    def test_install_repeat_and_restore(self):
        self.run_installer()
        self.assert_runtime(self.target, "patched")
        self.assert_runtime(self.state / "original-fex", "original")
        self.run_installer()
        self.assert_runtime(self.state / "original-fex", "original")
        self.run_installer("restore")
        self.assert_runtime(self.target, "original")
        self.assertEqual(self.unrelated.read_text(), "leave this alone")

    def test_incomplete_stage_cannot_change_runtime(self):
        (self.stage / "ConfigTemplate.json").unlink()
        self.run_installer(ok=False)
        self.assert_runtime(self.target, "original")
        self.assertFalse((self.state / "original-fex").exists())

    def test_restore_without_backup_is_safe(self):
        self.run_installer("restore", ok=False)
        self.assert_runtime(self.target, "original")

    def test_active_game_blocks_install_and_restore(self):
        self.pgrep.write_text("#!/bin/sh\nexit 0\n")
        self.run_installer(ok=False)
        self.assert_runtime(self.target, "original")
        self.pgrep.write_text("#!/bin/sh\nexit 1\n")
        self.run_installer()
        self.pgrep.write_text("#!/bin/sh\nexit 0\n")
        self.run_installer("restore", ok=False)
        self.assert_runtime(self.target, "patched")

    def test_copy_error_rolls_back_partial_install(self):
        original_copy = shutil.copy2

        def fail_second_binary(source, destination, *args, **kwargs):
            if Path(source) == self.stage / "usr/bin/FEXBash":
                raise OSError("simulated copy failure")
            return original_copy(source, destination, *args, **kwargs)

        with mock.patch.dict(os.environ, self.env), mock.patch.object(sys, "argv", [str(SCRIPT)]), \
             mock.patch.object(installer.shutil, "copy2", side_effect=fail_second_binary):
            with self.assertRaisesRegex(OSError, "simulated"):
                installer.main()
        self.assert_runtime(self.target, "original")
        self.assert_runtime(self.state / "original-fex", "original")

    def test_status_does_not_create_state(self):
        self.run_installer("status")
        self.assertFalse(self.state.exists())
        self.assert_runtime(self.target, "original")


if __name__ == "__main__":
    unittest.main()
