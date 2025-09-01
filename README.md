# CRM Maroc - Système de gestion commerciale et comptable

Un système complet de CRM, facturation et comptabilité adapté au contexte marocain, développé avec Django 5 et des technologies modernes.

## 🚀 Fonctionnalités principales

### CRM & Gestion commerciale
- **Gestion des contacts** : Clients, fournisseurs, prospects
- **Catalogue produits/services** : Gestion des prix, TVA, stocks
- **Devis et factures** : Création, validation, envoi par email
- **Bons de commande** : Achats et ventes
- **Gestion des paiements** : Rapprochement, lettrage comptable
- **Avoirs** : Gestion des retours et remises

### Comptabilité
- **Plan comptable marocain** : Structure PCM paramétrable
- **Journaux comptables** : Ventes, Achats, Banque, Caisse
- **Écritures automatiques** : Génération lors de la validation des documents
- **Grand-livre et balance** : Rapports comptables complets
- **Déclaration TVA** : Calcul automatique, export PDF/CSV

### Multi-entreprise
- **Séparation des données** : Chaque société a ses propres données
- **Séquences de numérotation** : Configurables par entreprise
- **Plans comptables** : Personnalisables par société
- **Gestion des utilisateurs** : Rôles et permissions par entreprise

### Sécurité et traçabilité
- **Authentification JWT** : API sécurisée
- **Sessions Django** : Interface web sécurisée
- **Historique des modifications** : Audit trail complet
- **Permissions RBAC** : Rôles : admin, comptable, vente, achat, lecture

## 🛠️ Technologies utilisées

- **Backend** : Django 5.0.2 + Django REST Framework
- **Base de données** : PostgreSQL 15 (SQLite supportée en dev)
- **Cache & tâches** : Redis + Celery
- **Frontend** : HTML + HTMX + TailwindCSS + Vanilla JS
- **PDF** : WeasyPrint
- **Stockage** : MinIO (S3-compatible)
- **Déploiement** : Docker + docker-compose

## 📋 Prérequis

- Docker et docker-compose (recommandé) OU Python 3.12 + Node (facultatif)
- Git
- Au moins 4GB de RAM disponible

## ⚙️ Configuration des variables d'environnement

Ne commitez jamais de secrets. Utilisez un fichier `.env` local basé sur l'exemple fourni.

```bash
cp env.example .env
# Éditez .env selon vos besoins (DB, MinIO, Email, etc.)
```

Variables principales (voir `env.example` pour la liste complète) :

```bash
# Django
DEBUG=True
SECRET_KEY=change-me
ALLOWED_HOSTS=localhost,127.0.0.1

# Base de données (choisissez une des deux approches)
DATABASE_URL=postgres://crm_user:crm_password@localhost:5432/crm_maroc  # PostgreSQL
# ou
# SQLite (dev rapide)
# Utilisez config/settings_sqlite.py si souhaité
```

## 🚀 Démarrage rapide (Docker recommandé)

```bash
git clone https://github.com/yassir-aea/CRM-Marocaine.git
cd CRM-Marocaine
cp env.example .env
# Assurez-vous que les ports 8080 (web) et 9000/9001 (MinIO) sont libres

# Lancer les services
make up

# Appliquer les migrations et créer un superutilisateur
make migrate
make superuser

# (Optionnel) Charger des données de démonstration
make seed
```

Accès:
- Interface web: `http://localhost:8080`
- Admin Django: `http://localhost:8080/admin`
- MinIO Console: `http://localhost:9001`

## 🚀 Démarrage rapide (local sans Docker)

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp env.example .env

# Base de données
# - PostgreSQL: créez la base et mettez à jour .env
# - ou SQLite: utilisez DJANGO_SETTINGS_MODULE=config.settings_sqlite

# Migrations et lancement
export DJANGO_SETTINGS_MODULE=config.settings_env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 0.0.0.0:8080
```

## 🏗️ Structure du projet
```
crm_maroc/
├── config/                 # Configuration Django
├── core/                   # Application principale
├── users/                  # Gestion des utilisateurs
├── companies/              # Gestion des sociétés
├── crm/                    # Gestion des contacts
├── catalog/                # Produits et services
├── billing/                # Facturation et paiements
├── accounting/             # Comptabilité
├── reports/                # Rapports et exports
├── settingsapp/            # Paramètres système
├── static/                 # Fichiers statiques
├── templates/              # Templates HTML
├── docker/                 # Configuration Docker
├── compose.yaml            # Services Docker
├── Makefile                # Commandes de développement
└── requirements.txt        # Dépendances Python
```

## 📖 Commandes Make utiles
```bash
make help          # Aide
make up            # Démarrer services
make down          # Arrêter
make build         # Rebuild images Docker
make migrate       # Migrations
make superuser     # Créer un superuser
make seed          # Données démo
make test          # Tests
make coverage      # Couverture
make fmt           # Formatage
make lint          # Lint
make clean         # Nettoyage
```

## 🔐 Bonnes pratiques (open-source)
- Ne pas committer `.env` ni secrets (voir `.gitignore`)
- Utiliser `env.example` pour documenter les variables
- Les fichiers de service (systemd) doivent rester des exemples sans secrets

## 🚀 Déployer et pousser sur GitHub

1) Initialiser le repo et configurer la remote:
```bash
git init
git add .
git commit -m "Initial public release (sanitized)"
git branch -M main
git remote add origin https://github.com/yassir-aea/CRM-Marocaine.git
git push -u origin main
```

2) Créer des tags de version (optionnel):
```bash
git tag -a v0.1.0 -m "Première version publique"
git push origin v0.1.0
```

3) Ouvrir le repo: `https://github.com/yassir-aea/CRM-Marocaine`

## 🔐 Authentification et permissions
- Rôles: admin, comptable, vente, achat, lecture
- JWT pour l'API REST (voir `config/settings_env.py`)
- Sessions Django pour le web

## 🧪 Tests
```bash
make test
make coverage
```

## Licence
Ce projet est sous licence MIT. Voir `LICENSE`.
