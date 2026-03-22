"""Application configuration for BookRover.

All settings are read from environment variables or a .env file.
Never hardcode values — use this module as the single source of truth
for all configuration across the application.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed configuration loaded from environment variables.

    Attributes:
        app_env: Deployment environment — 'dev' or 'prod'. Controls table names.
        dynamodb_region: AWS region for DynamoDB. Defaults to ap-south-1 (Mumbai).
        dynamodb_endpoint_url: Optional local endpoint (moto_server). None in production.
        table_prefix: Prefix for all DynamoDB table names. Always 'bookrover'.
        cors_allowed_origins: List of allowed CORS origins. Restrict to CloudFront URL in prod.
    """

    app_env: str = "dev"
    dynamodb_region: str = "ap-south-1"
    dynamodb_endpoint_url: str | None = None
    table_prefix: str = "bookrover"
    cors_allowed_origins: list[str] = ["*"]
    admin_emails: list[str] = []

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    def get_table_name(self, entity: str) -> str:
        """Return the fully qualified DynamoDB table name for the given entity.

        Args:
            entity: Entity name segment (e.g., 'bookstores', 'sellers', 'inventory').

        Returns:
            Table name in the format '{prefix}-{entity}-{env}'.
            Example: 'bookrover-bookstores-dev'
        """
        return f"{self.table_prefix}-{entity}-{self.app_env}"
