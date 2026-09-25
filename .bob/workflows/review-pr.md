Workflow name: review-pr

Steps:
1. (deterministic) Given a repo + PR number, get the diff and the linked
   issue text.
2. (Counterexample mode, skill: extract-claims) Produce the claim list
   from step 1's output.
3. (parallel subagents, one per claim, skill: falsify-claim) For each
   claim in the list, spawn a subagent that runs falsify-claim on just
   that claim. Wait for all subagents to finish.
4. (deterministic) Collect all subagent verdicts (FALSIFIED / HELD) into
   one results list.
5. (deterministic, engine code — not Bob) Run diff-scoped mutation testing
   against the PR's own test suite, separately from steps 2-4.
6. (deterministic, engine code) Render the Review Receipt: claim verdicts
   + mutation score + focus map of risky lines, as one HTML page.

Bob's job: steps 1-4 (repo understanding, claim extraction, parallel
falsification via subagents — this is the part that needs Bob 2.0's
agentic/parallel/document-understanding features).
Claude Code's job: steps 5-6 (deterministic engine code — mutation
testing and rendering — doesn't need an LLM agent at all).
