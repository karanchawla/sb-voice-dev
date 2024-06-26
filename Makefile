install: ## Install the poetry environment
	@echo "🚀 Creating virtual environment using pyenv and poetry"
	@poetry install	
	@poetry shell

format: ## Format code using isort and black.
	@echo "🚀 Formatting code: Running isort and black"
	@isort .
	@black .

check: ## Check code formatting using isort, black, flake8 and mypy.
	@echo "🚀 Checking code formatting: Running isort"
	@isort --check-only --diff .
	@echo "🚀 Checking code formatting: Running black"
	@black --check .
	@echo "🚀 Checking code formatting: Running flake8"
	@flake8 .
	@echo "🚀 Checking code formatting: Running mypy"
	@mypy .

build: clean-build ## Build wheel file using poetry
	@echo "🚀 Creating wheel file"
	@poetry build

clean-build: ## clean build artifacts
	@rm -rf dist

.PHONY: help

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
