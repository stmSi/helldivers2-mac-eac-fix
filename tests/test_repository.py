import hashlib
import json
from pathlib import Path
import re
import unittest
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]


class RepositoryTests(unittest.TestCase):
    def test_patch_checksums(self):
        versions = json.loads((ROOT / "versions.json").read_text())
        for name, key in (("fex-hd2.patch", "fex_patch_sha256"), ("fx-ctrl-g.patch", "fx_shortcut_patch_sha256")):
            self.assertEqual(hashlib.sha256((ROOT / "patches" / name).read_bytes()).hexdigest(), versions[key])

    def test_relative_document_links(self):
        for path in [ROOT / "README.md", *(ROOT / "docs").glob("*.md")]:
            for target in re.findall(r"\]\(([^)]+)\)", path.read_text()):
                if "://" in target or target.startswith("#"):
                    continue
                self.assertTrue((path.parent / unquote(target.split("#")[0])).exists(), f"{path.name}: {target}")

    def test_no_machine_paths_in_public_scripts(self):
        paths = [*(ROOT / "scripts").glob("*.py"), *(ROOT / "scripts").glob("*.sh"),
                 *(ROOT / "guest").glob("*"), *ROOT.glob("*.command")]
        for path in paths:
            if path.is_file():
                text = path.read_text()
                self.assertNotRegex(text, r"/Users/[^/]+/", str(path))
                self.assertNotRegex(text, r"userdata/[0-9]+/", str(path))
                self.assertNotIn("PRIVATE KEY-----", text, str(path))


if __name__ == "__main__":
    unittest.main()
