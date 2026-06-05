# Makefile for SapiSehat Backend

.PHONY: help install test run docker-build docker-run docker-stop clean

help:
	@echo "SapiSehat Backend - Available Commands"
	@echo "======================================="
	@echo "make install          - Install dependencies"
	@echo "make test             - Run unit tests"
	@echo "make test-coverage    - Run tests with coverage report"
	@echo "make run              - Run FastAPI server locally"
	@echo "make run-debug        - Run with debug logging"
	@echo "make docker-build     - Build Docker image"
	@echo "make docker-run       - Start Docker container"
	@echo "make docker-stop      - Stop Docker container"
	@echo "make docker-logs      - View container logs"
	@echo "make lint             - Run code linter (flake8)"
	@echo "make format           - Format code (black)"
	@echo "make clean            - Clean temporary files"

install:
	pip install -r requirements.txt

test:
	python -m pytest tests/ -v

test-coverage:
	pytest --cov=. tests/ --cov-report=html
	@echo "Coverage report: htmlcov/index.html"

run:
	python main.py

run-debug:
	DEBUG=true LOG_LEVEL=debug python main.py

docker-build:
	docker-compose build

docker-run:
	docker-compose up

docker-run-detached:
	docker-compose up -d

docker-stop:
	docker-compose down

docker-logs:
	docker-compose logs -f backend

docker-clean:
	docker-compose down -v

lint:
	flake8 . --exclude=venv,tests

format:
	black . --exclude=venv

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .coverage htmlcov
	rm -rf build dist *.egg-info

# Development shortcuts
dev-install: install
	pip install pytest pytest-cov black flake8

dev-test:
	python -m pytest tests/ -v --tb=short

dev-run:
	FASTAPI_ENV=development DEBUG=true LOG_LEVEL=debug python main.py
