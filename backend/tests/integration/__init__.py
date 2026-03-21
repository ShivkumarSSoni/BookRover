"""Integration tests for BookRover backend.

Pattern: wire real service + real repository together, with DynamoDB
mocked via moto (using the dynamodb_tables fixture from conftest.py).
Uses FastAPI TestClient with get_dynamodb_resource overridden to return
the moto-backed resource. No real AWS calls are ever made.
"""
