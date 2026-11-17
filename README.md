# Recipe API

API FastAPI de gestion de recettes (authentification JWT, partage de recettes entre utilisateurs).
Base PostgreSQL, schéma géré par Alembic, déployée sur Scalingo.

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
pip install -r requirements.txt

# 4. Schéma de la base puis données de démo (utilisateur demo / demo1234)
alembic upgrade head
python seed.py

# 5. Lancer l'API
uvicorn main:app --reload
```

- Documentation Swagger : http://localhost:8000/docs
- Santé de l'API et de la base : http://localhost:8000/health

## Variables d'environnement

| Variable | Rôle |
|---|---|
| `DATABASE_URL` | URL PostgreSQL en local (`postgresql://user:pass@host:5432/db`) |
| `SCALINGO_POSTGRESQL_URL` | Fournie automatiquement par l'addon PostgreSQL sur Scalingo (prioritaire sur `DATABASE_URL`) |
| `SECRET_KEY` | Clé de signature des JWT (obligatoire, secrète) |
| `ALGORITHM` | Algorithme JWT (défaut `HS256`) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Durée de validité du token (défaut `30`) |
| `CORS_ORIGINS` | URL(s) du client autorisées, séparées par des virgules |

## Modifier le schéma de la base

```bash
# après avoir modifié un modèle dans models/
alembic revision --autogenerate -m "description du changement"
alembic upgrade head
```

Les fichiers de `alembic/versions/` sont versionnés : sur Scalingo, `alembic upgrade head`
est lancé automatiquement après chaque déploiement (process `postdeploy` du `Procfile`).

## Déploiement sur Scalingo

```bash
scalingo create <app-api> --region osc-fr1
scalingo --app <app-api> addons-add postgresql postgresql-starter-512
scalingo --app <app-api> env-set SECRET_KEY=<valeur-aleatoire> CORS_ORIGINS=https://<url-du-client>
git push scalingo master:main
scalingo --app <app-api> run python seed.py      # une seule fois
```

Contrôle : `https://<app-api>.osc-fr1.scalingo.io/health` répond 200 et `/docs` affiche Swagger.
