# Environments and proof boundaries

Read this when the project's runtime depends on services, data, devices,
credentials, or a deployment environment. Discover the existing topology and
available access before choosing a sandbox design.

## Identify what can run where

Map the product to its dependencies and observable effects: local process,
emulator/device, local service, remote test tenant, staging, production, or
hardware-only behavior. Identify configuration/variant selection, runtime and
SDK versions, network access, authentication and required test state. Record
which facts are observed and which are only documented.

Inspect readiness, isolation and cleanup. Can two sessions safely run at once?
Who owns the ports, emulator, processes and data namespace? Who resets them?
Operate only on resources assigned to this run; existing shared processes are
not disposable simply because they resemble a dependency.

## Propose the minimum useful substitute

When the full application cannot run outside production, split the proof:
what can be exercised locally, what needs a controlled integration, and what
remains production-only. Continue with reachable checks and propose a route
for the rest. Do not label a partial substitute full end-to-end coverage.

Choose among existing test configuration, service emulators, deterministic
fakes, recorded/synthetic fixtures, containers, a disposable test tenant, or
an approved staging/production probe. Prefer the project's established tools.
A container is not automatically required and may not emulate real hardware,
identity, payments, push delivery, timing or external-service semantics.

For a proposed sandbox specify:

- which behavior it enables and which differences remain;
- minimum services/versions and a clear start/readiness/stop lifecycle;
- config separation that avoids accidental production fallback;
- synthetic or appropriately sanitized seed data, deterministic reset and
  per-run namespace where needed;
- local credentials/secret references without values in reports or fixtures;
- expected resource cost, isolation constraints and maintenance burden;
- a first smoke scenario that proves the sandbox is actually usable.

Use existing synthetic data first. Access to production does not itself
authorize exporting data, running migrations, sending real notifications or
creating transactions. Propose an authorized data path when sanitization or
production access is required. Pure mocks prove the modeled contract; real
integration still needs separate evidence.

## Evaluate startup and recovery

Probe readiness by observable conditions, with a timeout and useful diagnostic
output. Specify whether dependency failure blocks a check or fails product
behavior. Keep seeds and reset operations repeatable and scoped. Check recovery
after cancellation or failure: exit status, child processes, partial artifacts,
and resources created by this run.

An unavailable credential, device or remote environment yields a concrete
BLOCKED result and an enabling proposal. It is not evidence that the product
is defective or that a local approximation passed the production behavior.
