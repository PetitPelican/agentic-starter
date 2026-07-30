# Architecture — [PROJECT_NAME]
_Dernière mise à jour : YYYY-MM-DD_

> Répond à **« comment c'est bâti ? »** (le *pourquoi* est dans `decisions.md`). **Public** — sert de base à la page « Architecture » du site.

## Vue d'ensemble

[DESCRIPTION_COURTE — ex: pipeline data (API SaaS → entrepôt → dataviz)]

## Couches

### Sources & ingestion
- [À compléter — ex: API REST tierce, fichiers SFTP, webhooks Stripe]

### Traitement / pipeline
- [À compléter — ex: ADF, dbt, Airflow, scripts Python]

### Stockage
- [À compléter — ex: Snowflake, PostgreSQL, Supabase, S3]

### API / backend
- [À compléter — ex: FastAPI, Next.js API routes, Edge Functions]

### Frontend / dataviz
- [À compléter — ex: Power BI, Next.js, Expo, Streamlit]

## Flux de données

```
[SOURCE] → [TRAITEMENT] → [STOCKAGE] → [API] → [FRONTEND]
```

## Modèle de données

_Résumé des entités/tables principales et de leurs relations. Pour un projet **data-lourd**, détailler dans un fichier `data-model.md` séparé (couches raw/staging/marts) et ne garder ici qu'un renvoi._

- [à remplir — entités clés, relations, conventions de nommage]

## Environnements

| Env | URL / endpoint (non sensible) | Notes |
|---|---|---|
| Dev | | |
| Staging | | |
| Prod | | |

<!-- Identifiants, secrets, comptes de service, IP autorisées : dans operations.md (privé), pas ici. -->

