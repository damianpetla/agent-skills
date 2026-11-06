---
name: android-emulator-speech-test
description: Create or run macOS-local Android emulator speech tests using validated WAV injection into an explicitly owned emulator. Use for real app scenarios; transport alone does not verify capture or ASR, so pair it with an app-specific adapter.
---

# Android emulator speech testing

Use the package's bounded audio transport as one part of a local app test. Choose a host test when emulator audio is outside the behavior under test.

1. Read the requested scenario and define its app-specific assertions. Before injection, the adapter must confirm the app's real current recording is active. Add capture-path evidence when the case claims audio delivery, and an actual recognizer result when it claims ASR; keep those assertions in the app's test adapter.
2. Prepare the package's Python environment and emulator SDK stubs in an explicit task cache. Create a short, public synthetic WAV with an explicit phrase and host voice, then validate its PCM format and nonzero samples.
3. Reserve an owned emulator, its data directory and authenticated loopback gRPC endpoint. Launch the app through its own test adapter and wait for its actual capture-ready state. Only then call the transport with `capture_ready=True`.
4. While the transport runs, use the app adapter to observe the requested app behavior, such as capture, transcript, final/error and Finish state. Wait for `InjectionHandle.wait_fixture_offered(...)` to return true before applying the app's Finish action. Collect the app evidence required by the scenario and stop app capture before leaving the transport context.
5. Check the transport cleanup result independently from the app assertions. Report each evidence boundary separately; the transport alone cannot produce a real-ASR or full-scenario pass.

See [app adapter contract](references/app-adapter.md) for the shared transport API, adapter responsibilities, and limits. This draft package has no generic end-to-end test runner; different apps keep their lifecycle and acceptance assertions in their own adapters.

The real-emulator workflow is a local macOS prototype, not a configured CI job; host tests are separate.
