.PHONY: setup setup-backend lint format run test migrate env

setup: setup-backend
	cd backend && uv run pre-commit install

setup-backend:
	cd backend && uv sync

lint:  
	cd backend && uv run ruff check . --fix
	cd backend && uv run ruff format .

run:
	cd backend && uv run python manage.py runserver

test:
	cd backend && uv run python manage.py test