# Shortcuts. Run `make help` to list them.

.PHONY: help up down reset logs ps test

help:  ## Show this list
	@grep -E '^[a-z]+:.*##' Makefile | sed 's/:.*## /\t/'

up:  ## Build and start everything in the background
	docker compose up --build -d

down:  ## Stop everything (data is kept)
	docker compose down

reset:  ## Stop everything and delete all data
	docker compose down --volumes

logs:  ## Follow the backend's logs
	docker compose logs -f backend

ps:  ## Show the state of every service
	docker compose ps

test:  ## Run the backend tests (needs: pip install -r backend/requirements-dev.txt)
	cd backend && python -m pytest -q
