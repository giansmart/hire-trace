---
name: basic-interaction-rules
description: Collaboration rules for working in the hire-trace project. Load this before running any shell command, installing a dependency, or scaffolding project files, to check whether the user should run it instead.
---

# Basic interaction rules

This project is a hands-on collaboration, not a hand-off-and-wait workflow. Follow these
rules for how work gets split between the user and Claude.

## The user runs shell commands

Do not execute setup, dependency, environment, or scaffolding commands yourself (e.g.
`uv add`, `uv sync`, `uv init`, `git init`, `alembic upgrade`, package installs, running
the dev server). Instead, give the user the exact command in a code block and let them
run it. They are tracking commands run so far in `_internal_docs/commands.txt`.

This applies to anything that changes project or environment state via the shell.

## Writing file content is fine

Creating or editing file content directly — README files, source code, config files
(`pyproject.toml`, `.gitignore`), schemas, docs, other `SKILL.md` files — is expected and
should just be done with the Write/Edit tools, not handed off as a command. The
distinction is "shell command that changes state" vs. "file content the user asked for."

## Read-only inspection is always fine

Reading files, grepping, checking `git status`, or otherwise inspecting current state
never needs to be handed off — only state-changing shell commands do.

## Check the user's own changes before touching a file

The user writes code in this project too, not just Claude. Before editing or
overwriting any file, check its current state first (re-read it if it was last
touched outside this conversation, check `git status`/`git diff` for uncommitted
work) instead of assuming it still matches what Claude last wrote. Never blindly
overwrite work the user did themselves.

If something the user wrote looks inconsistent with the rest of the codebase, the
architecture in `README.md`, or introduces a bug or contradiction, say so and explain
why before proceeding — don't silently "fix" it and don't silently go along with it
either.

## When unsure

If it's not clear whether something counts as a command to hand off or content to
write, default to handing over the command and asking.
