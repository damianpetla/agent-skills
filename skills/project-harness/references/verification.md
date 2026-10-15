# Verification and evidence

Read this when evaluating quality gates, runtime/UI checks or whether a
completion claim is justified. Choose checks for the changed behavior and
project risks; avoid requiring every class of test in every repository.

## Check selection and credibility

Find the existing commands, their callers and CI counterparts. Trace what they
actually run, not just their names. Consider the relevant layers: compilation,
format/lint/static analysis, unit/property/contract/integration tests, executable
examples, UI/regression/accessibility, API or data compatibility, and performance
when behavior has a measured budget. Separate quick iteration from final checks.

Look for false confidence: zero collected tests, unexpected skips, wrappers
swallowing errors, stale builds, wrong variants/endpoints, obsolete snapshots,
stubbed critical behavior, and assertions that only inspect implementation
structure. A command that ran is not necessarily a check that proved anything.

Verification should preserve failure/cancellation status and report missing
coverage. Inspect the failure path or try a controlled known-bad fixture where
useful. Keep grading criteria independent of the implementation being assessed;
changes to tests or acceptance criteria need a technical justification, not
merely the desire to pass. Do not invent numerical coverage targets.

## Application and UI loop

For apps, assess a complete meaningful path:

1. Choose the device/browser, app variant, backend and known test state.
2. Build and install/serve an identified artifact from the intended code state.
3. Start and observe readiness rather than assume a delay is sufficient.
4. Execute the scenario and check explicit acceptance outcomes.
5. Capture scoped results, relevant logs and visual/UI evidence.
6. Verify consequential state where needed: persistence, backend writes,
   navigation, restart, failure handling or other acceptance behavior.
7. Clean up only resources and data owned by this run.

For Android, inspect the existing Gradle variants and device/test setup before
choosing tools. Reuse Android CLI, ADB, Compose/Views tests, Espresso, UI Automator
or another established runner when appropriate. Collect logs for the relevant
process and scenario interval, including crash evidence. Confirm the installed
package/artifact; launching an old app proves nothing about the current change.
An existing Android skill can supply current tool syntax when available, but
this skill does not require any one tool or testing framework.

For web apps, inspect the running build, browser state and selected backend.
For libraries or CLIs, prefer public contracts, consuming examples and command
behavior; UI automation may be irrelevant. For games and hardware-dependent
projects identify visual, input, audio or device effects that current tools
cannot observe.

Scripted selectors/assertions aim for repeatable regression checks. Natural-
language journeys, vision and exploratory clicking are agent-interpreted
observations. Both can help, but report which was used and its limits. Neither
screenshots alone nor clean logs prove the full behavior. Account for state,
synchronization and flakiness even when a runner is scripted.

## Evidence validity

Tie each result to the command/check, code or artifact identity (including
relevant uncommitted changes), environment/configuration, data/scenario, time,
outcome, coverage and evidence locations. Identify skips and failed prerequisites.
Store full traces outside the immediate conversation and provide concise
summaries with pointers to details.

Reuse evidence while its scope and state remain applicable. Rerun when relevant
code, dependencies, configuration or environment changed, or when evidence is
incomplete/flaky. Repeating an expensive suite without a new reason wastes
resources; reusing stale evidence hides defects.

## Verify the harness itself

For new or repaired controls, demonstrate a relevant passing path and, where
feasible, a known failing path in a disposable fixture. Verify that a fresh
session can discover and run the path and interpret the result. Keep product
test failures, infrastructure blocks and verifier defects distinct.

To evaluate broader harness changes, compare representative tasks with the
previous process: correctness, missed checks, false alarms, user corrections,
time and measured token/tool cost when available. A document-length score or
an LLM's positive assessment is not a substitute for observed task results.
