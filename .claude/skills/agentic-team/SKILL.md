---
name: agentic-team
description: >
  Lit les .mind/ de tous les projets d'un atelier et en rend deux vues : un
  DIAGNOSTIC en terminal (l'état du harnais projet par projet, et quel skill
  lancer) et une PAGE HTML autonome, qui s'ouvre d'un double-clic sur n'importe
  quelle machine, sans serveur. Cette page s'appelle **agentic-team**.
  Strictement en lecture.
  Trigger: /agentic-team, « ouvre la page agentic-team », « agentic team »,
  « /equipe » (ancien nom), « la vue
  d'équipe », « le tableau de l'atelier », « où en sont les projets »,
  « diagnostique ce projet », « qu'est-ce qui m'attend ».
---

# Équipe

> **Deux questions, une seule lecture.** « Dans quel état est ce projet, et que
> faut-il y lancer ? » et « où en est toute l'équipe ? » se répondent avec les
> mêmes fichiers : le `.mind/` de chaque dossier. Un seul analyseur, deux
> sorties — deux analyseurs finiraient par diverger, et personne ne le verrait.

**Strictement en lecture.** Ce skill n'écrit que la page HTML qu'on lui demande.
Il ne touche à aucun projet : il dit ce qu'il faut lancer, il ne le lance pas.

## Les trois usages

```bash
# 1. Diagnostic de tout l'atelier, en terminal
python3 .claude/skills/agentic-team/scripts/agentic-team.py --racine ~/Agentic

# 2. Un seul projet, en détail — « va voir ce projet-là »
python3 .claude/skills/agentic-team/scripts/agentic-team.py --racine ~/Agentic --projet <NomDuProjet>

# 3. La page autonome
python3 .claude/skills/agentic-team/scripts/agentic-team.py --racine ~/Agentic --html ~/agentic-team.html
```

Sur Windows, l'interpréteur s'appelle `python`.

## La page

**Autonome au sens strict** : aucun serveur, aucun CDN, aucune police distante,
aucun fichier joint. Tout est dans le fichier. Elle s'ouvre d'un double-clic,
hors ligne, sur macOS comme sur Windows — et se copie sur une clé si besoin.

Elle ouvre sur **ce qui attend une décision**, avant les cartes de projet : c'est
la seule colonne qui ne se délègue pas. Puis une carte par projet avec le `cap:`,
la fraîcheur, l'état du harnais et l'avancement des tâches. Thème clair et sombre
selon le réglage de la machine.

Régénérer, c'est relancer la commande : la page est un **relevé daté**, pas un
tableau de bord vivant. Elle porte sa date en tête.

## Ce que le diagnostic regarde

Pour chaque projet, dans cet ordre — le premier problème rencontré donne le
verdict, parce que les suivants n'ont pas de sens tant qu'il n'est pas réglé :

| Verdict | Ce qui a été constaté | Ce qu'il faut lancer |
|---|---|---|
| `NEUF` | ni `.mind/` ni `docs/` | cloner le starter, puis `/project-init` |
| `TRI` | taxonomie d'avant le 02/09/2026 | `/agentic-upgrade`, puis le tri à la main |
| `MANQ` | `.mind/` incomplet | `/agentic-upgrade` |
| `HOOK` | mémoire en place, aucun hook | `/agentic-sync` |
| `CABL` | hooks copiés, absents de `settings.json` | les câbler à la main |
| `GIT` | hooks câblés, pas de dépôt git | `git init` — sinon ils sont inertes |
| `6e` | un sixième fichier dans `.mind/` | le déplacer vers `docs/` |
| `AVGL` | le `CLAUDE.md` ne nomme jamais `.mind/` | y ajouter la table « quelle question → quel fichier » |
| `BRIEF` | aucun hook `briefing` câblé | `/agentic-sync` |
| `DENY` | aucune règle `deny` dans `settings.json` | déclarer ce qui doit être refusé |
| `OK` | conforme | rien |

Les trois derniers portent sur **le contexte de l'agent**, pas sur ses fichiers.
`AVGL` suit les `@imports` : un `CLAUDE.md` d'une ligne qui importe un fichier
nommant `.mind/` compte comme orienté. Et c'est sa limite — mesuré le
03/09/2026, un projet **orienté** a quand même vu son agent se tromper sur ses
propres accès. Un pointeur ne se déclenche que si on doute déjà : c'est `BRIEF`
qui discrimine vraiment, pas `AVGL`.

Il lit aussi l'en-tête de `state.md` (`maj`, `cap`, `sante`, `jalon`) et rend
trois états de fraîcheur, jamais deux : **à jour**, **tiède** (plus de 7 jours),
**périmé** (plus de 4 semaines) — et **illisible**, qui est le cas grave : un
en-tête cassé fait disparaître le projet des tableaux de bord sans un mot.

## Formater un projet existant — la marche à suivre

Le diagnostic dit **quoi** lancer. Le faire demande deux précautions.

**1. Travailler depuis le dossier du projet.** Les scripts acceptent
`--project-root`, mais le *jugement* — trier la mémoire, réconcilier
`CLAUDE.md`, câbler les hooks — demande d'être dans le projet : c'est là que
Claude Code charge son `CLAUDE.md` et son `settings.json`. Une session ouverte
ailleurs ne les voit pas.

**2. Le tri de mémoire n'est jamais automatique.** Les scripts signalent une
taxonomie ancienne, ils ne la migrent pas : trier demande de lire le contenu, et
le contenu appartient au projet. Voir l'étape mémoire d'`/agentic-upgrade`.

Puis vérifier, dans cet ordre : le dépôt est un dépôt git · les hooks sont
câblés deux fois (`python` et `python3`) · **ils se déclenchent vraiment**, ce
qui se prouve par un commit d'essai. Relancer `/agentic-team --projet <nom>` doit
alors rendre `OK`.

## Le contrat de lecture

L'analyseur suit **le même contrat que le tableau de bord de la machine**, et
c'est une contrainte, pas un détail : deux analyseurs qui divergent, c'est deux
vérités et aucun signal.

- en-tête `---` … `---` en tête de `state.md`, champs `maj cap sante jalon`
- tâches `- [ ]` `- [>]` `- [~]` `- [x]`, **dans tout le fichier**, toutes
  sections confondues
- marqueurs `!haut` `!moyen` `!bas` et `@<qui>`, dont `@dehors` réservé

> Ne pas se borner à une section « Chantiers ». Les fichiers réels s'organisent
> librement — « Attend une décision », « Outillage », « Technique ». Une version
> antérieure de cet analyseur ne lisait que ce qui suivait un titre
> « Chantiers » : elle rendait **zéro tâche sur dix projets pleins**, sans rien
> signaler. Le titre reste reconnu pour les anciens `pilotage.md` qui bornaient
> réellement leur section.

## Règles

- **Lecture seule.** Ne jamais modifier un projet depuis ce skill.
- **Ne rien voir n'est pas un succès.** Zéro tâche `@<qui>` sur tout un atelier
  se vérifie avant d'être annoncé — c'est plus souvent un analyseur cassé qu'un
  atelier serein.
- Ne pas recopier l'état d'un projet ailleurs : la page est un relevé daté, la
  vérité reste dans le `.mind/` de chaque projet.
