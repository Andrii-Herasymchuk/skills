---
description: "Document a shipped feature or change into Suppa Docs (release notes / technical doc page)."
agent: "agent"
argument-hint: "Feature name, PR, or describe what shipped"
tools: [read, search, execute, suppa/*]
---
Document this feature in Suppa Docs: ${input:feature:feature name or what shipped}.

1. Gather the facts: read the relevant code and, if useful, recent commits
   (`git log --oneline -20`) to understand what changed.
2. Pick the destination: list docs with `#tool:suppa_list_docs` and ask me which doc to
   add to (or whether to create a new one with `#tool:suppa_create_doc`).
3. Create a page with `#tool:suppa_create_page`, then fill it with
   `#tool:suppa_create_blocks`. Structure the content as:
   - **Overview** — what the feature does and why.
   - **How it works** — key components/flow (link files where relevant).
   - **Usage** — how to use/configure it, with examples.
   - **Notes / limitations** — edge cases, follow-ups.
4. Use clear headings and concise paragraphs (HTML is supported in blocks).

Return the doc/page IDs and a link-style reference. Do not change any code.
