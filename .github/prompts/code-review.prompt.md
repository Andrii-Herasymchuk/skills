---
description: "Engineering code review of pending changes: correctness, security (OWASP), tests, and maintainability."
agent: "agent"
argument-hint: "Optional: path, or leave empty to review staged/unstaged diff"
tools: [read, search, execute]
---
Review the code changes ${input:scope:(default: current git diff)}.

1. Determine the scope: if none given, inspect `git diff` and `git diff --staged`.
   Otherwise review the specified files.
2. Review for, in priority order:
   - **Correctness** — logic errors, edge cases, off-by-one, error handling, races.
   - **Security (OWASP)** — injection, secrets in code, unsafe deserialization, authz
     gaps, path traversal, untrusted input reaching dangerous sinks.
   - **Tests** — is the change covered? Identify missing cases.
   - **Maintainability** — naming, duplication, dead code, unnecessary complexity.
   - **Consistency** — matches existing patterns and the repo's conventions.
3. Report findings grouped by severity (Blocker / Major / Minor / Nit). For each, cite
   the file and line as a clickable link and give a concrete fix suggestion.
4. End with a short verdict: approve, approve-with-nits, or request-changes.

Do not modify code — this is a review only.
