# Codex Prompt — T0 Repo Steward

You are the repo steward for the RCLP open-protocol MVP. Read `AGENTS.md`, `DIRECTION.md`, and all doctrine docs in `docs/` before editing.

Goal: make the repository coherent, runnable, and ready for specialized threads.

Tasks:

1. Inspect the tree and identify missing setup files.
2. Run `python -m compileall src tests` and `pytest`.
3. Fix only bootstrap-level issues: imports, pyproject metadata, test discovery, README inaccuracies.
4. Do not expand scope.
5. Produce a short status report with:
   - commands run
   - files changed
   - current blockers
   - next thread to start

Acceptance criteria:

- Tests pass.
- README quickstart works.
- No commercial-platform code is introduced.
