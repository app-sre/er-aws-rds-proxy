from collections.abc import Sequence
from typing import Self

from external_resources_io.input import AppInterfaceProvision
from pydantic import BaseModel, Field, model_validator


class Auth(BaseModel):
    """Authentication configuration for RDS Proxy.

    Defines how the proxy authenticates with the database, including
    authentication scheme, password types, and credential sources.
    """

    auth_scheme: str = Field(
        default="SECRETS",
        description="Type of authentication the proxy uses for connections from clients",
    )
    client_password_auth_type: str | None = Field(
        default=None,
        description="Type of authentication the proxy uses for connections to the database",
    )
    description: str | None = Field(
        default=None, description="Description of the authentication configuration"
    )
    iam_auth: str | None = Field(
        default=None,
        description="Whether to require or disallow IAM authentication for connections",
    )
    secret_name: str | None = Field(
        default=None,
        description="Name of the Secrets Manager secret containing database credentials",
    )
    username: str | None = Field(
        default=None,
        description="Username for authentication with the database",
    )

    @model_validator(mode="after")
    def set_iam_auth(self) -> Self:
        """Set default IAM authentication when using SECRETS auth scheme.

        Automatically sets iam_auth to "DISABLED" when auth_scheme is "SECRETS"
        and iam_auth is not explicitly provided.
        """
        if self.iam_auth is None and self.auth_scheme == "SECRETS":
            self.iam_auth = "DISABLED"

        return self

    @model_validator(mode="after")
    def is_secret_name_set(self) -> Self:
        """Validate that secret_name is provided when using SECRETS auth scheme.

        Raises:
            ValueError: If auth_scheme is "SECRETS" but secret_name is None.
        """
        if self.auth_scheme == "SECRETS" and self.secret_name is None:
            raise ValueError("secret_name must be set when auth_scheme is SECRETS")

        return self


class RdsProxyData(BaseModel):
    """Configuration data for AWS RDS Proxy infrastructure.

    Defines all parameters needed to create and configure an RDS Proxy,
    including authentication, networking, connection pooling, and IAM settings.
    """

    # app-interface
    region: str = Field(description="AWS region")
    identifier: str = Field(description="Name identifier for the proxy")
    output_resource_name: str | None = None
    tags: dict[str, str] = Field(description="Resource tags")

    auth: Sequence[Auth]
    connection_borrow_timeout: int | None = Field(
        default=None, description="Seconds to wait for connection availability"
    )
    db_instance_identifier: str = Field(description="Database instance identifier")
    debug_logging: bool = Field(
        default=False, description="Enable detailed SQL statement logging"
    )
    engine_family: str = Field(
        default="POSTGRESQL", description="Database engine family (MYSQL or POSTGRESQL)"
    )
    iam_role_force_detach_policies: bool = Field(
        default=True, description="Force detach policies before destroying IAM role"
    )
    iam_role_max_session_duration: int = Field(
        default=43200, description="Maximum session duration for IAM role (seconds)"
    )
    idle_client_timeout: int = Field(
        default=1800, description="Seconds before disconnecting idle connections"
    )
    init_query: str = Field(
        default="", description="SQL statements to run on new connections"
    )
    log_group_retention_in_days: int = Field(
        default=30, description="CloudWatch log retention period (days)"
    )
    max_connections_percent: int = Field(
        default=90, description="Maximum connection pool size percentage"
    )
    max_idle_connections_percent: int = Field(
        default=50, description="Maximum idle connections percentage"
    )
    require_tls: bool = Field(
        default=True, description="Require TLS encryption for connections"
    )
    session_pinning_filters: list[str] = Field(
        default=[], description="SQL operations that trigger session pinning"
    )
    vpc_security_group_ids: list[str] = Field(description="VPC security group IDs")
    vpc_subnet_ids: list[str] = Field(description="VPC subnet IDs")

    @model_validator(mode="after")
    def set_auth_defaults(self) -> Self:
        """Set default client password authentication types based on engine family.

        For each auth configuration, sets the client_password_auth_type based on
        the database engine family when not explicitly provided:
        - POSTGRES engine family: "POSTGRES_SCRAM_SHA_256"
        """
        for auth_item in self.auth:
            if (
                auth_item.client_password_auth_type is None
                and self.engine_family == "POSTGRESQL"
            ):
                auth_item.client_password_auth_type = "POSTGRES_SCRAM_SHA_256"  # noqa: S105
        return self


class AppInterfaceInput(BaseModel):
    """Input model for AWS RDS Proxy app-interface integration.

    Combines RDS Proxy configuration data with provisioning information
    for app-interface workflow processing.
    """

    data: RdsProxyData
    provision: AppInterfaceProvision
