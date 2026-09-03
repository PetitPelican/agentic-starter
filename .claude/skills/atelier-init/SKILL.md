---
name: atelier-init
description: >
  Monte un ATELIER agentique sur une machine neuve — la couche au-dessus des
  projets : le CLAUDE.md de méthode à la racine (hérité par tous les agents) et
  le poste du CTO, harnais complet. À lancer UNE fois par machine, avant tout
  projet. Pour monter un projet, c'est project-init, agentic-upgrade ou
  agentic-sync.
  Trigger: /atelier-init, « installer le CTO », « porter l'atelier sur cette machine ».
---

# Atelier Init

> **Quand l'utiliser** : une machine neuve sur laquelle on veut reposer la même
> architecture agentique. Une fois, avant les projets.
> Un **projet** à monter → `/project-init`, `/agentic-upgrade` ou
> `/agentic-sync`. Ce skill ne touche à aucun projet.

## Ce qu'il monte

```
<racine>/                      ~/Agentic, C:\Users\<toi>\Documents\AGENTIC…
├── CLAUDE.md                  ← LA MÉTHODE. Héritée par tout sous-dossier.
├── cto/                       ← le poste du CTO
│   ├── CLAUDE.md              son rôle seulement — la méthode, il l'hérite
│   ├── .claude/               hooks, skills, settings
│   ├── .mind/  .memory/       sa mémoire : l'atelier, pas les projets
│   └── .git/                  sans dépôt, les deux hooks sont inertes
└── <projet>/                  montés ensuite, un par un
```

## Trois couches, une seule voyage

| Couche | Fichier | Contenu | Portable ? |
|---|---|---|---|
| Poste | `~/.claude/CLAUDE.md` | comptes, sessions, réseau, RAM | non — refait par machine |
| **Méthode** | **`<racine>/CLAUDE.md`** | mémoire, hooks, skills, frontières | **oui — c'est l'artefact** |
| Projet | `<projet>/CLAUDE.md` | rôle, stack, règles métier | non — propre au projet |

**Le socle ne « prévaut » pas sur les `CLAUDE.md` de projet.** Les deux sont
lus, et le plus spécifique l'emporte en cas de conflit — vérifié par commande :
un agent dans `parent/enfant` lit les deux fichiers, un agent dans `parent` ne
lit jamais celui de l'enfant. Le socle porte donc l'**invariant**, le projet
ajoute ses spécificités. Chercher à écraser depuis le parent produit deux textes
qui se contredisent, et c'est le plus précis qui gagne de toute façon.

Corollaire : **ne jamais mettre le rôle du CTO dans le socle.** Il serait hérité
par tous les chefs de projet, qui se croiraient CTO — et la frontière « un
projet appartient à son agent » leur interdirait alors de modifier leur propre
projet.

## Procédure

**1. Amorcer.** Le skill vit dans le starter : il faut donc le starter d'abord.

```bash
git clone https://github.com/PetitPelican/claude-starter.git /tmp/claude-starter
```

```powershell
git clone https://github.com/PetitPelican/claude-starter.git $env:TEMP\claude-starter
```

**2. Dry-run**, depuis n'importe où :

```bash
python3 /tmp/claude-starter/.claude/skills/atelier-init/scripts/atelier-init.py \
        --racine ~/Agentic --cto cto --utilisateur "<TonPrénom>"
```

Sur Windows, l'interpréteur s'appelle `python`. Le rapport montre ce qui serait
créé, ce qui existe déjà (jamais écrasé), et ce qui restera à faire à la main.

**3. Appliquer** après lecture du rapport : ajouter `--apply`.

**4. Ouvrir le CTO** dans son dossier — c'est ce qui lui donne son `CLAUDE.md`
et le socle hérité :

```bash
cd ~/Agentic/cto && claude
```

**5. Vérifier.** Trois contrôles, dans cet ordre — voir ci-dessous.

## Ce qui reste à la main, et pourquoi

Le script pose des fichiers. Il ne décide rien. Trois choses lui échappent :

**Le câblage des hooks.** Le harnais copie `mind-guard.py` et `journal.py`, mais
le bloc `hooks` de `settings.json` appartient au projet. Vérifier qu'ils y sont
déclarés, chacun **deux fois** — une entrée `python`, une `python3` — pour
couvrir Windows et macOS sans opérateur de shell. **Un hook qui ne démarre pas
ne bloque rien et ne le dit pas.**

**La preuve.** Faire un commit d'essai de code sans toucher `.mind/`, voir
`mind-guard` refuser, puis vérifier que `.logs/<jour>.md` s'écrit. Un hook qu'on
n'a pas vu se déclencher n'est pas un hook vérifié.

**Le contenu du socle.** Le template porte la méthode générique. Ce qui est propre
à la **machine** — comptes, sessions, réseau, contraintes mémoire — n'y va pas :
il va dans `~/.claude/CLAUDE.md`. Mélanger les deux, c'est perdre la portabilité
du socle au premier changement de poste.

## Ensuite

L'atelier est monté, il est vide. Le CTO enchaîne, projet par projet :

| Le projet | Le skill |
|---|---|
| n'existe pas encore | cloner le starter dedans, puis `/project-init` |
| existe, sans harnais | `/agentic-upgrade`, puis le tri de mémoire |
| a le harnais, en retard | `/agentic-sync` |

Le **tri de mémoire** est le seul vrai travail de jugement : les scripts
signalent une taxonomie ancienne, ils ne la migrent jamais d'office. Trier
demande de lire le contenu, et le contenu appartient au projet.

## Règles

- **Rien n'est jamais écrasé.** Un `CLAUDE.md` déjà présent à la racine ou chez
  le CTO est conservé et signalé.
- **Ne pas mettre le rôle dans le socle**, ni la méthode dans le rôle.
- **Ne pas monter de projet avec ce skill** : il monte l'atelier, une seule fois.
- **`git init` n'est pas cosmétique** : les deux hooks se déclenchent au commit.
  Un dossier sans dépôt porte un harnais inerte, silencieusement.
- Rapporter ce qui a été fait, ce qui a été ignoré, et ce qui reste. Ne rien voir
  n'est pas un succès, c'est une absence de mesure.
