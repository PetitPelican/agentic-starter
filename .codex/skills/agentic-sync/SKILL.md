---
name: agentic-sync
description: >
  Resynchronise un projet DÉJÀ agentic sur la dernière version d'agentic-starter :
  met à jour les fichiers starter-owned (corps des skills, moteur du site), supprime
  ce que le starter a retiré (agents/), applique les renommages, puis réconcilie à la
  main les fichiers project-owned (CLAUDE.md/AGENTS.md, mémoire, site.config.yml).
  Ne touche jamais au contenu de .memory/, _content/ ni aux secrets.
  Trigger: /agentic-sync ou "mets mon projet à jour avec le starter".
---

# Agentic Sync

> **Quand l'utiliser** : projet **déjà** agentic (a `.claude/skills/`, `.memory/`…) qu'on veut
> remettre au niveau du starter courant. Différent d'`agentic-upgrade` (onboarding additif d'un
> projet **sans** archi agentic) et de `project-init` (nouveau projet).

## Principe : ownership

- **Starter-owned → mis à jour vers la dernière version** (le script s'en charge) : corps des
  skills (`.claude/skills/**`, `.codex/skills/**`), suppression de ce qui a été retiré
  (`.claude/agents/`, `.codex/agents/`), nettoyage des renommages (`agent-init`, `doc-site`…).
  L'écrasement des skills est **voulu** : c'est le but du sync (récupérer la dernière logique).
- **Project-owned → jamais écrasé** : `.memory/**` (contenu), `site/site.config.yml`,
  `site/_content/**`, `.env*`, `.mcp.json`, `settings.local.json`.
- **Zone grise → réconciliée à la main** (ci-dessous, étapes 3-5), jamais en écrasement aveugle :
  section « Mémoire » + règles de `CLAUDE.md`/`AGENTS.md`, dérive de taxonomie mémoire, et le
  **moteur de site** (`build_site.py`, `publish.py`, `.gitignore`, `_assets/reference.docx`) :
  le script le **signale** s'il diffère mais ne l'écrase jamais — l'écraser seul casserait le build
  tant que `site.config.yml` n'existe pas ; il se met à jour dans le bloc « site » (swap + config + vérif).

Toujours **dry-run → validation → apply**. Rien de destructif sur le contenu projet.

## Procédure

### 1. État git + sauvegarde mentale
```bash
git status --short
```
Travailler sur une branche dédiée si le projet est en prod (`git switch -c chore/agentic-sync`).

### 2. Sync mécanique (script)
Dry-run d'abord, depuis la racine du projet :
```powershell
.\.claude\skills\agentic-sync\scripts\agentic-sync.ps1
```
Si le projet n'a pas encore ce skill, lancer depuis un clone local du starter :
```powershell
<CHEMIN_AGENTIC_STARTER>\.claude\skills\agentic-sync\scripts\agentic-sync.ps1 -ProjectRoot <CHEMIN_PROJET>
```
Présenter le rapport (Changements / Ignorés / À réconcilier). Après accord :
```powershell
.\.claude\skills\agentic-sync\scripts\agentic-sync.ps1 -Apply
```
Le script mirror les skills (ajoute les nouveaux, met à jour les corps, supprime les fichiers
retirés en amont), écrase le moteur de site **s'il existe déjà**, et supprime les chemins
obsolètes/renommés. Il ne crée pas de `site/` là où il n'y en a pas (→ `/publish-docs init`).

### 3. Réconcilier `CLAUDE.md` / `AGENTS.md` (guidé, pas d'écrasement)
Comparer avec les gabarits du template **uniquement sur les sections structurelles**, sans toucher
au rôle ni aux règles métier personnalisés du projet :
- **Section « Mémoire projet »** : aligner sur la taxonomie courante (lecture systématique
  `charter`/`rules`/`state`/`MEMORY.md` vs à la demande `architecture`/`decisions`/`operations` ;
  `state.md` = snapshot borné).
- **Règles** : si la règle git ou une règle générique a évolué dans le template, proposer le diff.
Montrer chaque changement, appliquer après validation.

### 4. Migrer la taxonomie mémoire (si dérive)
Le script ne touche pas `.memory/`. Si le projet est sur l'ancienne taxonomie, migrer le **contenu**
(non destructif, confirmer avant toute suppression). Mapping :

| Ancien | → Nouveau |
|---|---|
| `business.md` (qui/pourquoi/rôles) | `charter.md` |
| `business.md` (règles/contraintes) | `rules.md` |
| `clients.md` / `overview.md` | fondu dans `charter.md`, puis supprimer |
| `hosting.md`, secrets, dépannage, `troubleshooting.md` | `operations.md` (🔒 privé) |
| `data-model.md` | garder si data-lourd, sinon fondre dans `architecture.md` |
| `todo.md` | fondu dans `state.md` (snapshot) ; le reste part en `decisions.md` |
| `state.md`, `decisions.md`, `architecture.md` | inchangés |

**Multi-domaine** (ex. `.memory/<domaine>/…`) : appliquer la taxonomie **par domaine**
(`<domaine>/{charter,architecture,rules,decisions,state}.md`) + un niveau transverse
`.memory/_global/{charter,operations}.md`. Les fichiers très spécifiques (ingestion, lineage,
config d'orchestration, mesures BI…) restent comme sections d'`architecture.md` du domaine ou,
si opérationnels/sensibles, dans `operations.md`. Rien n'est supprimé sans validation explicite.

Mettre à jour `MEMORY.md` (pointeurs), puis `/memory-update` pour compresser.

### 5. Site : hardcodé → config-driven (si applicable)
Si le projet a un `site/` **sans** `site.config.yml`, le moteur vient d'être écrasé par la version
config-driven (étape 2). Générer la config manquante :
- créer `site/site.config.yml` (`title`, `tagline`, `logo_letter`, `preset`, `deploy`) ;
- vérifier que `_content/` et les `_diagrams/` sont en place ;
- `python site/publish.py --no-deploy` doit reproduire le site sans perte (HTML + Word/PDF).
Sinon (`site/` absent) : `/publish-docs init` pour le créer, ou ne rien faire.

### 6. Contrôles
```bash
# plus aucune référence aux éléments retirés / anciens noms
rg --hidden -n -i "\.claude/agents|\.codex/agents|agent-init|doc-site|project-upgrade" --glob "!.git/**"
# secrets : la mémoire publique et _content ne fuitent rien
rg -n -iE "(BEGIN PRIVATE|AccountKey|SAS=|[0-9]{1,3}(\.[0-9]{1,3}){3})" .memory site/_content 2>/dev/null
```

## Règles
- Ne jamais écraser `.memory/**`, `site/_content/**`, `site/site.config.yml`, `.env*` ni les settings locaux.
- Ne jamais supprimer de contenu mémoire sans confirmation explicite (migration = copie puis retrait validé).
- Répercuter tout changement de skill à l'identique dans `.claude/` **et** `.codex/`.
- Rapporter fichiers synchronisés / supprimés / à réconcilier ; garder la trace en dry-run avant apply.
- Projet en prod : brancher (`git switch -c`), un commit par bloc (mécanique, mémoire, site).
