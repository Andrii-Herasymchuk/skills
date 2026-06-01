---
description: "Generate a concise daily standup from my Suppa tasks (done / in progress / blocked / next)."
agent: "agent"
tools: [suppa/*]
---
Produce my daily standup using Suppa.

1. Resolve me with `#tool:suppa_get_me`.
2. Fetch my active work with `#tool:suppa_search_tasks` using `my=True, active=True`,
   and overdue items with `my=True, overdue=True`.
3. Group the results into:
   - **Done recently** — tasks in a completed stage updated in the last day or two.
   - **In progress** — active tasks assigned to me.
   - **Blocked / overdue** — overdue tasks or ones whose latest comment indicates a blocker.
   - **Next** — what I should pick up next.
4. For each item show: short ID, title, stage, and deadline if set.

Keep it tight — bullet points, no preamble. Do not create or modify any tasks.
