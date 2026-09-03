# Architecture — [PROJECT_NAME]

> Répond à **« c'est quoi, et comment c'est bâti ? »** — le *pourquoi* est dans
> `.memory/decisions.md`. **Public** — alimente les pages « Objectifs &
> périmètre » et « Architecture » du site de doc.
>
> Ce fichier a absorbé l'ancien `charter.md` : sous la nouvelle architecture, le
> **but** du projet vit dans le champ `cap:` de `state.md`, la **stack** dans
> `stack.md`, le **rôle de l'agent** dans le `CLAUDE.md` — il ne restait à la
> charte que ce qui suit.

## Ce que c'est

[DESCRIPTION_1_PHRASE]

**Le domaine** — [à remplir : les utilisateurs visés, la valeur produite, le
contexte métier. De quoi comprendre le projet sans lire le code.]

## Les frontières

- **Dans le périmètre** : [à remplir]
- **Hors périmètre** : [à remplir — aussi important que ce qui est dedans]

| Rôle | Qui / responsabilité |
|---|---|
| [ex : PO] | [à remplir] |
| [ex : Tech Lead] | [à remplir] |

<!-- Facturation / clients : n'ajouter une section « ## Clients & facturation »
     (onboarding, essai, paiement, résiliation) que si le projet a une dimension
     paiement. Sinon, ne pas créer cette section. -->

## Les couches

### Sources & ingestion
- [À compléter — ex : API REST tierce, fichiers SFTP, webhooks Stripe]

### Traitement / pipeline
- [À compléter — ex : ADF, dbt, Airflow, scripts Python]

### Stockage
- [À compléter — ex : Snowflake, PostgreSQL, Supabase, S3]

### API / backend
- [À compléter — ex : FastAPI, Next.js API routes, Edge Functions]

### Frontend / dataviz
- [À compléter — ex : Power BI, Next.js, Expo, Streamlit]

## Flux de données

```
[SOURCE] → [TRAITEMENT] → [STOCKAGE] → [API] → [FRONTEND]
```

## Modèle de données

_Résumé des entités principales et de leurs relations. Pour un projet
**data-lourd**, le détail vit dans `.memory/data-model.md` (couches
raw/staging/marts) et on ne garde ici qu'un renvoi — **jamais les deux** : un
contenu recopié à deux endroits diverge au premier changement._

- [à remplir — entités clés, relations, conventions de nommage]

## Les pièges

_Ce qui a déjà cassé, et le signe qui l'annonce. Un piège documenté vaut dix
règles : c'est la section qui fait gagner le plus de temps à un arrivant._

- [à remplir]

<!-- Les environnements et la table des outils sont dans stack.md.
     Identifiants, secrets, IP autorisées : dans .memory/operations.md (privé). -->
