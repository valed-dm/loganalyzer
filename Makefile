.PHONY: format lint test renew-hooks install-hooks check

# Format code using Poetry-managed tools
format:
	poetry run ruff check . --fix
	poetry run black .
	@echo "✅ Formatting complete!"

# Lint only (no fixes)
lint:
	poetry run ruff check .
	poetry run black --check .
	@echo "✅ Linting passed!"

test:
	poetry run pytest -v --cov
	@echo "✅ Tests passed!"

check: lint test

renew-hooks:
	poetry run pre-commit uninstall
	poetry run pre-commit clean
	poetry run pre-commit autoupdate
	poetry run pre-commit install --hook-type pre-commit --hook-type pre-push
	poetry run pre-commit run --all-files
	@echo "✅ Hooks renewed!"

install-hooks:
	poetry install
	poetry run pre-commit install --hook-type pre-commit --hook-type pre-push
	poetry run pre-commit run --all-files
	@echo "✅ Setup complete!"