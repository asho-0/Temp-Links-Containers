COMPOSE = docker compose

.PHONY: up build down shell logs dev

build:
	$(COMPOSE) build
dev:
	$(COMPOSE) up -d db
	$(COMPOSE) up -d temp_secret_links worker beat
	$(COMPOSE) exec temp_secret_links python3 -m app.cli create
	$(COMPOSE) exec temp_secret_links python3 -m app.cli migration
	$(COMPOSE) logs -f temp_secret_links
down:
	$(COMPOSE) down
clean:
	$(COMPOSE) down -v