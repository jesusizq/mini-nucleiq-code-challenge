# Makefile for mini-nucleiq

SHELL := /bin/bash

IMAGE := mini-nucleiq
PORT ?= 8000

.PHONY: help install test lint format run smoke docker-build docker-run

help:
	@echo "mini-nucleiq - Development Commands"
	@echo "===================================="
	@echo ""
	@echo "Quick Start:"
	@echo "  make install && make test : Install deps and run the tests"
	@echo "  make run                  : Serve the API at http://localhost:$(PORT)"
	@echo ""
	@echo "Available Commands:"
	@echo "  install       : Install dependencies (incl. dev) and pre-commit hooks"
	@echo "  test          : Run the test suite (pytest)"
	@echo "  lint          : Lint (ruff) and type-check (mypy --strict)"
	@echo "  format        : Format the code (black)"
	@echo "  run           : Serve the API locally with autoreload"
	@echo "  smoke         : Curl the endpoints of a running service (happy path + errors)"
	@echo "  docker-build  : Build the production Docker image"
	@echo "  docker-run    : Run the image, mapping port $(PORT)"
	@echo ""
	@echo "Example:"
	@echo "  make docker-build && make docker-run"

install:
	@echo "Installing dependencies..."
	poetry install
	poetry run pre-commit install
	@echo "✓ Install completed"

test:
	poetry run pytest

lint:
	@echo "Linting (ruff) and type-checking (mypy)..."
	poetry run ruff check src tests
	poetry run mypy
	@echo "✓ Lint completed"

format:
	poetry run black src tests

run:
	poetry run uvicorn mini_nucleiq.api.app:app --reload --port $(PORT)

smoke:
	BASE_URL=http://localhost:$(PORT) python3 scripts/smoke.py

docker-build:
	@echo "Building image $(IMAGE)..."
	docker build -t $(IMAGE) .
	@echo "✓ Image built"

docker-run:
	docker run --rm -p $(PORT):8000 $(IMAGE)
