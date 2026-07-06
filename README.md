# agentic-starter

> Starter agentique prêt à l'emploi pour démarrer un projet avec Claude Code et le CLI Codex.

`agentic-starter` fournit une base commune pour travailler avec plusieurs agents de code :

- `.claude/` et `CLAUDE.md` pour Claude Code
- `.codex/` et `AGENTS.md` pour le CLI Codex
- `.memory/` à la racine pour une mémoire projet partagée entre les assistants
- des agents spécialisés, des skills, des règles de permissions et un flux d'initialisation

---

## Quickstart

**Étape 1 — Cloner dans ton projet**

```bash
git clone https://github.com/PetitPelican/agentic-starter.git .
```

**Étape 2 — Recharger l'éditeur**

Après le clone, recharge la fenêtre pour que les assistants détectent les nouveaux fichiers :

`Shift + Ctrl + P` -> **Developer: Reload Window**

**Étape 3 — Initialiser le projet**

Dans Claude Code ou Codex, lance :

```text
/agent-init
```

L'agent va scanner ton projet, te poser les questions nécessaires, puis configurer automatiquement :

- `CLAUDE.md` pour Claude Code
- `AGENTS.md` pour le CLI Codex
- les agents adaptés au type de projet
- la mémoire projet dans `.memory/`
- les skills `agent-init`, `memory-update`, `caveman` et `caveman-compress`

**Étape 4 — Coder**

Utilise Claude Code ou Codex selon ton workflow. La mémoire étant centralisée dans `.memory/`, les deux outils peuvent s'appuyer sur le même état projet.

En fin de session ou de sprint, lance :

```text
/memory-update
```

---

## Projet existant

Si ton projet a déjà du code, ne clone pas directement dans le répertoire racine. Copie uniquement les dossiers et fichiers utiles.

```bash
git clone https://github.com/PetitPelican/agentic-starter.git /tmp/agentic-starter

cp -r /tmp/agentic-starter/.claude ./
cp -r /tmp/agentic-starter/.codex ./
cp -r /tmp/agentic-starter/.memory ./
cp /tmp/agentic-starter/CLAUDE.md ./
cp /tmp/agentic-starter/AGENTS.md ./
cp /tmp/agentic-starter/.mcp.json.example ./

rm -rf /tmp/agentic-starter
```

Sur Windows (PowerShell) :

```powershell
git clone https://github.com/PetitPelican/agentic-starter.git $env:TEMP\agentic-starter

Copy-Item -Recurse "$env:TEMP\agentic-starter\.claude" ".\.claude"
Copy-Item -Recurse "$env:TEMP\agentic-starter\.codex" ".\.codex"
Copy-Item -Recurse "$env:TEMP\agentic-starter\.memory" ".\.memory"
Copy-Item "$env:TEMP\agentic-starter\CLAUDE.md" ".\CLAUDE.md"
Copy-Item "$env:TEMP\agentic-starter\AGENTS.md" ".\AGENTS.md"
Copy-Item "$env:TEMP\agentic-starter\.mcp.json.example" ".\.mcp.json.example"

Remove-Item -Recurse -Force "$env:TEMP\agentic-starter"
```

Puis recharge l'éditeur (`Shift + Ctrl + P` -> **Developer: Reload Window**) et lance `/agent-init`.

> `agent-init` détecte automatiquement que le projet est existant et ajoute uniquement ce qui manque.

---

## Ce qui est inclus

### Claude Code

- `CLAUDE.md` — contexte projet pour Claude Code
- `.claude/settings.json` — permissions et configuration partagées
- `.claude/settings.local.json.example` — exemple de configuration locale
- `.claude/agents/` — agents spécialisés
- `.claude/skills/` — skills disponibles dans Claude Code

### Codex CLI

- `AGENTS.md` — contexte projet pour Codex
- `.codex/settings.json` — permissions et configuration partagées
- `.codex/settings.local.json.example` — exemple de configuration locale
- `.codex/agents/` — agents spécialisés
- `.codex/skills/` — skills disponibles dans Codex

### Agents disponibles

| Catégorie | Agents |
|---|---|
| Dev | frontend, backend, mobile, db, auth, payments |
| Data | sql, python, ingestion, transformation, orchestration |
| API | routes, auth, docs |
| Ops | build, qa, audit |
| Audit | audits comportementaux, transversaux et qualité |

### Skills

- `agent-init` — initialise le projet et adapte les fichiers de contexte
- `agentic-upgrade` — migre un ancien projet Claude-only vers `agentic-starter`
- `memory-update` — met à jour la mémoire projet
- `caveman` — mode ultra-compressé pour réduire les tokens
- `caveman-compress` — compresse les fichiers mémoire

### Mémoire

La mémoire n'est plus stockée dans `.claude/`. Elle vit maintenant à la racine, dans `.memory/`, pour être partagée par Claude Code, Codex et les autres assistants.

- `.memory/MEMORY.md` — index de tous les fichiers mémoire
- `.memory/state.md` — features faites, en cours et bloquées
- `.memory/decisions.md` — décisions d'architecture
- `.memory/architecture.md` — couches, flux de données et environnements
- `.memory/data-model.md` — modélisation des données
- `.memory/business.md` — règles métier, pricing et rôles
- `.memory/clients.md` — onboarding, trial, billing et résiliation

---

## Configuration MCP

Copie `.mcp.json.example` vers `.mcp.json`, puis remplis les clés nécessaires.

```bash
cp .mcp.json.example .mcp.json
```

Sur Windows (PowerShell) :

```powershell
Copy-Item .mcp.json.example .mcp.json
```

---

## Permissions locales

Les permissions partagées sont dans :

- `.claude/settings.json`
- `.codex/settings.json`

Pour des ajustements locaux non commités, copie les exemples :

```bash
cp .claude/settings.local.json.example .claude/settings.local.json
cp .codex/settings.local.json.example .codex/settings.local.json
```

Sur Windows (PowerShell) :

```powershell
Copy-Item .claude/settings.local.json.example .claude/settings.local.json
Copy-Item .codex/settings.local.json.example .codex/settings.local.json
```

---

## Contribuer

Les templates d'agents sont dans :

- `.claude/agents/`
- `.codex/agents/`

Les skills sont dans :

- `.claude/skills/`
- `.codex/skills/`

Garde la mémoire projet dans `.memory/` afin qu'elle reste indépendante d'un assistant spécifique.
