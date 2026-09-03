# Atelier agentique — la méthode

Ce fichier est lu par **tout agent ouvert dans un sous-dossier**. Il porte la
**méthode**, et rien d'autre : ce qui est vrai de tous les projets, sur
n'importe quelle machine.

Il ne prévaut pas sur le `CLAUDE.md` d'un projet — les deux sont lus, et le plus
spécifique l'emporte. Le socle dit **comment on travaille** ; le projet dit **sur
quoi**. Ne jamais dupliquer l'un dans l'autre.

Trois couches, à ne pas mélanger :

| Couche | Fichier | Contenu |
|---|---|---|
| Poste | `~/.claude/CLAUDE.md` | comptes, sessions, réseau, RAM — refait par machine |
| **Méthode** | **ce fichier** | mémoire, hooks, skills, frontières — **se transporte tel quel** |
| Projet | `<projet>/CLAUDE.md` | rôle, stack, règles métier — propre au projet |

---

## La mémoire — trois dossiers, trois natures

C'est le cœur. Ce qui les sépare n'est pas le sujet, c'est la **nature du
texte**.

**`.mind/`** — les **faits actuels**, en **exactement cinq fichiers**. Le texte
périmé s'y **remplace**, il ne s'ajoute pas.

| Fichier | Répond à |
|---|---|
| `state.md` | où on en est |
| `todo.md` | ce qui reste, et ce qui attend une décision |
| `stack.md` | avec quoi c'est fait |
| `architecture.md` | comment c'est agencé, et ses frontières |
| `rules.md` | ce qu'on ne franchit pas |

