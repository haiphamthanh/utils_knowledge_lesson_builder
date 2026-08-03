---
name: promote-pool-lesson
description: Convert a reviewed resource item from resource/pool into a structured Knowledge Lesson Builder lesson. Use when the user asks to list pool candidates, choose one source, propose its cookbook/lesson/graph/path placement, require confirmation, create the lesson, validate it, and move the source to resource/done.
---

# Promote Pool Lesson

1. Locate the project root containing `build.sh` and `resource/index.yml`.
2. Read `AGENTS.md` and every project document under `guidelines/` that it
   requires.
3. Run `python <skill-dir>/scripts/list_pool.py --project <root>`.
4. Present the returned candidates and ask the user to choose one. Stop if the
   pool is empty.
5. Read the selected file or the relevant files inside the selected directory.
   Inspect `knowledge/<cookbook>/cookbook.yml`, its graph, paths, lesson
   template, and nearby lessons.
6. Propose one concrete change set: title, stable lesson ID, depth, target
   cookbook, graph relations, and `core`, `optional`, or `graph-only` placement.
   Require explicit confirmation before writing or moving anything.
7. After confirmation:
   - Run `./build.sh create-lesson <cookbook> <lesson-id> --title <title> --depth <depth>`.
   - Replace the scaffold with source-grounded content that follows
     `templates/lesson.md`; set status to `review`.
   - Add only confirmed graph relations. Add path placement only for `core` or
     `optional`; leave a `graph-only` lesson out of every path.
   - Change `cookbook.yml` only when its metadata or defaults genuinely need to
     change. Never store lesson order there.
   - Run unit tests, cookbook validation, and one affected build.
   - Run `./build.sh resource complete <resource-id> --cookbook <cookbook> --lesson <lesson-id>`.
8. Commit the coherent change if the project requires staged commits. Never
   include unrelated files.

Do not overwrite an existing lesson, infer missing facts, move the resource
before validation succeeds, or let the graph author the learning path.
