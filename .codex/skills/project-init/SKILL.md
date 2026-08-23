---
name: project-init
description: >
  Initialise la structure Codex/agentic-starter d'un nouveau projet.
  Scanne tous types de fichiers, détecte la stack, suggère MCPs/CLIs, pose 6 questions,
  personnalise AGENTS.md (rôle, règles adaptées), pré-remplit les fichiers mémoire,
  propose le site de doc (/publish-docs).
  Reprenable : chaque phase teste si elle est déjà faite. `/project-init --verifier` = état, lecture seule.
  Trigger: /project-init ou "initialise ce projet"
---

# Agent Init

## Prérequis

Le dossier `.codex/` doit être présent dans le projet.

**Nouveau projet (répertoire vide) :**
```bash
git clone https://github.com/PetitPelican/agentic-starter.git .
```

**Projet existant (code déjà présent) :**
```bash
# Linux / Mac
git clone https://github.com/PetitPelican/agentic-starter.git /tmp/agentic-starter
cp -r /tmp/agentic-starter/.codex ./
rm -rf /tmp/agentic-starter

# Windows PowerShell
git clone https://github.com/PetitPelican/agentic-starter.git $env:TEMP\agentic-starter
Copy-Item -Recurse "$env:TEMP\agentic-starter\.codex" ".\.codex"
Remove-Item -Recurse -Force "$env:TEMP\agentic-starter"
```

Si `.codex/` (ou `.claude/`) est absent, affiche ces instructions et arrête. Le choix du harnais à conserver se fait en Phase 0.

---

## Détection du contexte

Avant de démarrer, détecte si c'est un projet nouveau ou existant :
- **Projet existant** : présence de fichiers de code (`src/`, `app/`, `*.py`, `*.ts`, etc.) OU d'un historique git (`git log` retourne des commits)
- **Nouveau projet** : répertoire quasi-vide (uniquement `.codex/`, `AGENTS.md`, `.gitignore`, `README.md`)

En mode **projet existant** :
- Ne pas modifier les fichiers qui existent déjà hors de `.codex/`
- Ne pas écraser un `AGENTS.md` déjà personnalisé (vérifier si `[PROJECT_NAME]` est encore présent)
- Pour les fichiers mémoire : ne créer que ceux qui n'existent pas encore
- Signaler à l'utilisateur ce qui existait déjà vs ce qui a été ajouté

---

## Reprise et idempotence

`project-init` est **reprenable**. Chaque phase commence par un test bon marché
qui dit si elle est déjà faite : un agent qui dévie au milieu d'une init ne
laisse plus un dépôt à moitié configuré sans moyen de savoir quoi.

La vérité vient du **système de fichiers**, jamais d'un fichier d'état — un état
ment dès qu'on touche au dépôt à la main. Les seules décisions non déductibles
des fichiers (choix du harnais, refus du site) sont consignées dans
`.memory/decisions.md`, dont c'est déjà le rôle.

**Au lancement, exécute la grille et affiche-la AVANT toute action :**

| Phase | Faite si | Sinon |
|---|---|---|
| 0 — harnais | un seul harnais présent, **ou** choix consigné dans `decisions.md` | reposer la question |
| 1 — scan | *rien à mémoriser* — toujours refait, c'est peu coûteux | — |
| 2 — questions | bloc `## Initialisation` dans `.memory/decisions.md` | reposer **uniquement** les questions manquantes |
| 3 — contexte | plus aucun `[PROJECT_NAME]` dans le(s) fichier(s) de contexte | remplacer ce qui reste |
| 3 — mémoire | plus aucun `[PROJECT_NAME]` dans `.memory/*.md` | traiter fichier par fichier |
| 3 — site | `site/_content/example/` absent, **ou** refus consigné | reproposer |
| 4 — permissions | `defaultMode: bypassPermissions` dans `.codex/settings.local.json` | l'ajouter |

```bash
grep -rl "\[PROJECT_NAME\]" CLAUDE.md AGENTS.md .memory/*.md 2>/dev/null
ls -d .claude .codex site/_content/example 2>/dev/null
grep -q "bypassPermissions" .codex/settings.local.json 2>/dev/null && echo "phase 4 ok"
grep -q "^## Initialisation" .memory/decisions.md 2>/dev/null && echo "phase 2 ok"
```

