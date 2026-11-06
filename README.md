# Agent Skills

Reusable skills for coding agents. Each skill is self-contained and may include focused references or helper scripts.

## Available skills

| Skill | Purpose |
| --- | --- |
| [project-harness](skills/project-harness/SKILL.md) | Audit and improve project instructions, tools, environments, and verification. |
| [android-emulator-speech-test](skills/android-emulator-speech-test/SKILL.md) | Inject a validated synthetic WAV into an explicitly owned Android emulator as one boundary in an app-specific speech test. |

## Structure

```text
skills/
├── project-harness/
└── android-emulator-speech-test/
    ├── SKILL.md
    ├── references/app-adapter.md
    └── scripts/
```

Add each skill under `skills/<name>/` with a `SKILL.md`. Include supporting files only when the skill's workflow needs them.

## Installation and updates

### Install a GitHub snapshot

In Codex, ask the skill installer to install the skill from its GitHub directory:

```text
Use $skill-installer to install android-emulator-speech-test from https://github.com/damianpetla/agent-skills/tree/main/skills/android-emulator-speech-test
```

The installer downloads the skill and its supporting files. Invoke it with `$android-emulator-speech-test`. This is a snapshot: later GitHub changes are not applied automatically; reinstall or update the skill to receive them.

### Use a live local clone

Clone this repository to a stable location, then symlink the selected skill directory into the agent's skills directory. Repository edits and a Git pull are visible on the next fresh skill invocation; a running invocation does not reload changed instructions.

Run from the repository root. The destination must not already exist; preserve an existing installation before replacing it.

```sh
mkdir -p ~/.agents/skills
ln -s "$(pwd)/skills/android-emulator-speech-test" ~/.agents/skills/android-emulator-speech-test
```

Invoke it with `$android-emulator-speech-test`.

### App-specific adapters

The shared skill prepares a fixture and transports audio. Each consumer also needs an app-specific adapter for launch, recording readiness, capture evidence, recognizer results and user-visible acceptance. Read both the shared skill and the app's adapter for app scenarios. Keep app identifiers, private paths, fixtures and acceptance rules in the app repository.

## License

This project is licensed under the [MIT License](LICENSE).
