# Engineering guidelines (moved from CLAUDE.md)

## 5. Evaluation-Driven Development

Never treat a single successful AI output as proof of reliability.

For LLM, RAG, and Agent workflows:

- Define representative evaluation datasets.
- Establish a baseline before optimization.
- Evaluate correctness and relevant failure modes.
- Measure latency, cost, and reliability when practical.
- Compare changes against the baseline.
- Record known limitations.

Do not invent evaluation results.

## 8. Parallel Agents

When supported, parallelize independent tasks with non-overlapping file ownership.

Do not allow multiple agents to modify the same component without coordination.

Integrate outputs and run relevant tests afterward.

Use sequential execution for tightly coupled tasks.

## 10. Continuous Improvement

After recurring errors:

- Identify the underlying cause.
- Determine the correct future behavior.
- Propose a short, positive, reusable instruction.
- Update project instructions only when the rule is broadly applicable and verified.

Keep this file concise, relevant, and current.

## 11. Handoff Notes

When a fresh session is appropriate, provide:

- Current project state.
- Completed work.
- Technical decisions.
- Modified files.
- Tests and results.
- Remaining tasks.
- Known issues.

## 12. Completion Report

For completed engineering tasks, report:

1. What changed.
2. Affected file paths.
3. Tests actually performed and their results.
4. Remaining limitations or risks.

Be concise. Never claim unverified success.