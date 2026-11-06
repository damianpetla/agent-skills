# App adapter contract

The package transports a WAV to one explicitly selected Android emulator. An app adapter owns the application-specific test scenario and any claims about captured input, recognition, UI state, or user-visible results.

## Local preparation

Run from the package root. Preparation is explicit and installs pinned Python dependencies only into the private cache venv; it reads the emulator protocol from an already-installed SDK and generates stubs into that cache. It does not download an Android SDK or create an emulator.

```sh
bash scripts/prepare.sh /absolute/path/to/installed-sdk /absolute/private/task-cache
/absolute/private/task-cache/python/bin/python scripts/audio_fixture.py synthesize \
  --phrase "A short public synthetic phrase" \
  --voice "AN_INSTALLED_MACOS_SAY_VOICE" \
  --output /absolute/private/task-cache/fixture.wav
/absolute/private/task-cache/python/bin/python scripts/audio_fixture.py validate \
  --wav /absolute/private/task-cache/fixture.wav
```

Choose the phrase and installed macOS voice explicitly. Keep the fixture and cache out of version control. Host-only boundary tests can be run without preparing a venv or starting an emulator:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

## Shared transport surface

- `scripts/prepare.sh SDK_DIR CACHE_DIR` prepares a cache-local Python environment and generated emulator gRPC stubs from the selected installed SDK. Use an explicit absolute, task-owned cache path; the script makes it private and rejects symlinks. It installs the pinned Python dependencies only in that venv. It does not install an Android SDK, launch an emulator, build or install an app, request permission, install a speech model, or drive app UI.
- `scripts/audio_fixture.py synthesize --phrase TEXT --voice VOICE --output WAV` creates a WAV using the selected host voice. `validate --wav WAV` accepts only mono PCM16LE at 16 kHz, 0.1–10 seconds, with nonzero samples. These checks validate the fixture format and signal, not its meaning or recognition.
- `scripts/emulator_audio.py` exposes `OwnedEmulatorAudio` as a context manager. Construct it with the task's explicit SDK, `emulator-N` target, AVD name/data directory, private discovery file, generated stubs directory, and a private marker directory that persists across contexts for the same boot.
- After the app adapter confirms actual current recording, call `audio.start_injection(wav_path, capture_ready=True, max_seconds=20)`. The bound must cover the WAV plus one second of silence and may not exceed 40 seconds. It returns an `InjectionHandle`; `handle.metadata` describes the source WAV, and `handle.wait_fixture_offered(timeout_seconds)` (a positive wait of at most 42 seconds) reports whether the paced fixture and one second of trailing silence were offered by the RPC generator. The generator continues sending silence until context cleanup or the hard bound.
- The context manager's cleanup covers the transport and owned emulator. Its cleanup dictionary reports `rpc`, `host_mic_off`, `emulator_stopped`, and `cleanup_ok`; it has no ASR verdict.

The `capture_ready=True` argument is the caller's assertion, not something the transport discovers; an app readiness button or provider callback alone may not establish current recording. A true `wait_fixture_offered` result proves only that the sender offered the packets. It does not prove guest receipt, app `AudioRecord` capture, provider delivery, recognized words, or an accepted UI draft.

## Adapter-owned scenario

The adapter must use the app's real foreground flow and its current capture-ready signal before injection. While injection is active, observe the app through its own UI/instrumentation boundary. Require `wait_fixture_offered` to return true before applying the app's Finish action. Before leaving the transport context, stop the app's capture as the scenario requires and collect its app-specific input and recognition evidence. Then inspect transport cleanup separately.

An app that exposes trustworthy capture evidence may assert that the synthetic signal reached its capture path. ASR evidence must come from that app's actual recognizer and observed result. If the app uses a different recognition stack or does not expose capture evidence, define the strongest supportable app-specific assertion and label the missing boundary; do not infer it from the gRPC response.

Report separate outcomes for fixture validity, transport offered/completed/cancelled state, app capture evidence, recognizer result, user-visible final state, and cleanup. A scenario may require only some of these boundaries, but any claim must be supported by its corresponding app evidence. Missing or unbound evidence is unknown/blocked; a valid input followed by an incorrect recognition result is a failure. Typed text, mocked callbacks, and a successful injection RPC are not proof of actual ASR. Do not reuse an app's private phrase, thresholds, package identifiers, debug observer, or acceptance rules as generic defaults.

## Ownership, cleanup, and scope

Use a task-owned AVD, absolute AVD data path and private discovery metadata for its token-authenticated loopback gRPC endpoint. Never print or copy the token, choose an implicit/default device, operate a physical device, or stop an unrelated ADB server. The durable marker directory enforces one injection per boot across separate contexts; preserve it for that boot and never remove its consumed marker to retry. Context exit cancels the RPC, verifies the host microphone remains off, and stops only the validated owned emulator; preserve the AVD data directory.

The transport does not launch/install an app, grant permissions, decide which recognizer or locale the app uses, query language/model readiness, perform downloads, press UI controls, inspect transcripts, retry speech, or classify ASR. Those behaviors belong to an app adapter and the requested scenario. The common package currently provides audio fixture preparation and bounded emulator transport, not a universal test runner or cross-platform runtime guarantee.

## References

- [Android Emulator gRPC commands](https://developer.android.com/studio/run/emulator-console#programmatic-commands-unique-to-grpc)
- [AOSP emulator audio injection example](https://android.googlesource.com/platform/external/qemu/+/08aefd1f57c653d17e9ef972df9d82c978f7695c/android/android-grpc/python/samples/audio/inject_audio.py) — a transport reference only; this package should use its own implementation and preserve applicable license/provenance notices.
