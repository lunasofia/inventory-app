VENV := .venv/bin

.PHONY: test run migrate makemigrations install-dev superuser

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
