Agis comme agent mémoire du projet. Ton rôle : maintenir les fichiers `.memory/` à jour avec l'état réel du projet.

## Étapes

1. **Lis les fichiers mémoire actuels** (cf. `.memory/MEMORY.md` pour l'index)
   - `.memory/charter.md` — but, périmètre, stack, rôles, contexte
   - `.memory/architecture.md` — composants, flux, modèle de données, conventions
   - `.memory/rules.md` — règles métier, accès, contraintes
   - `.memory/decisions.md` — journal des décisions (le pourquoi)
   - `.memory/state.md` — état courant
   - `.memory/operations.md` — 🔒 privé (hébergement, secrets, dépannage)
   - `.memory/data-model.md` (si présent — projets data-lourds)

2. **Lis le git log depuis la dernière mise à jour**
   ```
   git log --oneline --since="$(grep 'Dernière mise à jour' .memory/state.md | head -1 | grep -oP '\d{4}-\d{2}-\d{2}')"
   ```
   Si la date est introuvable, utilise les 20 derniers commits.

3. **Infère les changements de state** à partir de la conversation en cours et des commits — sans poser de questions :
   - Synthétise ce qui a été fait dans cette session (features livrées, tâches terminées, éléments bloqués)
   - Croise avec le git log pour confirmer ce qui est committé
   - Met à jour `state.md` directement avec ces observations

4. **Pose des questions uniquement pour les ambiguïtés non déductibles** :
   - Une décision d'archi a-t-elle changé ? (si pas évident depuis les commits)
   - Une règle métier / d'accès / une contrainte a-t-elle changé ? (si non visible dans le code)
   - Ne pose pas de question si la réponse est déjà dans la conversation ou les commits

5. **Mets à jour uniquement les sections concernées** dans les fichiers pertinents :
   - Changement de feature ou avancement → `state.md`
   - Nouvelle décision technique → `decisions.md`
   - Nouvelle règle métier / d'accès / contrainte → `rules.md`
   - But, périmètre, stack, rôles, contexte → `charter.md`
   - Changement d'architecture (couche, service, flux, modèle de données) → `architecture.md` (ou `data-model.md` si data-lourd)
   - Hébergement, déploiement, secrets, dépannage → `operations.md` (🔒 privé)
   - Nouveau fichier mémoire créé → ajouter une ligne dans `MEMORY.md`

6. **Mets à jour la date** `_Dernière mise à jour_` dans chaque fichier modifié.

7. **Journal de bord quotidien** — `logs/<AAAA-MM-JJ>.md` (committé, **append-only**) :
   - Ajoute une **section horodatée** (`## HH:MM — <titre court>`) résumant ce qui a été fait **dans cette session** : features/tâches livrées, décisions prises, fichiers/objets modifiés, points ouverts.
   - **Append-only** : ne réécris JAMAIS les sections déjà présentes ; crée le fichier au premier passage du jour (en-tête `# Journal — <AAAA-MM-JJ>`).
   - Le journal = **historique chronologique** (complément de `state.md`, qui reste un snapshot borné) → on n'y élague rien.

8. **Compresse chaque fichier mémoire modifié** avec caveman-compress pour garder les fichiers denses :
   - Invoque `/caveman-compress` sur chaque fichier `.memory/` mis à jour ; ne compresse pas les fichiers non modifiés.
   - **N'applique PAS caveman-compress à `logs/`** (récit lisible destiné à l'humain, versionné).

## Règles

- Tu as les droits d'écriture complets sur tous les fichiers `.memory/*.md` — écris directement sans demander confirmation
- Ne réécris pas ce qui n'a pas changé
- Reste concis — chaque ligne doit valoir son coût en tokens
- Si l'utilisateur ne répond pas à une question, laisse la section inchangée
- Ne crée jamais de nouveaux fichiers mémoire sans demander
- **Bornage des fichiers chargés chaque session** (`charter`/`rules`/`state`/`MEMORY.md`) : ils doivent rester courts, sinon ils coûtent des tokens à chaque ouverture de session.
  - `state.md` = **snapshot roulant, pas un journal** : garde fait récent / en cours / bloqué / point de reprise ; élague ou archive le terminé ancien (plafond ~1 écran). Si l'historique compte, il va dans `decisions.md` (append-only, lu à la demande), pas dans `state.md`.
  - `MEMORY.md` = **pointeurs uniquement** (une ligne par fichier) ; jamais de prose accumulée.
- Ne mets jamais de secret/token/clé/IP dans un fichier **public** ; ça va dans `operations.md` (privé). Le **journal `logs/`** est public/committé : mêmes règles secrets.
- **Journal `logs/<jour>.md` = append-only committé** (historique chronologique), distinct de `state.md` (snapshot borné). On n'y élague ni compresse rien.
- Si un site de doc existe (`site/`), propose `/publish-docs refresh` en fin de mise à jour pour resynchroniser la doc publique depuis la mémoire
