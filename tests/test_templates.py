from pathlib import Path
import tempfile
import unittest

import yaml

from scripts.builder import _asset_values
from scripts.models import BuilderError
from scripts.template_cli import list_templates, templates_as_table


ROOT = Path(__file__).resolve().parent.parent


class TemplateTests(unittest.TestCase):
    def test_registry_lists_available_templates(self) -> None:
        templates = list_templates(ROOT)
        ids = {template["id"] for template in templates}
        self.assertTrue(
            {
                "default",
                "chapter-lesson",
                "clean",
                "academic",
                "editorial",
                "editorial-banner",
                "editorial-study",
            }
            <= ids
        )
        self.assertIn("chapter-lesson", templates_as_table(templates))

    def test_stylesheet_and_header_include_accept_string_or_list(self) -> None:
        self.assertEqual(_asset_values("theme.css", "stylesheet"), ["theme.css"])
        self.assertEqual(
            _asset_values(["base.css", "theme.css"], "stylesheet"),
            ["base.css", "theme.css"],
        )
        with self.assertRaisesRegex(BuilderError, "string hoặc list string"):
            _asset_values(["theme.css", 1], "stylesheet")

    def test_ornate_themes_use_standalone_pdf_templates(self) -> None:
        for template_id in ("editorial-banner", "editorial-study"):
            template_dir = ROOT / "templates" / template_id
            manifest = yaml.safe_load(
                (template_dir / "template.yml").read_text(encoding="utf-8")
            )
            self.assertEqual(
                manifest["formats"]["pdf"]["template"], "pdf-template.tex"
            )
            self.assertTrue((template_dir / "pdf-template.tex").is_file())

    def test_registry_ignores_manifest_with_mismatched_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest_dir = root / "templates" / "wrong-directory"
            manifest_dir.mkdir(parents=True)
            (manifest_dir / "template.yml").write_text(
                "id: actual-id\nformats: {}\n", encoding="utf-8"
            )
            self.assertEqual(list_templates(root), [])


if __name__ == "__main__":
    unittest.main()
