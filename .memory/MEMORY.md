# Index mémoire — [PROJECT_NAME]

> Taxonomie générique : un fichier = un axe, sans redite. **Frontière public/privé** : les fichiers publics peuvent alimenter le site de doc (`/publish-docs`) ; `operations.md` est **privé** et n'est jamais publié.

**Stratégie de lecture** — en **début de session**, lire le contexte court/fort signal : `charter`, `rules`, `state` (+ cet index). Lire **à la demande** quand la tâche l'exige : `architecture` (avant de toucher au code/structure), `decisions` (tracer un choix), `operations` (déployer/déboguer). `state.md` = snapshot roulant borné, pas un journal.

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
