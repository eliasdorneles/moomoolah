.DEFAULT_GOAL := help

.PHONY: test
test:  ## Run all tests
	uv run pytest tests/ -v

.PHONY: lint
lint: format  ## Format code and run linter auto-fixing issues
	uv run ruff check --fix

.PHONY: format
format:
	uv run ruff format

.PHONY: check
check: lint test  ## Run linter and tests

.PHONY: run
run:  ## Run the application (usage: make run STATE_FILE=path/to/state.json)
	@if [ -z "$(STATE_FILE)" ]; then \
		echo "Usage: make run STATE_FILE=path/to/state.json"; \
		exit 1; \
	fi
	uv run python -m moomoolah $(STATE_FILE)

.PHONY: clean
clean:  ## Clean up temporary files and caches
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete

.PHONY: install
install:  ## Install dependencies
	uv sync

# Implements this pattern for autodocumenting Makefiles:
# https://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
#
# Picks up all comments that start with a ## and are at the end of a target definition line.
.PHONY: help
help:  ## Display command usage
	@grep -E '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
