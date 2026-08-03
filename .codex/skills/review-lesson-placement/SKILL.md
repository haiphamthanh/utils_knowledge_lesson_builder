---
name: review-lesson-placement
description: Audit an existing Knowledge Lesson Builder lesson without changing files. Use when the user asks whether a lesson belongs in the correct cookbook, learning path, chapter, core/optional/graph-only role, or prerequisite order, or whether earlier knowledge is sufficient without becoming excessive.
---

# Review Lesson Placement

1. Locate the project root containing `build.sh`, `knowledge/`, and
   `guidelines/`.
2. Read `AGENTS.md`, `guidelines/knowledge-model.md`,
   `guidelines/authoring.md`, and the target lesson.
3. Resolve the cookbook and lesson ID. If either is ambiguous, list the exact
   matches and ask the user to choose; do not guess.
4. Inspect the cookbook metadata, graph, every path that references the lesson,
   and the metadata and headings of nearby lessons.
5. Check structural evidence:
   - the lesson ID, filename, and graph node agree;
   - every graph relation uses an existing lesson and the most specific type;
   - each path placement has a clear chapter and `core` or `optional` role;
   - absence from all paths is reported as `graph-only`, not as an automatic
     error.
6. Run `./build.sh validate <cookbook> --path <path>` for each affected path.
   Add `--include-optional` when reviewing optional placement and
   `--include-draft` only when the target is a draft.
7. Review prerequisite sufficiency:
   - every true `requires` target appears before the lesson;
   - relations such as `builds_on`, `related_to`, and `leads_to` do not force
     path order;
   - a core lesson does not rely on optional knowledge;
   - no prerequisite is added merely because two topics are related.
8. Review pedagogy separately from machine validation: fit with chapter
   objective, depth, progressive disclosure, continuity from the previous and
   next lesson, and whether the chapter stays near 5–8 core lessons or fewer.
9. Return a table with `Check`, `Evidence`, `Result`, and `Recommendation`.
   Label subjective judgments as editorial review and validation failures as
   structural errors.

Stay read-only. Do not edit the lesson, graph, path, or cookbook. If the user
later asks for a fix, propose the smallest exact change set and require explicit
confirmation before writing. Never generate path order from the graph.
