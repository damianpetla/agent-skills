# Agent Skills

My skills for coding agents.

## Available skills

| Skill | Purpose |
| --- | --- |
| [project-harness](skills/project-harness/SKILL.md) | Audit and improve project instructions, tools, environments, and verification. |

## Structure

```text
skills/
└── project-harness/
    ├── SKILL.md
    ├── agents/openai.yaml
    └── references/
```

Add each new skill in its own `skills/<name>/` directory with a `SKILL.md`
file. Include supporting files when the skill needs them.

## Installation and updates

### Install directly from GitHub in Codex

Paste this prompt into Codex:

```text
Use $skill-installer to install project-harness from https://github.com/damianpetla/agent-skills/tree/main/skills/project-harness
```

The installer downloads the skill and its supporting files; you do not need to
clone this repository. The skill will be available on your next turn. Invoke it
with `$project-harness`.

This installs a snapshot; later GitHub changes are not applied automatically.
For a Git-managed installation, use the symlink setup below.

### Install from a local clone

This repository is the source of truth for versioned skills. Symlink a skill
into the agent's skills directory so repository changes are available directly,
without synchronizing copies. Keep the repository at the linked location.

To install `project-harness` in Codex, run these commands from the repository
root. The destination path must not already exist; move an existing installation
to a backup location first.

```sh
mkdir -p ~/.agents/skills
ln -s "$(pwd)/skills/project-harness" ~/.agents/skills/project-harness
```

Invoke the skill in Codex with `$project-harness`.

## License

This project is licensed under the [MIT License](LICENSE).
