@echo off
docker compose exec db psql -U postgres -d courseteer
