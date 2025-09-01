#!/usr/bin/env python3
"""
Script de lancement rapide pour le développement local
Usage: python run_local.py
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def run_command(command, description):
    """Exécuter une commande et afficher le résultat"""
    print(f"\n🔄 {description}...")
    print(f"Commande: {command}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} terminé avec succès")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de {description}")
        print(f"Erreur: {e.stderr}")
        return False

def check_dependencies():
    """Vérifier les dépendances système"""
    print("🔍 Vérification des dépendances...")
    
    # Vérifier Python
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 11):
        print("❌ Python 3.11+ requis")
        return False
    
    print(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # Vérifier pip
    try:
        import pip
        print("✅ pip disponible")
    except ImportError:
        print("❌ pip non disponible")
        return False
    
    return True

def setup_virtual_environment():
    """Créer et activer l'environnement virtuel"""
    venv_path = Path("venv")
    
    if not venv_path.exists():
        print("🔧 Création de l'environnement virtuel...")
        if not run_command("python -m venv venv", "Création de l'environnement virtuel"):
            return False
    
    # Activer l'environnement virtuel
    if os.name == 'nt':  # Windows
        activate_script = venv_path / "Scripts" / "activate"
        os.environ['VIRTUAL_ENV'] = str(venv_path)
        os.environ['PATH'] = f"{venv_path / 'Scripts'};{os.environ['PATH']}"
    else:  # Unix/Linux/Mac
        activate_script = venv_path / "bin" / "activate"
        os.environ['VIRTUAL_ENV'] = str(venv_path)
        os.environ['PATH'] = f"{venv_path / 'bin'}:{os.environ['PATH']}"
    
    print("✅ Environnement virtuel configuré")
    return True

def install_dependencies():
    """Installer les dépendances Python"""
    print("📦 Installation des dépendances...")
    
    # Mettre à jour pip
    if not run_command("python -m pip install --upgrade pip", "Mise à jour de pip"):
        return False
    
    # Installer les dépendances de développement
    if not run_command("pip install -r requirements-dev.txt", "Installation des dépendances"):
        return False
    
    return True

def setup_database():
    """Configurer la base de données"""
    print("🗄️ Configuration de la base de données...")
    
    # Créer le fichier .env s'il n'existe pas
    env_file = Path(".env")
    if not env_file.exists():
        env_example = Path("env.example")
        if env_example.exists():
            import shutil
            shutil.copy(env_example, env_file)
            print("✅ Fichier .env créé à partir de env.example")
        else:
            print("⚠️ Fichier env.example non trouvé, création manuelle du .env requis")
    
    # Vérifier que le fichier .env existe
    if not env_file.exists():
        print("❌ Fichier .env manquant. Veuillez le créer manuellement.")
        return False
    
    return True

def run_migrations():
    """Exécuter les migrations Django"""
    print("🔄 Exécution des migrations...")
    
    if not run_command("python manage.py makemigrations", "Création des migrations"):
        return False
    
    if not run_command("python manage.py migrate", "Application des migrations"):
        return False
    
    return True

def create_superuser():
    """Créer un super utilisateur"""
    print("👤 Création du super utilisateur...")
    
    # Vérifier si un super utilisateur existe déjà
    try:
        result = subprocess.run(
            "python manage.py shell -c \"from django.contrib.auth import get_user_model; User = get_user_model(); print('Super users:', User.objects.filter(is_superuser=True).count())\"",
            shell=True, capture_output=True, text=True
        )
        
        if "Super users: 0" in result.stdout:
            print("📝 Aucun super utilisateur trouvé, création d'un nouveau...")
            if not run_command("python manage.py createsuperuser --noinput --username admin --email admin@example.com", "Création du super utilisateur"):
                print("⚠️ Échec de la création automatique. Créez manuellement avec: python manage.py createsuperuser")
        else:
            print("✅ Super utilisateur déjà existant")
    except:
        print("⚠️ Impossible de vérifier les super utilisateurs")
    
    return True

def load_demo_data():
    """Charger les données de démonstration"""
    print("📊 Chargement des données de démonstration...")
    
    fixtures_file = Path("fixtures/demo_data.json")
    if fixtures_file.exists():
        if not run_command("python manage.py loaddata fixtures/demo_data.json", "Chargement des données de démonstration"):
            print("⚠️ Échec du chargement des données de démonstration")
    else:
        print("⚠️ Fichier de données de démonstration non trouvé")
    
    return True

def collect_static():
    """Collecter les fichiers statiques"""
    print("📁 Collecte des fichiers statiques...")
    
    if not run_command("python manage.py collectstatic --noinput", "Collecte des fichiers statiques"):
        return False
    
    return True

def start_development_server():
    """Démarrer le serveur de développement"""
    print("\n🚀 Démarrage du serveur de développement...")
    print("📍 L'application sera accessible à: http://127.0.0.1:8000")
    print("🔑 Connectez-vous avec l'utilisateur créé précédemment")
    print("⏹️  Appuyez sur Ctrl+C pour arrêter le serveur")
    print("\n" + "="*60)
    
    try:
        subprocess.run("python manage.py runserver", shell=True, check=True)
    except KeyboardInterrupt:
        print("\n\n👋 Serveur arrêté par l'utilisateur")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Erreur lors du démarrage du serveur: {e}")

def main():
    """Fonction principale"""
    print("🎯 CRM Maroc - Script de lancement rapide")
    print("="*60)
    
    # Vérifier les dépendances
    if not check_dependencies():
        sys.exit(1)
    
    # Configuration de l'environnement
    if not setup_virtual_environment():
        sys.exit(1)
    
    # Installation des dépendances
    if not install_dependencies():
        sys.exit(1)
    
    # Configuration de la base de données
    if not setup_database():
        print("\n⚠️ Configuration manuelle requise:")
        print("1. Créez un fichier .env basé sur env.example")
        print("2. Configurez votre base de données PostgreSQL")
        print("3. Relancez ce script")
        sys.exit(1)
    
    # Migrations
    if not run_migrations():
        sys.exit(1)
    
    # Super utilisateur
    create_superuser()
    
    # Données de démonstration
    load_demo_data()
    
    # Fichiers statiques
    if not collect_static():
        sys.exit(1)
    
    # Démarrer le serveur
    start_development_server()

if __name__ == "__main__":
    main()
