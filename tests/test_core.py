from pathlib import Path
import unittest

from scripts.core import create_plan
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
        self.assertEqual(plan.template_id, "default")
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


if __name__ == "__main__":
    unittest.main()
