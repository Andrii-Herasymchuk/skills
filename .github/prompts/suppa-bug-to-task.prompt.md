---
description: "Turn a bug, failing test, or code TODO into a well-formed Suppa task with reproduction steps."
agent: "agent"
argument-hint: "Paste the error, or point at the buggy code / TODO"
tools: [read, search, suppa/*]
---
Create a Suppa task for this issue: ${input:issue:error text, failing test, or code location}.

1. Investigate the code/error to understand the problem. Read the relevant files.
2. Draft a clear task:
   - **Title**: concise, action-oriented (e.g. "Fix null deref in invoice export").
   - **Description (HTML)**: Summary, Steps to reproduce, Expected vs Actual, and
     affected files/lines.
3. Before creating, ask me to confirm the assignee and project/workflow if unknown
   (use `#tool:suppa_search_users`, `#tool:suppa_list_workflows` to resolve IDs).
4. Create it with `#tool:suppa_create_task`. Set a `deadline` only if I specify one.
5. Return the new task's short ID and a one-line summary.

Do not modify code in this prompt — only file the task.