**`.memory/`** — les **traces datées**, qui s'accumulent sans plafond :
`MEMORY.md` (l'index), `decisions.md` (le pourquoi, daté), `operations.md`
(🔒 hébergement, secrets, dépannage), `data-model.md` (si data-lourd).

**`.logs/`** — un fichier `<AAAA-MM-JJ>.md` par jour, **append-only**, écrit par
la machine à chaque commit. Jamais élagué, jamais compressé.

**Le test qui tranche** : une phrase qui commence par « on a décidé de », ou qui
porte une **date au passé**, va dans `.memory/`. Tout le reste va dans `.mind/`.

**Jamais un sixième fichier dans `.mind/` sans une décision explicite de
l'humain.** S'il n'y rentre pas, il est à `.memory/`. Et `.mind/` reste **à la
racine du dépôt**, jamais à un niveau intermédiaire — l'outillage n'en cherche
qu'un.

### Ce qui ne se compresse jamais

**`.mind/todo.md` et les `.logs/` ne passent jamais par un mode de
compression** — `/caveman` compris. Ces fichiers sont relus par un **programme**,
et les règles de compression fusionnent les listes : `!haut` et `@<qui>`
disparaîtraient. On perdrait exactement l'information pour laquelle ces fichiers
existent, et **sans erreur** : le tableau de bord afficherait simplement des
tâches sans priorité et sans destinataire.

La compression utile porte sur le **contexte d'entrée** d'un agent, jamais sur un
fichier que quelque chose d'autre relit.

### La mémoire auto de l'agent — le quatrième étage

En plus des trois dossiers du dépôt, chaque agent tient une mémoire **locale**,
rangée par Claude Code **selon le chemin de travail de la session**, hors du
dépôt. Elle porte ce qui ne concerne aucun projet en particulier : les constats
transversaux sur la machine, l'outillage, la méthode.

Deux conséquences :

- **Elle n'est pas partagée et ne se commite pas.** Ce qui doit survivre à
  l'agent va dans `.mind/` ou `.memory/`, pas là.
- **Elle est indexée par le chemin.** Renommer le dossier d'un projet
  l'orpheline en entier, avec les transcripts, **sans afficher la moindre
  erreur**. Un nom de dossier est une adresse : le vérifier avant tout
  renommage.

**Règle des quatre semaines** : une affirmation de mémoire — auto ou `.mind/` —
qui n'a pas été revérifiée depuis un mois est **non confirmée**. On la mesure
avant de s'en servir comme prémisse.

Un instantané ne raconte pas l'histoire, un historique ne dit pas où on en est :
c'est pourquoi il y a `state.md` **et** `.logs/`, et pas l'un des deux.

> Cette mémoire n'est pas écrite pour l'agent. Elle est écrite pour que
> **quelqu'un puisse suivre un projet sans ouvrir le dépôt** — et pour qu'un
> agent qui reprend le projet à froid retrouve l'état sans rien demander.

### Le format est un contrat

`state.md` et `todo.md` sont **relus par un programme**. Leur forme n'est pas
libre.

```
--- .mind/state.md : en-tête obligatoire ---
maj:   AAAA-MM-JJ      # la date du jour, en ISO
cap:   ce que le projet doit produire — une phrase : son but, pas son domaine
sante: vert            # vert | orange | rouge
jalon: le prochain caillou, celui qui débloque les autres
```

```
--- .mind/todo.md ---
## Chantiers            # seul ce qui suit ce titre est lu

- [ ] !haut @humain  ce qui attend une décision
- [>] !moyen         en cours
- [x]                fait
```

États `[ ]` `[>]` `[~]` `[x]` · priorités `!haut` `!moyen` `!bas` ·
destinataires `@<qui>` — n'importe quel nom ; `@dehors` est le seul réservé,
et désigne une attente extérieure que personne dans l'équipe ne peut lever.

**Un `state.md` cassé est pire qu'un périmé.** Périmé, il s'affiche « tiède ».
Cassé, le projet est classé « aucune déclaration » et **disparaît sans un mot**.

---

## Les trois hooks

Ils rendent la règle **appliquée** au lieu d'énoncée. Tous sont **fail-open** :
une erreur, un fichier absent, un dépôt sans `.mind/` laissent passer.

- **`briefing`** (`SessionStart` + `UserPromptSubmit`) — injecte à l'ouverture
  ce qui ne tient pas dans un pointeur : le `cap:`, la fraîcheur, le nombre de
  décisions en attente, les **titres de section** de `stack.md`, `rules.md` et
  `architecture.md`, et les `deny` réellement appliqués. Il ne recopie rien —
  il relit à chaque fois, donc rien ne peut s'y périmer.

  **Pourquoi un pointeur ne suffit pas.** Mesuré le 03/09/2026 : un agent a
  répondu de travers sur ses propres accès alors que son contexte de démarrage
  portait, en gras, « les identifiants sont dans `.mind/stack.md` — le lire
  avant de conclure qu'un outil manque ». Un pointeur ne se déclenche que si on
  doute déjà ; la panne est de croire qu'on sait. Le briefing ne demande rien,
  il montre.

  Sur `UserPromptSubmit` il est **silencieux** tant que rien n'a bougé dans
  `.mind/` — coût nul en régime établi. C'est aussi ce qui permet de le poser
  sur une **session déjà ouverte** : un `settings.json` de projet ajouté à
  chaud est relu sans redémarrage (vérifié), et le message suivant est briefé.

Les deux autres se déclenchent sur `git commit`, et restent dormants tant que
git est refusé par défaut dans `settings.json`.

- **`mind-guard`** (`PreToolUse`) — refuse un commit de **code projet** qui
  laisserait `state.md` ou `todo.md` en arrière, ou qui les rendrait
  **illisibles**. Il lit le contenu **indexé**, pas celui du disque.
  Échappatoire : ` # mind-ok` en fin de commande.
- **`journal`** (`PostToolUse`) — écrit dans `.logs/<jour>.md`. Il regarde
  `HEAD`, pas le retour de la commande : un commit échoué n'écrit rien, un
  double appel ne crée pas deux entrées.

`mind-guard-relais.py` sert aux dépôts **multi-domaines** : chaque sous-périmètre
le pose à la place du hook, et il remonte à la racine par `git rev-parse`.

**Les hooks sont copiés, mais leur câblage vit dans `settings.json`, qui
appartient au projet.** Après toute mise à jour, vérifier qu'ils y sont
déclarés — chacun **deux fois**, une entrée `python` et une `python3`, pour
couvrir Windows et macOS. Un hook qui ne démarre pas ne bloque rien **et ne le
dit pas**.

---

## Les skills, et lequel quand

| Situation du dépôt | Le skill | Ce qu'il fait au contenu |
|---|---|---|
| on ne sait pas dans quel état il est | `/equipe` | **rien — il lit et il dit quoi lancer** |
| vide ou tout neuf | `/project-init` | crée et remplit |
| du code, aucun harnais | `/agentic-upgrade` | ajoute seulement, n'écrase rien |
| harnais présent, en retard | `/agentic-sync` | écrase le harnais, jamais le projet |

**`/equipe` passe en premier parce qu'il est le seul à ne rien écrire.** Il lit
les `.mind/` de tout l'atelier et rend deux choses : un **diagnostic** projet par
projet, qui nomme le skill à lancer, et une **page HTML autonome — l'`agentic-team`**,
qui s'ouvre d'un double-clic sur n'importe quelle machine, sans serveur ni
réseau. Elle ouvre sur **ce qui attend une décision**, avant l'état des projets.

```bash
python3 .claude/skills/equipe/scripts/equipe.py --racine <racine>            # diagnostic
python3 .claude/skills/equipe/scripts/equipe.py --racine <racine> --projet X # un seul
python3 .claude/skills/equipe/scripts/equipe.py --racine <racine> --html agentic-team.html
```

La page est un **relevé daté**, pas un tableau vivant : elle porte l'heure de sa
génération et ne bouge plus. `--suivi 60` la réécrit en boucle et y pose un
meta-refresh — le seul rafraîchissement qui fonctionne depuis un `file://`.

`/publish-docs` génère un site Quarto (HTML + Word/PDF) depuis la mémoire
**publique** — il ne lit jamais `operations.md` ni les `.env*`. `/caveman` est un
mode compressé, à la demande — **jamais sur `.mind/todo.md` ni sur les `.logs/`**
(voir « Ce qui ne se compresse jamais »), et jamais imposé à un sous-agent qui
**rapporte des constats** : un rapport relu par un autre agent doit être sans
ambiguïté avant d'être court.

Les deux scripts de migration tournent en **dry-run par défaut** et n'écrivent
qu'avec `--apply`. Ni l'un ni l'autre ne **trie** une mémoire ancienne : trier
demande de lire le contenu, et le contenu appartient au projet. Ils remontent le
choix à faire, pas la décision prise.

---

## Déléguer

**Tout agent lancé par un agent tourne en `sonnet` par défaut.**

| Comment | La forme |
|---|---|
| Outil `Agent` | `model: "sonnet"` |
| Ouvrier en ligne de commande | `claude -p --model claude-sonnet-5` |

Un modèle plus gros demande une **consigne explicite de l'humain**, au cas par
cas. Ce n'est pas au parent d'en décider pour son enfant.

**Pourquoi.** Un sous-agent démarre à froid : il redérive un contexte que le
parent possède déjà, et il le paie en entier. Le coût d'un sous-agent est donc
dans le **lancement**, pas dans le prix du jeton — et une grappe de sous-agents
sur le plus gros modèle vide un quota en un après-midi. Pour du travail
**cadré** — une recherche, un balayage, un portage mécanique — le modèle
intermédiaire suffit ; c'est le cadrage qui fait la qualité du retour, pas la
taille du modèle.

Corollaire : **ne pas lancer de sous-agent quand la tâche ne l'exige pas.** Une
tâche « en plusieurs points » ou « à traiter à fond » n'est pas une demande de
délégation. On délègue ce qui a besoin de **fan-out** — beaucoup de fichiers à
balayer, dont on ne veut que la conclusion — ou ce que l'humain demande
nommément.

Les identifiants de modèles vieillissent ; la règle, elle, ne change pas :
**par défaut le modèle intermédiaire, l'escalade sur consigne.**

---

## Les frontières

1. **Un projet appartient à son agent.** Ne pas écrire dans le `.mind/` ni le
   `.memory/` d'un autre projet. La raison n'est pas hiérarchique, elle est
   mécanique : deux agents qui écrivent dans le même `.mind/` produisent des
   conflits silencieux.
2. **Ne jamais décider à la place de l'humain.** Un agent ne peut pas en
   débloquer un autre : c'est le seul point de contrôle humain de la chaîne, et
   un agent qui approuverait au nom d'un autre le supprimerait.
3. **`operations.md` est privé** — jamais ouvert, jamais cité, jamais résumé,
   jamais publié. Cela vaut pour son propre projet autant que pour les autres.
4. **Aucun secret en clair dans un fichier commité.** Rapporter l'existence, la
   taille ou la date d'un secret — jamais sa valeur.

---

## Les réflexes

- **Un fait documenté se vérifie par commande avant de servir de prémisse.** Un
  document a toujours un temps de retard sur le disque.
- **Ne rien voir n'est pas un succès, c'est une absence de mesure** — et ça se
  dit. Tout compte rendu distingue trois états : **vérifié bon**, **vérifié
  mauvais**, **pas mesuré**.
- **Ne jamais recopier l'avancement d'un projet ailleurs** : il vit dans son
  `.mind/state.md`, et une copie se périmerait en silence. Retenir **où
  regarder**, pas **quoi**.
- **Tenir `.mind/` à jour fait partie du travail**, pas de la paperasse d'après.
  Avant de rendre la main, `state.md` et `todo.md` disent l'état réel.
- **Portabilité** : Python est une dépendance dure, et son interpréteur ne porte
  pas le même nom selon l'OS. Aucun script propre à un seul système — un outil
  qu'une des machines ne peut pas lancer ne signale jamais qu'il est mort.
