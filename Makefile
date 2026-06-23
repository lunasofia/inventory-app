VENV := .venv/bin

# Cloud Run deployment target (override on the command line if these change).
CLOUD_RUN_SERVICE ?= packwell
CLOUD_RUN_REGION  ?= us-central1

.PHONY: test run migrate makemigrations install-dev superuser seed-demo deploy

test:           ## Run the test suite
	$(VENV)/pytest

run:            ## Start the local dev server
	$(VENV)/python manage.py runserver 8000

migrate:        ## Apply database migrations
	$(VENV)/python manage.py migrate

makemigrations: ## Create new migrations
	$(VENV)/python manage.py makemigrations

install-dev:    ## Install dev + test dependencies
	$(VENV)/pip install -r requirements-dev.txt

superuser:      ## Create a Django superuser
	$(VENV)/python manage.py createsuperuser

seed-demo:      ## Seed/rebuild the demo account (demo@packlist.app / demo12345)
	$(VENV)/python manage.py seed_demo

deploy: test    ## Run tests, then redeploy current code to Cloud Run (keeps DB/secrets/env)
	gcloud run deploy $(CLOUD_RUN_SERVICE) --source . --region=$(CLOUD_RUN_REGION)
	@echo "Deployed. First-time DB/secret/domain setup is in docs/DEPLOY.md (it persists across these deploys)."
