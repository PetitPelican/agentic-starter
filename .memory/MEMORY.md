# Index mémoire — [PROJECT_NAME]
_Dernière mise à jour : YYYY-MM-DD_

> **Deux dossiers, deux natures.** `.mind/` n'énumère que des **faits actuels** :
> si on le lit, c'est que le projet fonctionne comme ça et qu'on en est là.
> `.memory/` garde les **traces datées** : décisions, journaux, matière du
> domaine.
>
> **Le test qui tranche** — une phrase qui commence par « on a décidé de », ou
> qui porte une date au passé, va dans `.memory/`. Tout le reste va dans
> `.mind/`.

**Cette mémoire ne sert pas d'abord à l'agent, elle sert à son commanditaire** —
pour voir où en est le projet sans ouvrir le dépôt. C'est ce qui décide du ton :
`state.md` s'écrit pour quelqu'un qui n'a pas lu le code.

## `.mind/` — les faits actuels · **exactement cinq fichiers**

Le texte périmé s'y **remplace**, il ne s'ajoute pas.

- [`.mind/state.md`](../.mind/state.md) — **Où on en est ?** En-tête
  `maj / cap / sante / jalon`, puis phase, ce qui tient, ce qui ne tient pas →
  *Suivi* · _(session)_
- [`.mind/todo.md`](../.mind/todo.md) — **Qui doit bouger ?** Kanban
  `[ ]`/`[>]`/`[x]`, `!haut`/`!moyen`/`!bas`, `@<qui>` → *Suivi* · _(session)_
- [`.mind/architecture.md`](../.mind/architecture.md) — **C'est quoi, et comment
  c'est bâti ?** Domaine, frontières, couches, flux, pièges →
  *Objectifs & périmètre* + *Architecture* · _(à la demande)_
- [`.mind/stack.md`](../.mind/stack.md) — **Avec quoi, et où ça tourne ?**
  Outils, stack, environnements → *Objectifs & périmètre* · _(à la demande)_
- [`.mind/rules.md`](../.mind/rules.md) — **Quelles règles ?** Métier, accès,
  contraintes → *Règles de gestion* · _(session)_

> **Jamais un sixième fichier dans `.mind/`.** Si un contenu n'y rentre pas,
> c'est qu'il appartient à `.memory/`. Deux fichiers de la machine sont **lus
> par le tableau de bord et gardés par `mind-guard`** : `state.md` (son en-tête)
> et `todo.md` (son dialecte). Les casser fait disparaître le projet du tableau
> de bord **sans message d'erreur**.

## `.memory/` — les traces datées

Ça s'accumule, sans plafond.

- [decisions.md](decisions.md) — **Pourquoi ces choix ?** Journal *append-only*
  → *Décisions / points ouverts* · **Public (curé)** · _(à la demande)_
- [operations.md](operations.md) — 🔒 **PRIVÉ.** Hébergement, déploiement,
  références de secrets, dépannage. **Jamais publié, jamais cité, jamais
  résumé** — c'est le pare-feu entre la mémoire interne et la doc publique.
- `data-model.md` — **conditionnel.** Livré par défaut ; `project-init` (ou
  `agentic-upgrade`) le **conserve** pour un projet data-lourd, sinon le
  **supprime** — le modèle vit alors dans une section d'`architecture.md`.

## Stratégie de lecture

**En début de session** : `.mind/state.md`, `.mind/todo.md`, `.mind/rules.md`
(+ cet index). C'est le contexte court à fort signal.
**À la demande** : `architecture.md` et `stack.md` avant de toucher au code ou à
la structure, `decisions.md` pour tracer un choix, `operations.md` pour déployer
ou déboguer.

## Fraîcheur — deux pièges, un par dossier

**Dans `.memory/`**, chaque fichier porte `_Dernière mise à jour_`. Une note de
trois semaines est affirmée avec exactement le même aplomb qu'une note d'hier :
**l'oubli n'y est pas visible de l'intérieur.** Au-delà de **4 semaines**,
vérifier dans le code avant de s'appuyer dessus pour une affirmation
structurelle — puis corriger le fichier si la réalité a bougé.

**Dans `.mind/`**, il n'y a pas de date, et c'est délibéré : ces fichiers n'ont
pas le droit d'être périmés. Un fait qui n'est plus vrai s'y **remplace**. La
seule date est le champ `maj:` de `state.md`, qui existe pour la machine.

<!-- Multi-domaine (plusieurs sous-projets dans un même dépôt) : chaque domaine
     porte son propre couple `.mind/` + `.memory/`, et un `CLAUDE.md` de racine
     porte le socle commun — il est hérité par tous les sous-dossiers, à
     n'importe quelle profondeur. Ne PAS créer de `.mind/` au niveau de la
     racine : aucun agent n'y tourne pour le tenir, et un état consolidé que
     personne ne maintient pourrit en silence. -->
