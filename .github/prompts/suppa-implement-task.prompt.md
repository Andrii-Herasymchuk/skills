---
description: "Implement a Suppa task end-to-end: fetch context, plan, code, verify, then update the task."
agent: "Suppa Dev Engineer"
argument-hint: "Task ID or short description"
tools: [read, edit, search, execute, todo, suppa/*]
---
Implement the work described by ${input:task:the task ID or description}.

Steps:
1. If a task ID is given, fetch full context with `#tool:suppa_get_task` and recent
   discussion with `#tool:suppa_get_comments`. Otherwise search with
   `#tool:suppa_search_tasks`.
2. Restate the goal and acceptance criteria in one or two sentences.
3. Plan the implementation as a `todo` list for anything non-trivial.
4. Implement the change following existing code patterns. Keep edits minimal and focused.
5. Verify: run the relevant build/tests/linter and fix any failures.
6. Update Suppa: add a progress comment with `#tool:suppa_add_comment` summarizing what
   changed, and move/close the task with `#tool:suppa_move_task` or
   `#tool:suppa_close_task` if it is done.

End with a short summary of the code changes and the Suppa updates (with IDs).
