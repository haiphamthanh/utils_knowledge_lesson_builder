from pathlib import Path
import unittest

from scripts.core import create_plan
from scripts.builder import _document_options, _resolve_template_asset
from scripts.models import BuilderError, Chapter, Lesson
from scripts.validation import validate_path


ROOT = Path(__file__).resolve().parent.parent


class CorePlanTests(unittest.TestCase):
    def test_example_plan_is_valid(self) -> None:
        plan = create_plan(
            root=ROOT,
            cookbook_id="web-system-foundations",
            path_id=None,
            template_id=None,
            format_id=None,
            include_optional=False,
            include_draft=False,
        )

        self.assertEqual(plan.path_id, "foundation")
        self.assertEqual(plan.template_id, "chapter-lesson")
        self.assertEqual(plan.format_id, "html")
        self.assertEqual(
            plan.ordered_lesson_ids,
            ("request-response", "persistent-state", "relational-database"),
        )

    def test_path_rejects_prerequisite_after_dependent_lesson(self) -> None:
        lessons = {
            lesson_id: Lesson(
                id=lesson_id,
                title=lesson_id,
                depth="standard",
                status="complete",
                tags=(),
                path=ROOT / f"{lesson_id}.md",
                body=f"## {lesson_id}\n",
            )
            for lesson_id in ("foundation", "advanced")
        }
        chapters = (
            Chapter(
                id="core",
                title="Core",
                objective=("Hiểu đúng thứ tự",),
                context="",
                out_of_scope=(),
                core_lessons=("advanced", "foundation"),
                optional_lessons=(),
            ),
        )

        with self.assertRaisesRegex(BuilderError, "prerequisite"):
            validate_path(
                chapters=chapters,
                lessons=lessons,
                dependencies={"foundation": set(), "advanced": {"foundation"}},
                include_optional=False,
                include_draft=False,
            )

    def test_numbering_is_controlled_by_template(self) -> None:
        expected = {
            "default": (True, "--toc-depth=2"),
            "chapter-lesson": (False, "--toc-depth=2"),
            "clean": (False, "--toc-depth=2"),
            "academic": (True, "--toc-depth=3"),
        }
        for template_id, (numbered, toc_option) in expected.items():
            with self.subTest(template=template_id):
                plan = create_plan(
                    root=ROOT,
                    cookbook_id="web-system-foundations",
                    path_id=None,
                    template_id=template_id,
                    format_id="html",
                    include_optional=False,
                    include_draft=False,
                )
                options = _document_options(plan)
                self.assertEqual("--number-sections" in options, numbered)
                self.assertIn(toc_option, options)

    def test_template_can_reuse_assets_only_inside_templates_root(self) -> None:
        plan = create_plan(
            root=ROOT,
            cookbook_id="web-system-foundations",
            path_id=None,
            template_id="clean",
            format_id="html",
            include_optional=False,
            include_draft=False,
        )
        resolved = _resolve_template_asset(
            plan, "../default/book.css", "Stylesheet"
        )
        self.assertEqual(resolved, (ROOT / "templates/default/book.css").resolve())
        with self.assertRaisesRegex(BuilderError, "không hợp lệ"):
            _resolve_template_asset(plan, "../../README.md", "Stylesheet")


if __name__ == "__main__":
    unittest.main()
