# Recipe API

Application de gestion de recettes : un client web, une API FastAPI (authentification JWT,
partage de recettes entre utilisateurs) et une base PostgreSQL dont le schéma est géré par Alembic.
Le tout est déployé sur Scalingo.

[![CI](https://github.com/Shakil60/FastAPI/actions/workflows/ci.yml/badge.svg)](https://github.com/Shakil60/FastAPI/actions/workflows/ci.yml)

## Liens publics

| Composant | URL |
|---|---|
| Client | https://fastapi-client.osc-fr1.scalingo.io |
| API (Swagger) | https://fastapi.osc-fr1.scalingo.io/docs |
| Santé API + base | https://fastapi.osc-fr1.scalingo.io/health |

Compte de démo : `demo` / `demo1234`.

## Architecture

```
 Navigateur
     │  HTTPS
     ▼
┌──────────────────────────┐        ┌──────────────────────────┐        ┌───────────────────────┐
│ App Scalingo             │ fetch  │ App Scalingo             │  SQL   │ Addon PostgreSQL      │
│ fastapi-client           │ ─────▶ │ fastapi                  │ ─────▶ │ postgresql-starter-512│
│ HTML/CSS/JS statique     │  JSON  │ FastAPI + Uvicorn        │        │ (SCALINGO_POSTGRESQL_ │
│ (buildpack static/nginx) │ + JWT  │ CORS limité au client    │        │  URL)                 │
└──────────────────────────┘        └──────────────────────────┘        └───────────────────────┘
```

- **Client** (`client/`) : pages statiques sans framework ni build. Il appelle l'API avec `fetch` et garde
  le token JWT dans `localStorage`. L'URL de l'API se règle dans `client/config.js`
  (`localhost:8000` en local, l'app Scalingo en ligne).
- **API** : découpée en couches.
  - `routes/` : endpoints HTTP, validation des droits, codes d'erreur.
  - `services/` : logique métier et accès aux données (hachage Argon2, JWT, règles de partage).
  - `models/` : tables SQLAlchemy (`users`, `recipes`, `accesses`).
  - `schemas/` : modèles Pydantic d'entrée et de sortie (le mot de passe n'est jamais renvoyé).
  - `config.py` : toute la configuration vient des variables d'environnement.
- **Base** : PostgreSQL 16, en local avec `docker compose` et en production avec l'addon Scalingo.
  Le schéma n'est jamais créé par l'application : il passe uniquement par les migrations `alembic/versions/`.
- **Droits** : un utilisateur voit ses recettes et celles qu'on lui a partagées. Un partage donne la lecture
  seule ou la lecture et la modification. Seul le propriétaire peut supprimer une recette.
- **CI** (`.github/workflows/ci.yml`) : elle se lance à chaque push et à chaque pull request, sur un
  PostgreSQL 16 de service. Elle exécute `alembic upgrade head`, puis `alembic check` (aucune migration
  manquante), puis `pytest`.

## Lancer en local

Prérequis : Python 3.13, Docker.

```bash
# 1. Base PostgreSQL locale
docker compose up -d

# 2. Configuration : copier l'exemple puis renseigner SECRET_KEY
cp .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(32))"   # valeur pour SECRET_KEY

# 3. Dépendances
python -m venv .venv
.venv\Scripts\activate          # Windows  (Linux/macOS : source .venv/bin/activate)
pip install -r requirements-dev.txt

# 4. Schéma de la base puis données de démo (utilisateur demo / demo1234)
alembic upgrade head
python seed.py

# 5. Lancer l'API (http://localhost:8000/docs)
uvicorn main:app --reload

# 6. Dans un autre terminal, servir le client (http://localhost:5173)
python -m http.server 5173 -d client
```

Tests : `pytest` (ils utilisent la base définie par `DATABASE_URL` et la vident entre chaque test).

## Variables d'environnement

Les valeurs ne sont jamais versionnées : `.env` est ignoré par git et `.env.example` sert de modèle.

**App API (`fastapi`)**

| Variable | Rôle |
|---|---|
| `SCALINGO_POSTGRESQL_URL` | Fournie automatiquement par l'addon PostgreSQL (prioritaire sur `DATABASE_URL`) |
| `DATABASE_URL` | URL PostgreSQL en local (`postgresql://user:pass@host:5432/db`) |
| `SECRET_KEY` | Clé de signature des JWT (obligatoire, secrète) |
| `ALGORITHM` | Algorithme JWT (défaut `HS256`) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Durée de validité du token (défaut `30`) |
| `CORS_ORIGINS` | URL(s) du client autorisées, séparées par des virgules |

**App client (`fastapi-client`)**

| Variable | Rôle |
|---|---|
| `PROJECT_DIR` | `client` : Scalingo ne déploie que ce sous-dossier du dépôt |
| `BUILDPACK_NAME` | `static` : sert les fichiers avec nginx |

## Modifier le schéma de la base

```bash
# après avoir modifié un modèle dans models/
alembic revision --autogenerate -m "description du changement"
alembic upgrade head
```

Les fichiers de `alembic/versions/` sont versionnés. Sur Scalingo, `alembic upgrade head` est lancé
automatiquement après chaque déploiement (process `postdeploy` du `Procfile`). La CI échoue si un
modèle a changé sans migration.

## Déploiement sur Scalingo

Le même dépôt GitHub alimente deux apps : l'API (racine du dépôt, `Procfile`) et le client (`client/`).

**1. API**

```bash
scalingo create fastapi --region osc-fr1
scalingo --app fastapi addons-add postgresql postgresql-starter-512
scalingo --app fastapi env-set SECRET_KEY=<valeur-aleatoire>
git remote add scalingo git@ssh.osc-fr1.scalingo.com:fastapi.git
git push scalingo main
scalingo --app fastapi run python seed.py      # une seule fois
```

Le `Procfile` déclare `web` (Uvicorn sur `$PORT`) et `postdeploy` (migrations).

**2. Client**

```bash
scalingo create fastapi-client --region osc-fr1
scalingo --app fastapi-client env-set PROJECT_DIR=client BUILDPACK_NAME=static
git remote add scalingo-client git@ssh.osc-fr1.scalingo.com:fastapi-client.git
git push scalingo-client main
```

**3. Relier le client à l'API**

```bash
scalingo --app fastapi env-set CORS_ORIGINS=https://fastapi-client.osc-fr1.scalingo.io
```

**Contrôle**
- `https://fastapi.osc-fr1.scalingo.io/health` répond `{"status":"ok"}`.
- Le client affiche la page de connexion, et la connexion avec `demo` / `demo1234` liste les recettes.
- En cas d'erreur : `scalingo --app <app> logs --lines 200` avant toute autre action.

## Coût mensuel

Région `osc-fr1`, prix HT, un conteneur par app, sans scaling.

| Ressource | Plan | Estimé | Réel |
|---|---|---|---|
| App `fastapi` (API) | 1 conteneur M (512 Mo) | ~14,40 € | _à relever sur la facture Scalingo_ |
| Addon PostgreSQL | Starter 512M | ~7,20 € | _à relever_ |
| App `fastapi-client` | 1 conteneur S (256 Mo) | ~7,20 € | _à relever_ |
| **Total** | | **~28,80 €** | |

Pistes d'économie : passer l'API en conteneur S (l'empreinte mémoire d'Uvicorn le permet), ou servir le
client directement depuis l'API pour n'avoir qu'une seule app.
