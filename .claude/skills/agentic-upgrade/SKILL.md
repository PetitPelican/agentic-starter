---
name: agentic-upgrade
description: >
  Onboarde un projet existant qui n'a PAS encore d'archi agentic (ou est sur l'ancien
  claude-starter) : ajoute .codex/, AGENTS.md, .memory/ et les skills, en additif, sans
  écraser les personnalisations. Pour un projet DÉJÀ agentic qu'on veut resynchroniser
  sur la dernière version du starter, utiliser `agentic-sync` à la place.
---

# Agentic Upgrade

> **Quand l'utiliser** : projet existant **sans** archi agentic (aucun `.codex/`/`.memory/`,
> ou ancien `claude-starter` avec `.claude/memory/`). Purement **additif** : *copy-if-missing*,
> jamais d'écrasement.
> Projet **déjà** agentic à remettre au niveau du starter courant (skills, moteur, fichiers
> retirés/renommés) → c'est `agentic-sync`, pas ce skill.

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
   .\.claude\skills\agentic-upgrade\scripts\agentic-upgrade.ps1
   ```

   Si le projet n'a pas encore ce skill, lancer le script depuis un clone local de `agentic-starter` :
   ```powershell
   <CHEMIN_AGENTIC_STARTER>\.claude\skills\agentic-upgrade\scripts\agentic-upgrade.ps1 -ProjectRoot <CHEMIN_PROJET>
   ```

3. Présenter le rapport dry-run à l'utilisateur, surtout les conflits et fichiers qui ne seront pas écrasés.

4. Appliquer uniquement après accord :
   ```powershell
   .\.claude\skills\agentic-upgrade\scripts\agentic-upgrade.ps1 -Apply
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

## Migration de la taxonomie mémoire

Les anciens projets ont `state/decisions/business/clients/architecture/data-model`. La taxonomie actuelle est **charter / architecture / rules / decisions / state / operations** (+ `data-model` conditionnel). Après la copie mécanique, migrer le **contenu** (non destructif, à confirmer avant toute suppression) :

| Ancien | → Nouveau |
|---|---|
| `business.md` (qui / pourquoi / rôles / pricing) | `charter.md` |
| `business.md` (règles métier / contraintes) | `rules.md` |
| `clients.md` | section « Clients & facturation » de `charter.md`, puis supprimer |
| `state.md`, `decisions.md` | inchangés |
| `architecture.md` | inchangé (+ absorbe `data-model.md` si projet non data-lourd) |
| `data-model.md` | garder si data-lourd, sinon fondre dans `architecture.md` |
| hébergement / secrets / dépannage (souvent épars) | `operations.md` (🔒 privé) |

Créer `charter.md`, `rules.md`, `operations.md` s'ils manquent (gabarits du starter). Vérifier ensuite que `MEMORY.md`, `CLAUDE.md` et `AGENTS.md` pointent la nouvelle liste.

## Site de documentation (optionnel)

Si le projet n'a pas de dossier `site/`, proposer `/publish-docs init` puis `/publish-docs refresh` pour générer une doc Quarto (HTML + Word/PDF) depuis la mémoire **publique**.

## Règles

- Ne pas supprimer `.claude/` : agentic-starter supporte Claude Code et Codex.
- Ne pas écraser `CLAUDE.md`, `AGENTS.md`, `.memory/` ou des settings existants.
- Si `.memory/` existe déjà, ne pas fusionner automatiquement avec `.claude/memory/`; signaler le conflit.
- Préférer créer `AGENTS.md` depuis `CLAUDE.md` personnalisé quand il existe, puis adapter le wording pour Codex.
- Garder la migration mécanique et traçable : rapporter fichiers ajoutés, modifiés, ignorés et conflits.
