# agentic-starter

> Starter agentique prêt à l'emploi pour démarrer un projet avec Claude Code et le CLI Codex.

`agentic-starter` fournit une base commune pour travailler avec plusieurs agents de code :

- `.claude/` et `CLAUDE.md` pour Claude Code
- `.codex/` et `AGENTS.md` pour le CLI Codex
- `.memory/` à la racine pour une mémoire projet partagée entre les assistants
- des skills, des règles de permissions, un flux d'initialisation et un site de doc optionnel

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
/project-init
```

L'agent va te demander quel(s) assistant(s) tu utilises (Claude Code / Codex / les deux) et supprimer le harnais non retenu, scanner ton projet, te poser les questions nécessaires, puis configurer automatiquement :

- le(s) fichier(s) de contexte conservé(s) : `CLAUDE.md` (Claude Code) et/ou `AGENTS.md` (Codex)
- les règles adaptées au type de projet détecté
- la mémoire projet dans `.memory/`
- optionnellement, un site de documentation Quarto (`/publish-docs`)

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

Puis recharge l'éditeur (`Shift + Ctrl + P` -> **Developer: Reload Window**) et lance `/project-init`.

> `project-init` détecte automatiquement que le projet est existant et ajoute uniquement ce qui manque.

---

## Ce qui est inclus

### Claude Code

- `CLAUDE.md` — contexte projet pour Claude Code
- `.claude/settings.json` — permissions et configuration partagées
- `.claude/settings.local.json.example` — exemple de configuration locale
- `.claude/skills/` — skills disponibles dans Claude Code

### Codex CLI

- `AGENTS.md` — contexte projet pour Codex
- `.codex/settings.json` — permissions et configuration partagées
- `.codex/settings.local.json.example` — exemple de configuration locale
- `.codex/skills/` — skills disponibles dans Codex

### Skills

Tout passe par des **skills** (plus d'agents-personas) :

- `project-init` — initialise le projet et adapte les fichiers de contexte
- `project-upgrade` — migre un projet existant vers la dernière version du starter
- `memory-update` — met à jour la mémoire projet
- `publish-docs` — génère un site de documentation Quarto (HTML + Word/PDF) depuis la mémoire
- `audit` — audit exhaustif du code (comportemental / transversal / qualité), rapport seul
- `caveman` — mode ultra-compressé pour réduire les tokens
- `caveman-compress` — compresse les fichiers mémoire

### Mémoire

La mémoire n'est plus stockée dans `.claude/`. Elle vit maintenant à la racine, dans `.memory/`, pour être partagée par Claude Code, Codex et les autres assistants.

Taxonomie générique (un fichier = un axe), avec une frontière **public / privé** :

- `.memory/MEMORY.md` — index de tous les fichiers mémoire
- `.memory/charter.md` — but, périmètre, stack, rôles, contexte métier _(public)_
- `.memory/architecture.md` — composants, flux, modèle de données, conventions _(public)_
- `.memory/rules.md` — règles métier, accès, contraintes _(public)_
- `.memory/decisions.md` — journal des décisions (le pourquoi) _(public)_
- `.memory/state.md` — fait / en cours / bloqué / à faire _(public)_
- `.memory/operations.md` — 🔒 hébergement, déploiement, secrets, dépannage _(**privé — jamais publié**)_
- `.memory/data-model.md` — modélisation détaillée _(conditionnel : projets data-lourds)_

Les fichiers **publics** peuvent alimenter un site de doc via `/publish-docs` ; `operations.md` reste privé.

Les fichiers chargés à chaque session (`charter`, `rules`, `state`, `MEMORY.md`) sont volontairement courts ; `state.md` est un **snapshot roulant borné** (pas un journal). `architecture`, `decisions` et `operations` sont lus à la demande.

### Site de documentation (optionnel)

- `site/` — moteur Quarto piloté par `site/site.config.yml` (titre, preset `data`/`web`/`api`/`generic`, cible de déploiement `azure`/`ghpages`/`zip`/`none`).
- `/publish-docs [setup|init|refresh|publish]` — installe les outils (Quarto/Graphviz), génère les pages depuis la mémoire **publique** vers `_content/`, produit un site HTML + livrables Word/PDF, déploie. Ne lit jamais `operations.md` ni les `.env*`.

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

Tout passe par des **skills** (les deux harnais sont maintenus en miroir) :

- `.claude/skills/`
- `.codex/skills/`

Toute modification d'un skill doit être répercutée à l'identique dans les deux dossiers. Garde la mémoire projet dans `.memory/` afin qu'elle reste indépendante d'un assistant spécifique.
