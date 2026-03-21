.PHONY: run test lint format coverage

run:
	uvicorn bookrover.main:app --reload --port 8000

test:
	pytest tests/ -v

coverage:
	pytest tests/ --cov=bookrover --cov-report=term-missing

lint:
	ruff check bookrover/ tests/

format:
	black bookrover/ tests/
