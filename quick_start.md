# 🚀 Guide de démarrage rapide - CRM Maroc

## 📋 Prérequis

- Python 3.11+
- pip
- Git

## 🎯 Installation rapide

### 1. Cloner le projet
```bash
git clone <url-du-repo>
cd crm_maroc
```

### 2. Créer l'environnement virtuel
```bash
python -m venv venv

# Activer l'environnement virtuel
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Installer les dépendances
```bash
# Installation complète (développement)
pip install -r requirements-dev.txt

# Ou installation minimale (production)
pip install -r requirements.txt
```

## 🗄️ Configuration de la base de données

### Option A : SQLite (développement rapide)
```bash
# Utiliser la configuration par défaut
export DJANGO_SETTINGS_MODULE=config.settings_local
```

### Option B : PostgreSQL (recommandé)
```bash
# Installer PostgreSQL
# Ubuntu/Debian
sudo apt-get install postgresql postgresql-contrib

# macOS
brew install postgresql

# Windows
# Télécharger depuis https://www.postgresql.org/download/windows/

# Créer la base de données
sudo -u postgres psql
CREATE DATABASE crm_maroc_dev;
CREATE USER crm_user WITH PASSWORD 'crm_password';
GRANT ALL PRIVILEGES ON DATABASE crm_maroc_dev TO crm_user;
\q

# Utiliser la configuration PostgreSQL
export DJANGO_SETTINGS_MODULE=config.settings_dev
```

## 🔧 Configuration de l'environnement

### 1. Créer le fichier .env
```bash
cp env.example .env
```

### 2. Éditer .env
```bash
# Configuration de base
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1

# Base de données SQLite (par défaut)
DATABASE_URL=sqlite:///db.sqlite3

# Ou PostgreSQL
DB_NAME=crm_maroc_dev
DB_USER=crm_user
DB_PASSWORD=crm_password
DB_HOST=localhost
DB_PORT=5432

# Redis (optionnel pour le développement)
REDIS_URL=redis://localhost:6379/0
```

## 🚀 Lancement du projet

### Méthode 1 : Script automatique (recommandé)
```bash
python run_local.py
```

### Méthode 2 : Commandes manuelles

#### 1. Créer les migrations
```bash
python manage.py makemigrations
```

#### 2. Appliquer les migrations
```bash
python manage.py migrate
```

#### 3. Créer un super utilisateur
```bash
python manage.py createsuperuser
```

#### 4. Charger les données de démonstration
```bash
python manage.py loaddata fixtures/demo_data.json
```

#### 5. Collecter les fichiers statiques
```bash
python manage.py collectstatic --noinput
```

#### 6. Démarrer le serveur
```bash
python manage.py runserver
```

## 🌐 Accès à l'application

- **Interface web** : http://127.0.0.1:8000
- **Admin Django** : http://127.0.0.1:8000/admin
- **API REST** : http://127.0.0.1:8000/api/v1/

## 🧪 Tests

### Lancer tous les tests
```bash
python -m pytest
```

### Tests avec couverture
```bash
python -m pytest --cov=. --cov-report=html
```

### Tests d'une application spécifique
```bash
python -m pytest core/
python -m pytest users/
python -m pytest billing/
```

## 🔧 Commandes Django utiles

### Gestion des migrations
```bash
# Créer des migrations
python manage.py makemigrations [app_name]

# Appliquer les migrations
python manage.py migrate

# Voir le statut des migrations
python manage.py showmigrations

# Annuler la dernière migration
python manage.py migrate [app_name] [previous_migration]
```

### Shell Django
```bash
# Shell standard
python manage.py shell

# Shell avec extensions (django-extensions)
python manage.py shell_plus
```

### Gestion des utilisateurs
```bash
# Créer un super utilisateur
python manage.py createsuperuser

# Changer un mot de passe
python manage.py changepassword [username]
```

### Gestion des données
```bash
# Charger des données
python manage.py loaddata [fixture_name]

# Exporter des données
python manage.py dumpdata [app_name] > [filename].json

# Vider la base de données
python manage.py flush
```

### Gestion des fichiers statiques
```bash
# Collecter les fichiers statiques
python manage.py collectstatic

# Trouver les fichiers statiques
python manage.py findstatic [filename]
```

### Gestion des applications
```bash
# Vérifier la configuration
python manage.py check

# Valider les modèles
python manage.py validate

# Lister les applications installées
python manage.py check --list-tags
```

## 🐳 Développement avec Docker

### Démarrer tous les services
```bash
make up
```

### Voir les logs
```bash
make logs
```

### Arrêter les services
```bash
make down
```

### Reconstruire les images
```bash
make build
```

## 🔍 Débogage

### Debug Toolbar
Le Debug Toolbar est automatiquement activé en mode développement.

### Logs
```bash
# Voir les logs en temps réel
tail -f logs/django.log

# Ou avec le serveur de développement
python manage.py runserver --verbosity=2
```

### Base de données
```bash
# Ouvrir un shell PostgreSQL
psql -U crm_user -d crm_maroc_dev

# Voir les tables
\dt

# Voir la structure d'une table
\d [table_name]
```

## 📊 Données de démonstration

Le projet inclut des données d'exemple :
- **Société** : "Top3 SARL"
- **Utilisateurs** : admin, comptable, vendeur
- **Clients** : 5 clients d'exemple
- **Fournisseurs** : 5 fournisseurs d'exemple
- **Produits** : 10 produits/services
- **Taux TVA** : 20%, 10%, 7%, 0%

## 🚨 Dépannage courant

### Erreur de migration
```bash
# Réinitialiser la base de données
python manage.py flush
python manage.py migrate --run-syncdb
```

### Erreur de dépendances
```bash
# Mettre à jour pip
pip install --upgrade pip

# Réinstaller les dépendances
pip install -r requirements.txt --force-reinstall
```

### Erreur de base de données
```bash
# Vérifier la connexion
python manage.py dbshell

# Vérifier les migrations
python manage.py showmigrations
```

### Erreur de fichiers statiques
```bash
# Nettoyer et recréer
rm -rf staticfiles/
python manage.py collectstatic --noinput
```

## 📚 Ressources utiles

- [Documentation Django](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [HTMX](https://htmx.org/)
- [Bootstrap 5](https://getbootstrap.com/)

## 🆘 Support

- **Issues** : Utiliser les issues GitHub
- **Documentation** : Ce guide et le README principal
- **Email** : support@crm-maroc.com

---

**Bon développement ! 🚀**
