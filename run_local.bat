@echo off
chcp 65001 >nul
echo 🎯 CRM Maroc - Script de lancement rapide Windows
echo ================================================

REM Vérifier si Python est installé
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python n'est pas installé ou n'est pas dans le PATH
    echo Veuillez installer Python 3.11+ depuis https://python.org
    pause
    exit /b 1
)

echo ✅ Python détecté

REM Vérifier si l'environnement virtuel existe
if not exist "venv" (
    echo 🔧 Création de l'environnement virtuel...
    python -m venv venv
    if errorlevel 1 (
        echo ❌ Erreur lors de la création de l'environnement virtuel
        pause
        exit /b 1
    )
)

REM Activer l'environnement virtuel
echo 🔄 Activation de l'environnement virtuel...
call venv\Scripts\activate.bat

REM Mettre à jour pip
echo 📦 Mise à jour de pip...
python -m pip install --upgrade pip

REM Installer les dépendances
echo 📦 Installation des dépendances...
pip install -r requirements-dev.txt
if errorlevel 1 (
    echo ❌ Erreur lors de l'installation des dépendances
    pause
    exit /b 1
)

REM Créer le fichier .env s'il n'existe pas
if not exist ".env" (
    if exist "env.example" (
        echo 📝 Création du fichier .env...
        copy env.example .env >nul
    ) else (
        echo ⚠️ Fichier env.example non trouvé
        echo Veuillez créer manuellement le fichier .env
        pause
        exit /b 1
    )
)

REM Créer les migrations
echo 🔄 Création des migrations...
python manage.py makemigrations
if errorlevel 1 (
    echo ❌ Erreur lors de la création des migrations
    pause
    exit /b 1
)

REM Appliquer les migrations
echo 🔄 Application des migrations...
python manage.py migrate
if errorlevel 1 (
    echo ❌ Erreur lors de l'application des migrations
    pause
    exit /b 1
)

REM Créer un super utilisateur
echo 👤 Création du super utilisateur...
python manage.py createsuperuser --noinput --username admin --email admin@example.com 2>nul
if errorlevel 1 (
    echo ⚠️ Impossible de créer le super utilisateur automatiquement
    echo Créez-le manuellement avec: python manage.py createsuperuser
)

REM Charger les données de démonstration
echo 📊 Chargement des données de démonstration...
if exist "fixtures\demo_data.json" (
    python manage.py loaddata fixtures\demo_data.json
) else (
    echo ⚠️ Fichier de données de démonstration non trouvé
)

REM Collecter les fichiers statiques
echo 📁 Collecte des fichiers statiques...
python manage.py collectstatic --noinput

REM Démarrer le serveur
echo.
echo 🚀 Démarrage du serveur de développement...
echo 📍 L'application sera accessible à: http://127.0.0.1:8000
echo 🔑 Connectez-vous avec l'utilisateur créé précédemment
echo ⏹️  Appuyez sur Ctrl+C pour arrêter le serveur
echo.
echo ================================================

python manage.py runserver

pause
