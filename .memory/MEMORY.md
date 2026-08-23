# Index mémoire — [PROJECT_NAME]
_Dernière mise à jour : YYYY-MM-DD_

> Taxonomie générique : un fichier = un axe, sans redite. **Frontière public/privé** : les fichiers publics peuvent alimenter le site de doc (`/publish-docs`) ; `operations.md` est **privé** et n'est jamais publié.

**Stratégie de lecture** — en **début de session**, lire le contexte court/fort signal : `charter`, `rules`, `state` (+ cet index). Lire **à la demande** quand la tâche l'exige : `architecture` (avant de toucher au code/structure), `decisions` (tracer un choix), `operations` (déployer/déboguer). `state.md` = snapshot roulant borné, pas un journal.

**Fraîcheur** — chaque fichier porte `_Dernière mise à jour_`. Une note de trois
semaines est affirmée avec exactement le même aplomb qu'une note d'hier : c'est
le principal piège de cette mémoire, car **l'oubli n'y est pas visible de
l'intérieur**. Au-delà de **4 semaines**, vérifie dans le code avant de t'appuyer
dessus pour une affirmation structurelle (architecture, modèle de données,
procédure d'exploitation) — puis corrige le fichier si la réalité a bougé.
`state.md` est le plus volatil : périmé, il égare plus vite que les autres.

## Public — alimente le site de doc

- [charter.md](charter.md) — **C'est quoi ?** But, périmètre, stack, rôles, contexte métier → *Objectifs & périmètre* · _(session)_
- [architecture.md](architecture.md) — **Comment c'est bâti ?** Composants, flux, modèle de données, conventions → *Architecture* · _(à la demande)_
- [rules.md](rules.md) — **Quelles règles ?** Règles métier, accès, contraintes → *Règles de gestion* · _(session)_
- [decisions.md](decisions.md) — **Pourquoi ces choix ?** Journal des décisions (append-only) → *Décisions / points ouverts* · _(à la demande)_
- [state.md](state.md) — **Où on en est ?** Fait / en cours / bloqué / à faire → *Suivi* · _(session)_

## Privé — jamais publié

- [operations.md](operations.md) — 🔒 Hébergement, déploiement, réf. secrets, dépannage · _(à la demande — jamais publié)_

## Conditionnels

- `data-model.md` — modélisation des tables par couche. **Livré par défaut** : `project-init` (ou `agentic-upgrade`) le **conserve** pour les projets data-lourds, sinon le **supprime** (le modèle vit alors dans une section d'`architecture.md`).

<!-- Multi-domaine (plusieurs sous-projets dans un même dépôt) : voir la convention `.memory/<domaine>/{charter,architecture,rules,decisions,state}.md` + `.memory/_global/{charter,operations}.md`. -->
