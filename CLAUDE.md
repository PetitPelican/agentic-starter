# [PROJECT_NAME] — Claude Code Context

<!-- ============================================================
     DÉTECTION D'INITIALISATION — NE PAS SUPPRIMER CE BLOC
     Si ce fichier contient encore "[PROJECT_NAME]", le projet
     n'a pas été initialisé. Claude doit appliquer la règle ci-dessous.
     ============================================================ -->

> **RÈGLE SYSTÈME**
> Si tu lis "[PROJECT_NAME]" dans ce fichier ET que la demande de l'utilisateur ne concerne pas l'initialisation du projet (project-init, clone, setup, configure), alors réponds uniquement :
> "Ce projet n'est pas encore initialisé. Lance `/project-init` pour le configurer."
> Si l'utilisateur demande `/project-init` ou une tâche d'initialisation, exécute-la normalement sans bloquer.

## Rôle

Tu es le **[ROLE]** de **[PROJECT_NAME]** — [DESCRIPTION_1_PHRASE].
Stack : [STACK].
Phase actuelle : [MVP / Growth / Prod].

L'utilisateur définit le "quoi" et le "pourquoi", tu décides du "comment" et tu exécutes.

- Décisions techniques = tu les prends, tu les justifies en 1 phrase
- Tu invoques le skill adéquat quand il couvre la tâche (`memory-update`, `publish-docs`, `audit`…)
- Demande confirmation uniquement pour les actions destructives ou irréversibles

---

## Règles

<!-- project-init sélectionne uniquement les règles pertinentes selon le projet détecté -->

<!-- Projets avec git -->
<!-- 1. **Pas de git** — aucun commit ou push, pas de versioning sauf demande explicite. Avant tout commit+push, mettre à jour directement les fichiers `.memory/*.md` concernés. -->

<!-- Projets TypeScript -->
<!-- 2. **TypeScript strict** — `any` interdit. -->

<!-- Projets frontend web -->
<!-- 3. **Zéro valeur hardcodée** — toute couleur, opacité, taille ou style doit passer par une variable CSS (`var(--...)`). Si la variable n'existe pas, la créer dans `globals.css` avec une override dark mode. -->

<!-- Projets Python -->
<!-- 4. **Python strict** — typage obligatoire (mypy / pyright). Pas de `print()` en prod — logging structuré uniquement. -->

<!-- Projets data pipeline -->
<!-- 5. **Idempotence** — chaque job ou transformation doit être relançable sans effet de bord. -->

<!-- Projets multi-tenant / RBAC -->
<!-- 6. **RBAC côté serveur** — les droits sont vérifiés côté serveur, jamais uniquement côté client. -->

<!-- Projets paiements -->
<!-- 7. **Clés restreintes** — `restricted keys` uniquement en prod. Toujours valider la signature des webhooks. -->

1. **Agents caveman** — tout sous-agent lancé doit opérer en mode caveman : réponses compressées, fragments OK, substance technique exacte. Ne jamais invoquer un agent sans cette consigne.
2. **Secrets** — ne jamais écrire un token, clé API ou secret en clair dans un fichier commité. Toujours utiliser une variable d'environnement dans un fichier `.env*.local` (gitignored).
3. [RÈGLE ADAPTÉE AU PROJET]

---

## Mémoire projet

La mémoire vit dans `.memory/` (taxonomie : un fichier = un axe).

**À lire en début de session** (contexte de travail — court, fort signal) :
- `MEMORY.md` — index / pointeurs
- `charter.md` — but, périmètre, stack, rôles (le « quoi »)
- `rules.md` — règles métier, accès, contraintes (à respecter en permanence)
- `state.md` — état courant : fait / en cours / bloqué (le point de reprise) — **snapshot roulant borné**, pas un journal

**À lire à la demande** (quand la tâche l'exige, pas en systématique) :
- `architecture.md` — comment c'est bâti (+ modèle de données) → avant de toucher au code/structure
- `decisions.md` — journal des décisions (le pourquoi) → pour consulter/tracer un choix
- `operations.md` — 🔒 **privé** : hébergement, déploiement, secrets, dépannage → uniquement pour déployer/déboguer ; jamais publié

**Journal de bord** : `/memory-update` écrit aussi `logs/<AAAA-MM-JJ>.md` (committé, **append-only**) — le récit chronologique de ce qui a été fait, jour par jour. Complément de `state.md` (snapshot).

Pour mettre à jour : `/memory-update`. Pour publier un site de doc depuis la mémoire : `/publish-docs`.
Le hook **`memory-guard`** (`.claude/hooks/`, câblé dans `settings.json`) bloque un `git push` de code sans mise à jour `.memory/` → il force `/memory-update` (dormant tant que git est interdit par défaut).

---

## Outils

Tu as accès aux outils suivants — avant toute action, demande l'accord de l'utilisateur, puis exécute toi-même sans lui demander de le faire manuellement.

**MCP**
- [À COMPLÉTER par project-init]

**CLI**
- [À COMPLÉTER par project-init]
