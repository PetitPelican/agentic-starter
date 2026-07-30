# Index mémoire — [PROJECT_NAME]

> Taxonomie générique : un fichier = un axe, sans redite. **Frontière public/privé** : les fichiers publics peuvent alimenter le site de doc (`/publish-docs`) ; `operations.md` est **privé** et n'est jamais publié.

## Public — alimente le site de doc

- [charter.md](charter.md) — **C'est quoi ?** But, périmètre, stack, rôles, contexte métier → *Objectifs & périmètre*
- [architecture.md](architecture.md) — **Comment c'est bâti ?** Composants, flux, modèle de données, conventions → *Architecture*
- [rules.md](rules.md) — **Quelles règles ?** Règles métier, accès, contraintes → *Règles de gestion*
- [decisions.md](decisions.md) — **Pourquoi ces choix ?** Journal des décisions (append-only) → *Décisions / points ouverts*
- [state.md](state.md) — **Où on en est ?** Fait / en cours / bloqué / à faire → *Suivi*

## Privé — jamais publié

- [operations.md](operations.md) — 🔒 Hébergement, déploiement, réf. secrets, dépannage

## Conditionnels (créer au besoin)

- `data-model.md` — modélisation des tables par couche (**projets data-lourds** ; sinon = section d'`architecture.md`)

<!-- Multi-domaine (plusieurs sous-projets dans un même dépôt) : voir la convention `.memory/<domaine>/{charter,architecture,rules,decisions,state}.md` + `.memory/_global/{charter,operations}.md`. -->