Affichage attendu :

```
  Phase 0  harnais       ✅ Codex retiré
  Phase 1  scan          ↻ à refaire (rapide)
  Phase 2  questions     ✅ 6/6 consignées dans decisions.md
  Phase 3  contexte      ⏳ CLAUDE.md ok · .memory/ : 4 fichiers avec [PROJECT_NAME]
  Phase 4  permissions   ⏳ à appliquer

  → reprise en phase 3
```

**Règles absolues.** Ne redemande jamais une réponse déjà consignée. Ne refais
jamais une phase marquée ✅. Toute phase relancée sur un projet déjà initialisé
doit être **sans effet** — comme l'est `agentic-upgrade`.

### `/project-init --verifier`

Même grille, **lecture seule** : n'exécute aucune phase, affiche l'état, et
s'arrête. Sert à constater qu'une init est complète, et de test de
non-régression au skill lui-même.

---

## Phase 0 — Choix du/des agent(s)

Avant tout, demande à l'utilisateur quel(s) assistant(s) il compte utiliser sur ce projet :

« Quel(s) assistant(s) vas-tu utiliser sur ce projet ? »
- **Claude Code** uniquement
- **Codex** uniquement
- **Les deux**

Le starter embarque les deux harnais en miroir (`.claude/` + `CLAUDE.md` pour Claude Code, `.codex/` + `AGENTS.md` pour Codex). Selon la réponse, **supprime le harnais non retenu** (action destructive → afficher la liste exacte des chemins et demander une confirmation unique avant de supprimer) :

| Réponse | Garder | Supprimer |
|---|---|---|
| Claude Code | `.claude/`, `CLAUDE.md` | `.codex/`, `AGENTS.md` |
| Codex | `.codex/`, `AGENTS.md` | `.claude/`, `CLAUDE.md` |
| Les deux | tout | rien |

```bash
# Claude Code uniquement
rm -rf .codex AGENTS.md          # Linux/Mac
Remove-Item -Recurse -Force .codex, AGENTS.md   # Windows PowerShell

# Codex uniquement
rm -rf .claude CLAUDE.md
Remove-Item -Recurse -Force .claude, CLAUDE.md
```

Pour la suite de l'init, ne personnalise et ne cite que le(s) fichier(s) de contexte conservé(s) (`CLAUDE.md` et/ou `AGENTS.md`).

