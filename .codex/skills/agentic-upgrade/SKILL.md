---
name: agentic-upgrade
description: >
  Migre un projet existant basé sur l'ancien claude-starter vers agentic-starter.
  Utiliser quand un projet contient .claude/, CLAUDE.md, .claude/memory/ ou des
  références claude-starter, et qu'il faut ajouter .codex/, AGENTS.md et .memory/
  sans écraser les personnalisations du projet.
---

# Agentic Upgrade

## Objectif

Mettre à jour un projet existant vers la structure agentic-starter :

- conserver `.claude/` et `CLAUDE.md`
- ajouter `.codex/` et `AGENTS.md`
- migrer la mémoire de `.claude/memory/` vers `.memory/`
- remplacer les références obsolètes à `claude-starter` et `.claude/memory`
- ne jamais écraser un fichier personnalisé sans le signaler

## Procédure

1. Lire l'état Git avant toute action :
   ```bash
   git status --short
   ```

2. Lancer le script en dry-run depuis la racine du projet à migrer :
   ```powershell
   .\.codex\skills\agentic-upgrade\scripts\agentic-upgrade.ps1
   ```

   Si le projet n'a pas encore `.codex/`, lancer le script depuis un clone local de `agentic-starter` :
   ```powershell
   <CHEMIN_AGENTIC_STARTER>\.codex\skills\agentic-upgrade\scripts\agentic-upgrade.ps1 -ProjectRoot <CHEMIN_PROJET>
   ```

3. Présenter le rapport dry-run à l'utilisateur, surtout les conflits et fichiers qui ne seront pas écrasés.

4. Appliquer uniquement après accord :
   ```powershell
   .\.codex\skills\agentic-upgrade\scripts\agentic-upgrade.ps1 -Apply
   ```

   Pour supprimer l'ancien dossier `.claude/memory/` après copie vers `.memory/`, ajouter :
   ```powershell
   -RemoveLegacyMemory
   ```

5. Relancer la recherche de contrôle :
   ```bash
   rg --hidden -n -i "claude-starter|\.claude/memory|Claude Code Context|Claude doit" --glob "!.git/**"
   ```

   Les seules mentions Claude restantes doivent être liées à `.claude/`, `CLAUDE.md`, Claude Code, ou à un script qui appelle réellement le CLI Claude.

## Règles

- Ne pas supprimer `.claude/` : agentic-starter supporte Claude Code et Codex.
- Ne pas écraser `CLAUDE.md`, `AGENTS.md`, `.memory/` ou des settings existants.
- Si `.memory/` existe déjà, ne pas fusionner automatiquement avec `.claude/memory/`; signaler le conflit.
- Préférer créer `AGENTS.md` depuis `CLAUDE.md` personnalisé quand il existe, puis adapter le wording pour Codex.
- Garder la migration mécanique et traçable : rapporter fichiers ajoutés, modifiés, ignorés et conflits.
