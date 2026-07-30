---
name: audit
description: >
  Audit exhaustif du code en lecture seule (rapport, aucune modification) : 3 volets —
  comportemental (ce que l'app fait), transversal (dette structurelle), qualité (comment
  c'est écrit). Adapte les patterns à la stack détectée. Produit un rapport par dimension
  + une synthèse (tableau de bord, top-10, plan en 3 sprints). Trigger: /audit
---

# Audit — revue exhaustive du code

**Règle absolue : ne modifie AUCUN fichier. Rapport uniquement.**

Audit en lecture seule, adapté à la **stack détectée** (framework web/mobile, ORM/client DB,
provider de paiements). 3 volets, ~40 points de contrôle. Complète les `/code-review` et
`/security-review` intégrés par une passe **structurée et exhaustive**.

## Exécution

1. **Cartographie (une fois)** : lister tous les fichiers source (hors `node_modules`, `dist`,
   `.next`, `.expo`, `.turbo`, `generated`, lock files). Lire chaque fichier **intégralement**.
2. **Lancer les dimensions.** Idéalement **en parallèle via des sous-agents** (Task tool, un
   sous-agent par dimension A1…C3, **mode caveman**) ou via `/workflows` ; sinon séquentiellement.
   Chaque dimension produit un rapport `AUDIT_<VOLET>_<CODE>.md`.
3. **Synthèse** (voir plus bas) une fois toutes les dimensions terminées.

### Discipline (dans chaque dimension)
- Notes intermédiaires après chaque fichier ; rapport final seulement une fois tout lu.
- Si la limite de contexte approche : **s'arrêter**, indiquer le dernier fichier traité et le reste — ne pas compresser/sauter.
- Section propre → écrire explicitement « Aucune occurrence détectée ».
- **Numéro de ligne exact** par occurrence. Fichiers auto-générés → « ignoré — auto-généré ».
- Incertain → inclure avec la mention `(à confirmer)`.
- Sévérités : **Critique** (sécurité/données/prod) · **Élevé** (bugs users) · **Moyen** (dette) · **Informatif**.

---

## Volet A — Comportemental (ce que l'app fait)

**A1 · Données & DB + Auth & accès** → `AUDIT_COMPORTEMENTAL_A1.md`
- UI déconnectée de la DB (handler `onSubmit`/`onPress` sans appel persistant ; succès affiché sans confirmation).
- Schéma DB incohérent avec le code (colonnes migrations ↔ types générés ↔ champs utilisés ; `NOT NULL` sans validation).
- Échec silencieux sur appels DB (`error` non vérifié ; redirection malgré `error`).
- Données mockées en prod (`mockData`/`fakeData`/`TODO: replace`).
- Écritures multi-tables sans transaction/rollback.
- Policies d'accès (RLS) absentes / permissives (`USING (true)`) / non isolées par user/tenant.
- Vérification de rôle **UI-only** sans équivalent serveur/policy.
- Middleware d'auth incomplet (whitelist vs blacklist ; routes protégées couvertes ?).
- Session expirée sans gestion (refresh token, listener 401, stockage sécurisé mobile).

**A2 · Architecture + UX silencieuse** → `AUDIT_COMPORTEMENTAL_A2.md`
- Logique métier dupliquée entre apps au lieu de `packages/` ; types non partagés.
- Pas de gestion offline (mobile) ; imports circulaires entre packages ; appels DB directs dans l'UI.
- États de chargement absents ; actions destructives sans confirmation ; validation formulaire absente ; empty states non gérés.

**A3 · Ops & prod** → `AUDIT_COMPORTEMENTAL_A3.md`
- Variables d'env manquantes/non validées au boot ; publiques = non secrètes.
- Migrations non rejouables (idempotence, `DROP` sans garde, procédure de rejeu).
- Webhook paiements sans vérification de signature (raw body, secret en env).
- Absence de rate limiting sur routes publiques ; `console.log` de données sensibles (**Critique**).

---

## Volet B — Transversal (dette structurelle)

**B1 · Valeurs hardcodées + Tests absents** → `AUDIT_TRANSVERSAL_B1.md`
- Hardcodé hors système de styles/constantes : couleurs, espacements/typo, **constantes métier**, **clés & URLs** (`sk_live_`, `whsec_`, JWT `eyJ`…), textes UI, config technique (timeouts, limits, noms de tables/buckets).
- Tests : framework configuré ? logique métier / routes API / policies d'accès sans test ? (aucun framework = **Critique**).

**B2 · Gestion des erreurs + Logging** → `AUDIT_TRANSVERSAL_B2.md`
- Appels DB/fetch sans vérification d'erreur / try-catch ; formulaires sans gestion d'erreur ; promesses non gérées (sans `await`/`.catch`) ; états `error` capturés mais non affichés ; actions destructives sans confirmation.
- `console.log` en prod (sensibles = **Critique**) ; pas de tracking d'erreurs (Sentry) ; logs serveur non structurés ; webhook paiements non loggué ; monitoring perf (informatif).

---

## Volet C — Qualité (comment c'est écrit)

**C1 · TypeScript + Structure** → `AUDIT_QUALITE_C1.md`
- Contournements de types (`any`, `as`, `@ts-ignore`, `!` non justifié) ; types trop larges (`string` au lieu d'union) ; types dupliqués ; fonctions critiques sans type de retour.
- Fichiers > 200 lignes ; fonctions > 40 lignes ; nommage ambigu ; logique dupliquée (DRY) ; structure de dossiers ; ordre des imports.

**C2 · Composants UI + Mobile + Perf web** → `AUDIT_QUALITE_C2.md`
- Composants > 150 lignes ; re-renders inutiles (props inline, pas de `useCallback`/`useMemo`) ; `useEffect` mal utilisé ; `'use client'` abusif ; fetch client au lieu de serveur ; props drilling.
- Mobile (si applicable) : `ScrollView` sur listes longues (→ `FlatList`) ; animations sans `useNativeDriver` ; images non optimisées ; listeners non nettoyés ; `Dimensions.get` statique.
- Perf web : images/fonts non optimisées ; métadonnées SEO ; bundle non tree-shakeable (`import *`).

**C3 · Requêtes DB + SQL & migrations** → `AUDIT_QUALITE_C3.md`
- `select('*')` ; N+1 ; index manquants sur colonnes filtrées ; subscriptions non désabonnées ; requêtes sans `.limit()` ; requêtes dupliquées.
- Migrations non idempotentes ; colonnes sans contraintes (`NOT NULL`/`CHECK`/FK `ON DELETE`) ; timestamps standards + trigger `updated_at` ; nommage `snake_case` ; fonctions SQL trop complexes ; policies RLS mal optimisées (sous-requêtes vs `auth.uid()` direct).

> Marque « Non applicable » toute catégorie hors périmètre (pas de mobile, pas de paiements, pas de SQL…).

---

## Format de rapport (par dimension)

```markdown
# Audit <volet> — <code> : <catégories>
Date : [date]  ·  Fichiers analysés : X  ·  Critique : X | Élevé : X | Moyen : X

## <Catégorie>
### <Risque>
| Sévérité | Fichier | Ligne | Constat | Action |
|---|---|---|---|---|
```
Une section vide → « Aucune occurrence détectée ».

## Synthèse finale → `AUDIT_SYNTHESE.md`

Une fois toutes les dimensions terminées, agréger :
1. **Tableau de bord** : total par sévérité, par volet et global.
2. **Top 10** des problèmes les plus critiques (impact réel users/sécurité).
3. **Plan en 3 sprints** : Sécurité (Critiques — avant tout déploiement) · Stabilité (Élevés — avant démo) · Dette (Moyens — backlog).

Ne modifier aucun rapport existant.
