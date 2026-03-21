"""Unit tests for BookRover service classes.

Pattern: instantiate the concrete service with a unittest.mock.MagicMock
that implements the repository ABC interface. Assert service behaviour
without touching DynamoDB or HTTP.
"""
