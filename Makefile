.PHONY: setup setup-backend lint format

setup: setup-backend
	cd backend && uv run pre-commit install

setup-backend:
	cd backend && uv sync

lint:  
	cd backend && uv run ruff check . --fix
	cd backend && uv run ruff format .
