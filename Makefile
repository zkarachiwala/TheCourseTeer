.PHONY: up down psql logs

# Start Postgres and Adminer in the background
up:
	docker compose up -d

# Stop and remove containers (data volume is preserved)
down:
	docker compose down

# Open a psql shell into the running database
psql:
	docker compose exec db psql -U $${POSTGRES_USER:-postgres} -d $${POSTGRES_DB:-courseteer}

# Tail logs from all services
logs:
	docker compose logs -f
