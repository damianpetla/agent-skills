---
name: project-harness
description: "Audit or improve a project's coding-agent harness: instructions, tools, environments, orchestration, and evidence-based verification adapted to the repository."
metadata:
  origin: Personal skill developed from project requirements and primary-source research.
  version: "0.1.0"
---

# Project Harness

Make the project's delivery loop executable: understand the task, prepare the
environment, implement, verify the relevant behavior, inspect evidence, and
leave a state that the next session can resume. Judge capabilities by what they
can prove, not by the number of instruction files or installed tools.

## Choose scope

Use the project and objective from the conversation; otherwise use the current
repository. Ask only for an unresolved choice that changes the analysis.

- **Audit** is the default for a bare invocation or a request to assess readiness.
  Inspect existing mechanisms, perform suitable bounded checks, and propose
  improvements. Keep project source and configuration intact; save findings
  using the workspace's artifact conventions.
- **Improve** applies when the user asks to build or fix the harness. Diagnose
  first, then implement the smallest useful changes within the authorized
  scope and verify them. Existing authorization remains valid; a separate
  approval ceremony is unnecessary for ordinary reversible work.

State the chosen scope briefly. A harness task is not permission to implement
unrelated product features, deploy, connect accounts, export production data,
or reset shared environments. Preserve unrelated work and external skills.

## Discover the actual project

Inspect the repository's purpose, architecture, manifests, build configuration,
CI, tests, scripts, documentation and current work. Find the existing sources
before proposing replacements. Libraries, CLIs, games, backend services and
apps need different proof of correctness.

Map the instructions used by the actual clients: entry files, imports, scoped
rules, skills, hooks and task/session state. Check installed capabilities when
loading behavior depends on version. Distinguish always-loaded context from
material fetched on demand. Identify conflicts, duplication and dead pointers.
AGENTS.md is one possible entry point, not the required shape of the harness.

Determine where the product can run, which dependencies it needs, and what
access is available. Read [environments.md](references/environments.md) when
runtime checks require services, devices, data, credentials, or production-only
dependencies. A blocked environment is an actionable finding, not a reason to
pretend validation succeeded or stop all independent analysis.

## Follow a representative delivery loop

Select a meaningful existing behavior or test path appropriate to the project.
Prefer a critical user journey or contract over a convenient superficial check.
Trace setup → start/readiness → verification → evidence → cleanup, including
how a new session discovers and resumes that path.

Run existing checks only after inspecting what they execute and where their
side effects go. Use the project's expected sandbox and data boundaries.
Keep probes bounded; report unavailable checks and continue useful work.
Do not silently substitute a production endpoint when a local service fails.

For each relevant capability, report workflow integration and execution
evidence separately:

- **Workflow integration:** record whether it is **Declared** (a document,
  command or tool claims to provide it) and **Connected** (agents can discover
  when and how to use its implementation).
- **Execution evidence:** record whether it is **Executed** (it ran against an
  identified code/artefact/environment state) and **Confirmed** (its observed
  result supports a specific acceptance claim).

State what is supported, absent or unknown for each item, with evidence. A
manually confirmed check may still be disconnected from the agent workflow;
report that gap explicitly. Mark genuinely irrelevant capabilities as such.

## Diagnose gaps and propose repairs

Read [verification.md](references/verification.md) when analysing checks,
runtime/UI proof, false positives, or completion claims. Examine both product
correctness and the trustworthiness of the verification mechanism.

For each material gap, give evidence, the concrete failure it could cause,
the smallest useful repair, prerequisites, maintenance/cost tradeoffs, and a
way to demonstrate the repair works. Separate observed defects from risks and
unknowns. Recognize existing controls that need wiring or documentation rather
than replacing them. Prioritize critical gaps; a short list can be sufficient.

Propose missing tools when they would close the loop: a small script, an adapter
to existing commands, a scenario runner, or a more substantial service if its
lifecycle genuinely requires one. Read [tools.md](references/tools.md) when
designing or implementing tools. Design one result for both human and agent
consumers, with readable summaries and structured evidence.

Adapt orchestration to real work: explicit task boundaries, dependency order,
ownership of shared resources, durable progress for long sessions, and bounded
retry/stop conditions. Use existing plans or trackers. A small task may need
none of the additional machinery; subagents are optional and depend on the
session's authorization and tools.

## Implement when requested

Reuse the project's stack and output conventions. Encode mechanical invariants
in checks and put non-obvious decisions in discoverable instructions. Keep one
source of truth; avoid parallel command stacks and copied rule sets. Choose the
right home for each addition instead of generating a fixed set of templates.

Connect changes to how agents start work, choose checks and recognize
completion. Keep local and CI behavior aligned, with explicit differences for
resources that one environment cannot provide. Preserve external skills unless
their modification was separately requested.

Exercise the improved path on the appropriate project state. Where feasible,
confirm a meaningful failing case in an isolated fixture as well as a passing
case. Match negative testing to risk; do not break the user's working tree or
weaken assertions for a green result. New files alone do not prove a working
harness.

## Deliver findings and evidence

Write in the user's language. Use a concise chat summary and save substantial
findings in the project's existing documentation/artifact location. Scale the
report to the work; include:

- what the project can currently prove, and how;
- prioritized gaps, proposed or implemented repairs, and their tradeoffs;
- actual checks, scoped results and evidence locations;
- blocked or unverified behavior and the next concrete action to close it;
- the smallest sensible next step, with existing strengths preserved.

Use PASS, FAIL, BLOCKED, NOT_RUN or NOT_APPLICABLE with reasons. Distinguish
agent-interpreted observations from scripted assertions. Report measured costs
when available; otherwise label estimates. Claim reduced waste or errors only
after comparison on representative tasks. Future sessions should be able to
find the instructions, execute the checks and understand the remaining limits.
