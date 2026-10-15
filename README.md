# Agent Skills

Moje skille dla agentów programistycznych.

## Dostępne skille

| Skill | Zastosowanie |
| --- | --- |
| [project-harness](skills/project-harness/SKILL.md) | Audyt i usprawnianie instrukcji, narzędzi, środowisk i weryfikacji w projekcie. |

## Struktura

```text
skills/
└── project-harness/
    ├── SKILL.md
    ├── agents/openai.yaml
    └── references/
```

Każdy kolejny skill trafia do osobnego katalogu `skills/<nazwa>/` z plikiem
`SKILL.md`. Dodatkowe pliki dodawaj wtedy, gdy dany skill ich potrzebuje.

## Używanie i aktualizacje

Repozytorium jest źródłem wersjonowanych skilli. Instalacje w katalogach
agentów są osobnymi kopiami; zmiany w repozytorium przenoś do nich świadomie.

Przy pierwszej instalacji `project-harness` w Codexie, gdy katalog docelowy
jeszcze nie istnieje, uruchom z głównego katalogu repozytorium:

```sh
mkdir -p ~/.agents/skills
cp -R skills/project-harness ~/.agents/skills/project-harness
```

Wywołanie w Codexie: `$project-harness`.
