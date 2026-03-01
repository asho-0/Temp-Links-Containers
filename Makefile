COMPOSE = docker compose

.PHONY: up build down shell logs dev

build:
	$(COMPOSE) build
dev:
	$(COMPOSE) up -d db
	$(COMPOSE) up -d temp_secret_vault
	$(COMPOSE) exec temp_secret_vault python3 -m app.cli create
	$(COMPOSE) exec temp_secret_vault python3 -m app.cli migration
	$(COMPOSE) logs -f temp_secret_vault
down:
	$(COMPOSE) down
clean:
	$(COMPOSE) down -v