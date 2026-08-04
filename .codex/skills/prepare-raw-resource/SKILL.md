---
name: prepare-raw-resource
description: Inspect and safely prepare a Knowledge Lesson Builder item from resource/raw for resource/pool. Use when the user asks to assess a raw source, keep it as one topic, split a large multi-topic source losslessly, generate a split plan, verify exact coverage, or finalize a confirmed preparation.
---

# Prepare Raw Resource

1. Locate the project root containing `build.sh` and `resource/index.yml`. Read
   `AGENTS.md` and `guidelines/resources.md`.
2. If no resource ID was supplied, run
   `./build.sh resource list --status raw --json` and ask the user to choose.
3. Run `./build.sh resource inspect <id> --json`. Stop on any hard failure.
4. Read headings and file structure first. For a large source, read text in
   batches of about 2,000 words with about 200 words of overlap. Track exact
   file and line boundaries; do not paraphrase, summarize, reorder, or omit.
5. Prefer `single` at 3,000 words or fewer when the source has one learning
   goal. Above 3,000 words, review whether topic boundaries justify a split.
   Above 8,000 words, propose a split unless the user explicitly approves a
   reasoned large-single override. Above 50,000 words without a usable heading
   or file outline, stop and ask the user for an outline.
6. Present a concrete proposal: mode, reason, and for each part its ID, title,
   exact line ranges, approximate word count, attachments, and rationale.
   Ask for **confirmation 1**. Do not write a plan before confirmation.
7. After confirmation 1, write a version-1 YAML plan below
   `build/resource-preparation/<id>/`, marking every attachment either on one
   or more parts or in `archive_only`. Run:

   ```bash
   ./build.sh resource prepare <id> --plan <plan-path>
   ```

   Use `--allow-large-single` only after the user explicitly approved it.
8. Report preparation ID, source hash, output hashes, attachment decisions,
   coverage percentage, gaps, and overlaps. Require 100% coverage, zero gaps,
   and zero overlaps. Ask for **confirmation 2**. Nothing may enter pool before
   this confirmation.
9. After confirmation 2, run:

   ```bash
   ./build.sh resource finalize <id> --preparation <preparation-id>
   ./build.sh resource verify <id> --json
   ```

10. Report success only when post-finalize verification passes. On failure,
    leave/recover the raw original and explain how to retry with the same
    preparation ID.

Never move files directly, choose `archive-only` for the user, finalize below
100% coverage, self-approve either confirmation, or rewrite source content.
