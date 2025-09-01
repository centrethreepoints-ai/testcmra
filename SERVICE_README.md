# CRM Maroc Service Management

Ce document explique comment gérer le service CRM Maroc en tant que service systemd sur votre système Linux.

## 📁 Fichiers de service

- **`crm-maroc.service`** - Service simple avec Django runserver (développement)
- **`crm-maroc-gunicorn.service`** - Service avec Gunicorn (production)
- **`crm-service.sh`** - Script de gestion complet avec toutes les fonctionnalités
- **`crmctl`** - Script de gestion simplifié pour les opérations courantes
- **`gunicorn.conf.py`** - Configuration Gunicorn pour la production

## 🚀 Installation du service

### 1. Installation initiale

```bash
# Installer le service (requiert sudo)
sudo ./crm-service.sh install

# Vérifier l'installation
./crm-service.sh status
```

### 2. Démarrer le service

```bash
# Démarrer le service
sudo ./crm-service.sh start

# Ou utiliser le script simplifié
./crmctl start
```

### 3. Vérifier le statut

```bash
# Voir le statut complet
./crm-service.sh status

# Ou version simplifiée
./crmctl status
```

## ⚙️ Commandes disponibles

### Script complet (`crm-service.sh`)

```bash
sudo ./crm-service.sh install      # Installer le service
sudo ./crm-service.sh uninstall    # Désinstaller le service
sudo ./crm-service.sh start        # Démarrer le service
sudo ./crm-service.sh stop         # Arrêter le service
sudo ./crm-service.sh restart      # Redémarrer le service
sudo ./crm-service.sh reload       # Recharger la configuration
./crm-service.sh status            # Voir le statut
./crm-service.sh logs              # Voir les logs en temps réel
./crm-service.sh help              # Afficher l'aide
```

### Script simplifié (`crmctl`)

```bash
./crmctl start                     # Démarrer le service
./crmctl stop                      # Arrêter le service
./crmctl restart                   # Redémarrer le service
./crmctl status                    # Voir le statut
./crmctl help                      # Afficher l'aide
```

## 🔧 Gestion systemd directe

Une fois le service installé, vous pouvez aussi utiliser les commandes systemd standard :

```bash
# Démarrer
sudo systemctl start crm-maroc

# Arrêter
sudo systemctl stop crm-maroc

# Redémarrer
sudo systemctl restart crm-maroc

# Voir le statut
sudo systemctl status crm-maroc

# Voir les logs
sudo journalctl -u crm-maroc -f

# Activer au démarrage
sudo systemctl enable crm-maroc

# Désactiver au démarrage
sudo systemctl disable crm-maroc
```

## 📊 Vérification du service

### 1. Statut du service

```bash
./crmctl status
```

Cela affichera :
- Le statut systemd du service
- Si le port 8000 écoute
- Les informations du processus

### 2. Logs en temps réel

```bash
./crm-service.sh logs
```

### 3. Vérification manuelle

```bash
# Vérifier si le port écoute
netstat -tlnp | grep :8000

# Vérifier les processus Django
ps aux | grep "runserver\|gunicorn"

# Vérifier les logs systemd
sudo journalctl -u crm-maroc --no-pager -l
```

## 🌐 Accès à l'application

Une fois le service démarré, vous pouvez accéder à votre application :

- **URL locale** : http://localhost:8000
- **URL réseau** : http://VOTRE_IP:8000
- **URL VM** : http://10.10.10.15:8000

## 🔒 Sécurité

Le service est configuré avec des paramètres de sécurité :

- Exécution sous l'utilisateur `master`
- Répertoire de travail restreint à `/opt/app`
- Protection du système activée
- Pas de nouveaux privilèges

## 🚨 Dépannage

### Service ne démarre pas

```bash
# Vérifier les logs d'erreur
sudo journalctl -u crm-maroc --no-pager -l

# Vérifier la configuration
sudo systemctl status crm-maroc --no-pager -l

# Vérifier les permissions
ls -la /etc/systemd/system/crm-maroc.service
```

### Port déjà utilisé

```bash
# Vérifier ce qui utilise le port 8000
sudo netstat -tlnp | grep :8000

# Tuer le processus si nécessaire
sudo pkill -f "runserver\|gunicorn"
```

### Problèmes de permissions

```bash
# Vérifier les permissions du répertoire
ls -la /opt/app/

# Vérifier l'utilisateur du service
sudo systemctl show crm-maroc | grep User
```

## 📝 Configuration avancée

### Utiliser Gunicorn (production)

1. Installer Gunicorn :
```bash
pip install gunicorn
```

2. Utiliser le service Gunicorn :
```bash
sudo cp crm-maroc-gunicorn.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable crm-maroc-gunicorn
sudo systemctl start crm-maroc-gunicorn
```

### Modifier la configuration

- **Port** : Modifier `bind` dans `gunicorn.conf.py`
- **Workers** : Modifier `workers` dans `gunicorn.conf.py`
- **Logs** : Modifier les chemins dans `gunicorn.conf.py`

## 🔄 Mise à jour du service

Après avoir modifié le code ou la configuration :

```bash
# Redémarrer le service
./crmctl restart

# Ou recharger la configuration
sudo ./crm-service.sh reload
```

## 📋 Checklist d'installation

- [ ] Service installé avec `sudo ./crm-service.sh install`
- [ ] Service démarré avec `./crmctl start`
- [ ] Statut vérifié avec `./crmctl status`
- [ ] Application accessible sur http://VOTRE_IP:8000
- [ ] Service configuré pour démarrer automatiquement

## 🆘 Support

En cas de problème :

1. Vérifiez les logs : `./crm-service.sh logs`
2. Vérifiez le statut : `./crmctl status`
3. Redémarrez le service : `./crmctl restart`
4. Réinstallez le service : `sudo ./crm-service.sh uninstall && sudo ./crm-service.sh install`
