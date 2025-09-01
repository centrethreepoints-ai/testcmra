.PHONY: help up down build logs shell migrate superuser test coverage fmt lint clean

help: ## Afficher cette aide
	@echo "Commandes disponibles:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

up: ## Démarrer tous les services
	docker-compose up -d

down: ## Arrêter tous les services
	docker-compose down

build: ## Reconstruire les images Docker
	docker-compose build --no-cache

logs: ## Afficher les logs de tous les services
	docker-compose logs -f

logs-web: ## Afficher les logs du service web
	docker-compose logs -f web

logs-worker: ## Afficher les logs du worker Celery
	docker-compose logs -f worker

shell: ## Ouvrir un shell dans le conteneur web
	docker-compose exec web bash

shell-db: ## Ouvrir un shell PostgreSQL
	docker-compose exec db psql -U crm_user -d crm_maroc

migrate: ## Appliquer les migrations
	docker-compose exec web python manage.py migrate

makemigrations: ## Créer de nouvelles migrations
	docker-compose exec web python manage.py makemigrations

superuser: ## Créer un super utilisateur
	docker-compose exec web python manage.py createsuperuser

collectstatic: ## Collecter les fichiers statiques
	docker-compose exec web python manage.py collectstatic --noinput

test: ## Lancer les tests
	docker-compose exec web python -m pytest

test-coverage: ## Lancer les tests avec couverture
	docker-compose exec web python -m pytest --cov=. --cov-report=html

coverage: ## Afficher le rapport de couverture
	docker-compose exec web coverage report

fmt: ## Formater le code avec black et isort
	docker-compose exec web black .
	docker-compose exec web isort .

lint: ## Vérifier le code avec flake8
	docker-compose exec web flake8 .

clean: ## Nettoyer les conteneurs et volumes
	docker-compose down -v
	docker system prune -f

restart: ## Redémarrer les services
	docker-compose restart

status: ## Afficher le statut des services
	docker-compose ps

seed: ## Charger les données de démonstration
	docker-compose exec web python manage.py loaddata fixtures/demo_data.json

reset-db: ## Réinitialiser la base de données
	docker-compose down -v
	docker-compose up -d db
	sleep 10
	docker-compose exec db psql -U crm_user -d postgres -c "DROP DATABASE IF EXISTS crm_maroc;"
	docker-compose exec db psql -U crm_user -d postgres -c "CREATE DATABASE crm_maroc;"
	make migrate
	make seed
	make superuser
