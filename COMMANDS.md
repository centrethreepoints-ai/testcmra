# 🚀 Commandes de lancement - CRM Maroc

## 📋 Installation et configuration

### 1. **Installation rapide (recommandé)**
```bash
# Script automatique Python (toutes plateformes)
python run_local.py

# Script Windows
run_local.bat

# Script Linux/Mac
./run_local.sh
```

### 2. **Installation manuelle**
```bash
# Créer l'environnement virtuel
python -m venv venv

# Activer l'environnement virtuel
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# Installer les dépendances
pip install -r requirements-dev.txt

# Créer le fichier .env
cp env.example .env
```

## 🗄️ Configuration de la base de données

### **Option A : SQLite (développement rapide)**
```bash
export DJANGO_SETTINGS_MODULE=config.settings_sqlite
# ou
set DJANGO_SETTINGS_MODULE=config.settings_sqlite  # Windows
```

### **Option B : PostgreSQL (recommandé)**
```bash
export DJANGO_SETTINGS_MODULE=config.settings_dev
# ou
set DJANGO_SETTINGS_MODULE=config.settings_dev  # Windows
```

### **Option C : Variables d'environnement**
```bash
export DJANGO_SETTINGS_MODULE=config.settings_env
# ou
set DJANGO_SETTINGS_MODULE=config.settings_env  # Windows
```

## 🔧 Commandes Django principales

### **Gestion des migrations**
```bash
# Créer les migrations
python manage.py makemigrations

# Appliquer les migrations
python manage.py migrate

# Voir le statut des migrations
python manage.py showmigrations

# Créer des migrations pour une app spécifique
python manage.py makemigrations users
python manage.py makemigrations billing
```

### **Gestion des utilisateurs**
```bash
# Créer un super utilisateur
python manage.py createsuperuser

# Changer un mot de passe
python manage.py changepassword admin

# Créer un utilisateur via shell
python manage.py shell
```

### **Gestion des données**
```bash
# Charger les données de démonstration
python manage.py loaddata fixtures/demo_data.json

# Exporter des données
python manage.py dumpdata users > users_data.json
python manage.py dumpdata billing > billing_data.json

# Vider la base de données
python manage.py flush
```

### **Fichiers statiques**
```bash
# Collecter les fichiers statiques
python manage.py collectstatic --noinput

# Trouver un fichier statique
python manage.py findstatic bootstrap.min.css
```

### **Vérification et validation**
```bash
# Vérifier la configuration
python manage.py check

# Valider les modèles
python manage.py validate

# Lister les applications installées
python manage.py check --list-tags
```

## 🚀 Lancement du serveur

### **Serveur de développement**
```bash
# Port par défaut (8000)
python manage.py runserver

# Port personnalisé
python manage.py runserver 8080

# Interface réseau
python manage.py runserver 0.0.0.0:8000

# Mode verbeux
python manage.py runserver --verbosity=2
```

### **Serveur de production**
```bash
# Gunicorn
gunicorn config.wsgi:application --bind 0.0.0.0:8000

# Avec workers
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers=4
```

## 🧪 Tests

### **Lancer les tests**
```bash
# Tous les tests
python -m pytest

# Tests avec couverture
python -m pytest --cov=. --cov-report=html

# Tests d'une application
python -m pytest core/
python -m pytest users/
python -m pytest billing/

# Tests avec marqueurs
python -m pytest -m "not slow"
python -m pytest -m integration
```

### **Tests Django**
```bash
# Tests Django standard
python manage.py test

# Tests d'une app spécifique
python manage.py test users
python manage.py test billing

# Tests avec couverture
coverage run --source='.' manage.py test
coverage report
coverage html
```

## 🔍 Débogage et développement

### **Shell Django**
```bash
# Shell standard
python manage.py shell

# Shell avec extensions
python manage.py shell_plus

# Shell avec imports automatiques
python manage.py shell_plus --notebook
```

### **Debug Toolbar**
```bash
# Le Debug Toolbar est automatiquement activé en mode DEBUG
# Accédez à n'importe quelle page pour voir la barre de débogage
```

### **Logs**
```bash
# Voir les logs en temps réel
tail -f logs/django.log

# Logs avec le serveur
python manage.py runserver --verbosity=2
```

## 🐳 Docker

### **Services Docker**
```bash
# Démarrer tous les services
make up
# ou
docker-compose up -d

# Voir les logs
make logs
# ou
docker-compose logs -f

# Arrêter les services
make down
# ou
docker-compose down

# Reconstruire
make build
# ou
docker-compose build --no-cache
```

### **Commandes Docker individuelles**
```bash
# Base de données
docker-compose exec db psql -U crm_user -d crm_maroc

# Redis
docker-compose exec redis redis-cli

# Shell Django
docker-compose exec web python manage.py shell

# Migrations
docker-compose exec web python manage.py migrate
```

## 📊 Gestion des données

### **Fixtures**
```bash
# Créer des fixtures
python manage.py dumpdata --indent=2 users.User > fixtures/users.json
python manage.py dumpdata --indent=2 companies.Company > fixtures/companies.json

# Charger des fixtures
python manage.py loaddata fixtures/users.json
python manage.py loaddata fixtures/companies.json
```

### **Import/Export**
```bash
# Exporter des données
python manage.py export_users --format=csv --output=users.csv

# Importer des données
python manage.py import_users --file=users.csv
```

## 🔧 Maintenance

### **Nettoyage**
```bash
# Nettoyer les fichiers temporaires
python manage.py clearsessions
python manage.py clear_cache

# Nettoyer les migrations
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
find . -path "*/migrations/*.pyc" -delete
```

### **Mise à jour**
```bash
# Mettre à jour les dépendances
pip install -r requirements.txt --upgrade

# Mettre à jour Django
pip install --upgrade Django

# Vérifier les vulnérabilités
safety check
```

## 📚 Commandes utiles

### **Gestion des apps**
```bash
# Créer une nouvelle app
python manage.py startapp newapp

# Lister les apps installées
python manage.py check --list-tags
```

### **Base de données**
```bash
# Shell de base de données
python manage.py dbshell

# Vider la base
python manage.py flush

# Créer une sauvegarde
python manage.py dumpdata > backup.json
```

### **Fichiers**
```bash
# Collecter les statiques
python manage.py collectstatic --noinput --clear

# Trouver un template
python manage.py findstatic base.html
```

## 🆘 Dépannage

### **Erreurs courantes**
```bash
# Erreur de migration
python manage.py migrate --run-syncdb

# Erreur de dépendances
pip install -r requirements.txt --force-reinstall

# Erreur de base de données
python manage.py dbshell

# Erreur de fichiers statiques
rm -rf staticfiles/
python manage.py collectstatic --noinput
```

### **Vérifications**
```bash
# Vérifier la configuration
python manage.py check --deploy

# Vérifier les modèles
python manage.py validate

# Vérifier les URLs
python manage.py check --list-tags
```

---

## 🎯 **Résumé des commandes essentielles**

```bash
# 1. Installation
python run_local.py

# 2. Configuration
export DJANGO_SETTINGS_MODULE=config.settings_sqlite

# 3. Base de données
python manage.py makemigrations
python manage.py migrate

# 4. Super utilisateur
python manage.py createsuperuser

# 5. Données de démonstration
python manage.py loaddata fixtures/demo_data.json

# 6. Fichiers statiques
python manage.py collectstatic --noinput

# 7. Lancement
python manage.py runserver
```

**L'application sera accessible à : http://127.0.0.1:8000**
