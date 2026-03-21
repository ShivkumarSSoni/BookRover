"""Unit tests for BookRover router handlers.

Pattern: use FastAPI TestClient with the real router, but override the
service Depends() with a unittest.mock.MagicMock that implements the
service ABC. No repository, no DynamoDB needed.
"""
