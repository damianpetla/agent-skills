# Tools for people and agents

Read this when a missing capability warrants designing or implementing a tool.
First identify the exact gap and the outcome that would close it. Reuse a sound
existing command or add a small adapter before proposing a separate framework.

## Choose scope and lifecycle

A script is often enough for collecting evidence, running an ordered check
stack, seeding data or installing a test build. A richer runner/service can be
justified by coordinated processes, device ownership, resumable scenarios,
multiple backends or persistent state. Explain the benefit, dependencies and
maintenance cost; complexity should solve an observed problem.

Use the repository's language, package manager and task conventions. Keep one
execution path shared by humans, agents and CI where practical. Explain real
environment differences rather than hide them behind success defaults.

Document the tool's purpose, accepted inputs, working directory, prerequisites,
side effects and proof boundary. Provide discoverable help and useful errors.
Make run identity, readiness, timeout, retry limits and cleanup explicit when
the lifecycle needs them. A rerun should have predictable effects on owned
resources and seed data. Do not claim idempotence without checking it.

## One result, two presentations

Produce readable progress and an actionable final summary for a person, plus
a stable machine-readable result for an agent when decisions depend on it.
Choose a simple native format such as JSON/JSONL or structured test output;
the skill does not require a universal schema.

Derive both views from the same execution facts. Keep structured output separate
from progress chatter, preserve non-success exit codes, and report meaningful
statuses: PASS, FAIL, BLOCKED, NOT_RUN, NOT_APPLICABLE. Define their exit-code
mapping in that tool. A blocked prerequisite, empty test collection or silently
skipped critical check must not masquerade as a passing check.

Include enough identity and scope to interpret evidence: check/scenario,
code/artifact, environment, timing, coverage and paths to full logs, traces,
screenshots or reports. Capture only relevant diagnostic data and redact
secrets. Let the agent consume a concise structured summary instead of repeatedly
loading complete logs. Make full evidence navigable for a human.

## Confirm the tool closes its gap

Exercise an ordinary success case and the important error or cancellation path.
Use temporary fixtures or isolated test data when probing failure. Confirm
status propagation, diagnostics, meaningful assertions and cleanup. A wrapper
that always returns zero is not reliable even when its happy path looks good.

Connect the tool to project instructions and the appropriate local/CI trigger.
State what remains unverified. Publishing a report or touching live data is a
separate capability, not an implicit consequence of generating local evidence.
