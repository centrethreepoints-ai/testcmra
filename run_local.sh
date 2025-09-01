#!/bin/bash

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🎯 CRM Maroc - Script de lancement rapide${NC}"
echo "================================================"

# Vérifier si Python est installé
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 n'est pas installé${NC}"
    echo "Veuillez installer Python 3.11+"
    exit 1
fi

# Vérifier la version de Python
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 11 ]); then
    echo -e "${RED}❌ Python 3.11+ requis (version actuelle: $PYTHON_VERSION)${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Python $PYTHON_VERSION détecté${NC}"

# Vérifier si l'environnement virtuel existe
if [ ! -d "venv" ]; then
    echo -e "${BLUE}🔧 Création de l'environnement virtuel...${NC}"
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Erreur lors de la création de l'environnement virtuel${NC}"
        exit 1
    fi
fi

# Activer l'environnement virtuel
echo -e "${BLUE}🔄 Activation de l'environnement virtuel...${NC}"
source venv/bin/activate

# Mettre à jour pip
echo -e "${BLUE}📦 Mise à jour de pip...${NC}"
python -m pip install --upgrade pip

# Installer les dépendances
echo -e "${BLUE}📦 Installation des dépendances...${NC}"
pip install -r requirements-dev.txt
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Erreur lors de l'installation des dépendances${NC}"
    exit 1
fi

# Créer le fichier .env s'il n'existe pas
if [ ! -f ".env" ]; then
    if [ -f "env.example" ]; then
        echo -e "${BLUE}📝 Création du fichier .env...${NC}"
        cp env.example .env
    else
        echo -e "${YELLOW}⚠️ Fichier env.example non trouvé${NC}"
        echo "Veuillez créer manuellement le fichier .env"
        exit 1
    fi
fi

# Créer le dossier logs s'il n'existe pas
mkdir -p logs

# Créer les migrations
echo -e "${BLUE}🔄 Création des migrations...${NC}"
python manage.py makemigrations
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Erreur lors de la création des migrations${NC}"
    exit 1
fi

# Appliquer les migrations
echo -e "${BLUE}🔄 Application des migrations...${NC}"
python manage.py migrate
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Erreur lors de l'application des migrations${NC}"
    exit 1
fi

# Créer un super utilisateur
echo -e "${BLUE}👤 Création du super utilisateur...${NC}"
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if User.objects.filter(is_superuser=True).count() == 0:
    User.objects.create_superuser('admin', 'admin@example.com', 'REDACTED')
    print('Super utilisateur créé: admin/REDACTED')
else:
    print('Super utilisateur déjà existant')
" 2>/dev/null

# Charger les données de démonstration
echo -e "${BLUE}📊 Chargement des données de démonstration...${NC}"
if [ -f "fixtures/demo_data.json" ]; then
    python manage.py loaddata fixtures/demo_data.json
else
    echo -e "${YELLOW}⚠️ Fichier de données de démonstration non trouvé${NC}"
fi

# Collecter les fichiers statiques
echo -e "${BLUE}📁 Collecte des fichiers statiques...${NC}"
python manage.py collectstatic --noinput

# Démarrer le serveur
echo
echo -e "${GREEN}🚀 Démarrage du serveur de développement...${NC}"
echo -e "${BLUE}📍 L'application sera accessible à: http://127.0.0.1:8000${NC}"
echo -e "${BLUE}🔑 Connectez-vous avec l'utilisateur créé précédemment${NC}"
echo -e "${YELLOW}⏹️  Appuyez sur Ctrl+C pour arrêter le serveur${NC}"
echo
echo "================================================"

# Démarrer le serveur
python manage.py runserver