> Note : si tu es en train d'exécuter ce skill, c'est que le harnais courant existe. Ne supprime jamais le harnais depuis lequel tu tournes sans confirmation explicite (ex. Codex ne s'auto-supprime pas `.codex/` s'il l'utilise).

**Consigne le choix** dans `.memory/decisions.md` (bloc `## Initialisation`, créé
s'il manque) : c'est la seule façon de distinguer « les deux harnais retenus »
de « la phase 0 n'a jamais tourné ».

---

## Phase 1 — Scan automatique

Lis **tout** ce que tu trouves dans le répertoire courant. Ne te limite pas aux fichiers code.

### Fichiers de config / stack
- `package.json`, `requirements.txt`, `go.mod`, `pyproject.toml`, `Cargo.toml`, `pom.xml`, `build.gradle`
- `dbt_project.yml`, `airflow.cfg`, `prefect.yaml`, `dagster.yaml`
- `docker-compose.yml`, `Dockerfile`, `kubernetes/`, `.github/workflows/`
- `.mcp.json` — MCPs déjà configurés
- `.env.example` — variables d'environnement déclarées

### Fichiers de documentation & métier
Lis tout fichier lisible qui décrit le projet : README, specs, cahiers des charges, business plans, PRDs, wireframes décrits en texte.
- `.md`, `.txt`, `.rst` — lecture directe
- Tout fichier dont le nom contient : `spec`, `brief`, `cahier`, `requirements`, `roadmap`, `business`

**Fichiers binaires — procédure d'extraction obligatoire :**

Pour chaque fichier `.docx` trouvé, tente dans l'ordre :
```bash
# Option 1 — pandoc (le plus fiable)
pandoc "<fichier>" -t plain --wrap=none

# Option 2 — python-docx
python -c "import docx; print('\n'.join([p.text for p in docx.Document('<fichier>').paragraphs]))"

# Option 3 — docx2txt
docx2txt "<fichier>" -

# Option 4 — LibreOffice
soffice --headless --convert-to txt "<fichier>" --outdir /tmp && cat /tmp/<nom>.txt
```
Si aucune option ne fonctionne, affiche : "Fichier `<nom>.docx` non extractible — résume-moi son contenu en quelques phrases." et attends la réponse avant de continuer.

Pour chaque fichier `.pdf` trouvé, tente dans l'ordre :
```bash
# Option 1 — pdftotext (poppler)
pdftotext "<fichier>" -

# Option 2 — python pdfminer
python -c "from pdfminer.high_level import extract_text; print(extract_text('<fichier>'))"

# Option 3 — pymupdf
python -c "import fitz; doc=fitz.open('<fichier>'); print('\n'.join([p.get_text() for p in doc]))"
```
Si aucune option ne fonctionne : "Fichier `<nom>.pdf` non extractible — résume-moi son contenu en quelques phrases."

Pour chaque fichier `.xlsx` ou `.csv` trouvé, tente :
```bash
# CSV — lecture directe (premiers 50 lignes)
head -50 "<fichier>"

# XLSX — python openpyxl
python -c "import openpyxl; wb=openpyxl.load_workbook('<fichier>'); [print(row) for sheet in wb.sheetnames for row in wb[sheet].iter_rows(values_only=True, max_row=20)]"
```

**Règle** : ne passe pas au rapport de scan tant qu'un fichier métier extractible n'a pas été lu. Les fichiers métier sont prioritaires sur les fichiers de code pour comprendre le projet.

### CLIs installés
Vérifie la présence de chaque CLI via `command -v` (ou `where` sur Windows) :
`git`, `vercel`, `eas`, `supabase`, `stripe`, `dbt`, `kubectl`, `helm`, `terraform`, `aws`, `gcloud`, `az`, `snowflake`, `airbyte`, `prefect`, `dagster`, `poetry`, `conda`

### Rapport de scan
Synthétise en une liste courte :
- Stack détectée (frameworks, langages, BDD, cloud)
- Services externes identifiés (Supabase, Snowflake, Stripe, S3, etc.)
- CLIs présents
- MCPs déjà configurés
- Ce que tu as compris du projet (en 2-3 phrases max)

---

## Phase 2 — Questions (6)

Pose chaque question une par une. Attends la réponse avant de continuer.

**Q1 — Nom et description**
"Quel est le nom de ce projet et en une phrase, qu'est-ce qu'il fait ?"

**Q2 — Rôle de l'agent**
"Dans ce projet, quel rôle dois-je jouer ?" Propose des options selon le scan :
- CTO / Tech Lead (projets produit, SaaS, fullstack)
- Data Engineer / Architecte data (projets pipeline, warehouse)
- Lead Data Scientist (projets ML, analyse)
- Développeur senior (projet sans dimension produit)
- Assistant technique (projet sans décision d'archi à déléguer)
- Autre → laisser l'utilisateur décrire librement

**Q3 — Type de projet**
"Quel est le type de projet ?" Présente uniquement les options cohérentes avec le scan :
- Web app (frontend + backend)
- Mobile app
- Fullstack web + mobile
- API backend
- SaaS multi-tenant
- Data pipeline / ETL
- Data science / ML
- Data warehouse / Analytics
- Script / automatisation

**Q4 — Domaines actifs**
"Quels domaines sont actifs dans ce projet ?" (plusieurs réponses) :
`frontend` · `backend` · `mobile` · `base de données` · `authentification` · `paiements` · `data pipeline` · `SQL/warehouse` · `Python/ML` · `orchestration` · `API routes` · `documentation API`

**Q5 — Outils**
Basé sur le scan, liste les services/MCPs/CLIs **détectés** et demande confirmation + ce qui manque :
"J'ai détecté [X, Y, Z]. Est-ce complet ? Y a-t-il d'autres outils à configurer ?"

Référence de MCPs disponibles selon les services détectés :
| Service détecté | MCP à suggérer |
|---|---|
| Supabase | `@supabase/mcp-server-supabase` |
| Stripe | `@stripe/mcp` |
| Notion | `@notionhq/notion-mcp-server` |
| Snowflake | `@modelcontextprotocol/server-snowflake` |
| PostgreSQL direct | `@modelcontextprotocol/server-postgres` |
| GitHub | `@modelcontextprotocol/server-github` |
| Slack | `@modelcontextprotocol/server-slack` |
| AWS | `mcp-server-aws` |
| Linear | `@linear/mcp-server` |
| Jira | `@modelcontextprotocol/server-jira` |

Si un service est détecté mais son MCP n'est pas dans `.mcp.json`, suggère-le explicitement avec la commande d'installation.

**Q6 — Contraintes**
"Y a-t-il des contraintes spécifiques ?" (plusieurs réponses) :
`multi-tenant` · `RBAC strict` · `conformité RGPD` · `conformité SOC2` · `budget infra limité` · `pas de git` · `pas d'IA dans le produit` · `déploiement on-premise` · `autre`

**Consigner les six réponses.** Avant de passer en phase 3, écris dans
`.memory/decisions.md` un bloc :

```markdown
## Initialisation

- harnais : Claude Code | Codex | les deux
- Q1 nom / description : …
- Q2 rôle : …
- Q3 type de projet : …
- Q4 domaines : …
- Q5 outils : …
- Q6 contraintes : …
- site de doc : oui | refusé le AAAA-MM-JJ
```

Sans ce bloc, une reprise redemanderait les six questions. Il rend aussi les
décisions d'init relisibles bien après, ce que `decisions.md` est fait pour.

---

## Phase 3 — Personnalisation

### Fichier(s) de contexte (`CLAUDE.md` et/ou `AGENTS.md` selon Phase 0)

Applique les remplacements ci-dessous au(x) fichier(s) conservé(s) en Phase 0 — `CLAUDE.md` pour Claude Code, `AGENTS.md` pour Codex, les deux si « Les deux ». Le contenu est identique dans les deux fichiers.

**Section Rôle** — remplacer :
- `[PROJECT_NAME]` → nom du projet
- `[ROLE]` → rôle choisi en Q2, adapté :
  - CTO/Tech Lead → "tu es le CTO/Tech Lead de **[PROJECT_NAME]**"
  - Data Engineer → "tu es le Data Engineer / Architecte data de **[PROJECT_NAME]**"
  - Data Scientist → "tu es le Lead Data Scientist de **[PROJECT_NAME]**"
  - Autre → reformuler selon la réponse libre
- `[DESCRIPTION_1_PHRASE]` → description fournie
- `[STACK]` → stack détectée + confirmée
- Phase actuelle → adapter selon le contexte détecté

**Section Règles** — sélectionner uniquement les règles pertinentes :

| Règle | Inclure si |
|---|---|
| Git (commit/push sur demande) | `git` détecté dans CLIs ET projet versionné |
| TypeScript strict | TypeScript détecté dans la stack |
| Zéro valeur hardcodée CSS | Frontend web détecté |
| Python strict (mypy/pyright) | Python détecté, pas de TS |
| Pas de print() / logging structuré | Python détecté |
| Idempotence pipelines | Data pipeline confirmé (Q4) |
| RLS / RBAC côté serveur | Multi-tenant ou RBAC strict (Q6) |
| Clés restreintes en prod | Paiements confirmés (Q4) |

Ne pas inclure une règle si elle ne s'applique pas au projet. Ne pas laisser les règles avec "(supprimer si non applicable)".

**Section Outils** — remplir avec les outils confirmés en Q5 uniquement. Si MCP suggéré mais pas encore installé, le lister avec la mention `(à installer)`.

### Memory (taxonomie : charter / architecture / rules / decisions / state / operations)

- `charter.md` : remplacer `[PROJECT_NAME]` + date ; description (Q1), stack détectée, rôles (Q2 + mentionnés), but & périmètre. Ajouter une section « Clients & facturation » **uniquement** si paiements confirmés (Q4).
- `architecture.md` : remplacer `[PROJECT_NAME]` + pré-remplir depuis le scan :
  - **Sources & ingestion** → connecteurs / APIs / webhooks détectés
  - **Traitement / pipeline** → outils détectés (dbt, Airflow, ADF, scripts Python, etc.)
  - **Stockage** → BDD détectées (Snowflake, PostgreSQL, Supabase, S3, etc.)
  - **API / backend** & **Frontend / dataviz** → frameworks détectés (FastAPI, Next.js, Power BI, Expo…)
  - **Flux de données** → schéma `SOURCE → TRAITEMENT → STOCKAGE → API → FRONTEND` avec les vrais noms
  - **Modèle de données** → entités principales (détailler dans `data-model.md` si data-lourd)
  - Laisser vide les couches non détectées plutôt que de deviner
- `rules.md` : remplacer `[PROJECT_NAME]` + contraintes (Q6) + règles d'accès (RBAC/RLS) si multi-tenant / RBAC (Q6)
- `decisions.md` : remplacer `[PROJECT_NAME]` + une entrée initiale si un choix de stack marquant ressort du scan ; sinon laisser le gabarit
- `state.md` : remplacer `[PROJECT_NAME]` + date du jour
- `operations.md` : remplacer `[PROJECT_NAME]` + **référencer** (sans valeurs) où vivent les secrets (`.env*.local`, coffre…) et l'hébergement détecté (cloud via CLIs). 🔒 privé — jamais publié.
- `data-model.md` : conserver **uniquement** si SQL/warehouse ou data pipeline (Q4) ; pré-remplir les couches pertinentes (raw/staging/marts) ; sinon **supprimer** (le modèle vit dans `architecture.md`)
- `MEMORY.md` : remplacer `[PROJECT_NAME]` + retirer la ligne `data-model.md` si le fichier a été supprimé

### MCPs non installés

Pour chaque MCP suggéré mais absent de `.mcp.json`, générer le bloc JSON à ajouter et afficher la commande d'installation.

### Site de documentation (optionnel)

Proposer : « Veux-tu un **site de documentation Quarto** (HTML + Word/PDF), généré depuis la mémoire ? »
- Si **oui** → invoquer `/publish-docs init` avec `preset` déduit du type de projet (Q3 : data-pipeline→`data`, web-app→`web`, API→`api`, sinon `generic`), puis `/publish-docs setup` si Quarto/Graphviz manquent.
- Si **non** → ne rien créer (le dossier `site/` reste absent ; on pourra le faire plus tard via `/publish-docs init`). **Consigner le refus** dans le bloc `## Initialisation` de `decisions.md`, sinon chaque reprise reproposera le site.

---

## Phase 4 — Bypass des permissions

Vérifie et corrige les permissions pour éviter les prompts d'approbation à chaque action.

### `settings.local.json` (projet)
Vérifie que `.codex/settings.local.json` contient `"defaultMode": "bypassPermissions"` dans `permissions`.
- Si absent : l'ajouter
- Si le fichier n'existe pas : le créer avec ce contenu minimal :
```json
{
  "permissions": {
    "defaultMode": "bypassPermissions"
  }
}
```

### `~/.codex/settings.json` (global)
Vérifie que le fichier global contient aussi `"defaultMode": "bypassPermissions"`.
- Si absent : proposer à l'utilisateur de l'ajouter (action sur le fichier global — demander confirmation)
- Si le fichier n'existe pas : proposer de le créer

**Important :** après toute modification de settings, indiquer à l'utilisateur de faire `Shift+Ctrl+P` → **Developer: Reload Window** pour que les changements prennent effet.

---

## Résumé de fin

En fin d'init, afficher :
1. Ce qui a été personnalisé (harnais retenu, fichier(s) de contexte, memory pré-remplie) + le harnais supprimé le cas échéant
2. MCPs à installer (commandes exactes)
3. Prochaine action recommandée (`/memory-update` pour valider l'état initial)

---

## Règles d'exécution

- Ne pas modifier les skills (`caveman/`, `caveman-compress/`, `memory-update.md`)
- Ne pas modifier `settings.json`
- Toujours confirmer la suppression du harnais non retenu (Phase 0) avant d'exécuter (liste des chemins + confirmation unique) ; ne jamais supprimer le harnais courant sans confirmation explicite
- Si un fichier n'est pas lisible (Excel, PDF) et qu'aucun outil n'est disponible, le signaler et continuer
