from typing import Any

import pytest
from external_resources_io.input import parse_model

from er_aws_rds_proxy.app_interface_input import AppInterfaceInput

DEFAULT_DATA: dict = {
    "region": "us-east-1",
    "identifier": "app-int-example-01-rds-proxy1",
    "output_resource_name": "creds-rds-proxy1",
    "tags": {
        "managed_by_integration": "external_resources",
        "cluster": "appint-ex-01",
        "namespace": "example-rds-01",
        "environment": "production",
        "app": "rds-proxy-example",
    },
    "auth": [
        {
            "auth_scheme": "SECRETS",
            "secret_name": "rds-db-credentials",
        }
    ],
    "db_instance_identifier": "rds-db-instance-id",
    "engine_family": "POSTGRESQL",
    "vpc_security_group_ids": ["sg-1", "sg-2"],
    "vpc_subnet_ids": ["subnet-1", "subnet-2", "subnet-3"],
}

DEFAULT_PROVISION: dict = {
    "provision_provider": "aws",
    "provisioner": "app-int-example-01",
    "provider": "rds-proxy",
    "identifier": "app-int-example-01-rds-proxy1",
    "target_cluster": "appint-ex-01",
    "target_namespace": "example-rds-01",
    "target_secret_name": "creds-rds-proxy1",
    "module_provision_data": {
        "tf_state_bucket": "external-resources-terraform-state-dev",
        "tf_state_region": "us-east-1",
        "tf_state_dynamodb_table": "external-resources-terraform-lock",
        "tf_state_key": "aws/app-int-example-01/rds-proxy/app-int-example-01-rds-proxy1/terraform.tfstate",
    },
}


def build_input_data(  # noqa: PLR0913
    *,
    auth_scheme: str | None = None,
    client_password_auth_type: str | None = None,
    description: str | None = None,
    iam_auth: str | None = None,
    secret_name: str | None = None,
    username: str | None = None,
    auth: list[dict] | None = None,
    **kwargs: Any,  # noqa: ANN401
) -> dict:
    """Build test input data with optional overrides.

    This builder allows creating test input data by overriding specific fields
    while using defaults for the rest. For auth-related fields, it modifies
    the first auth entry in the auth list.

    Args:
        auth_scheme: Override auth_scheme in first auth entry
        client_password_auth_type: Override client_password_auth_type in first auth entry
        description: Override description in first auth entry
        iam_auth: Override iam_auth in first auth entry
        secret_name: Override secret_name in first auth entry
        username: Override username in first auth entry
        auth: Override entire auth list
        region: Override region
        identifier: Override identifier
        output_resource_name: Override output_resource_name
        tags: Override tags
        connection_borrow_timeout: Override connection_borrow_timeout
        db_instance_identifier: Override db_instance_identifier
        debug_logging: Override debug_logging
        engine_family: Override engine_family
        iam_role_force_detach_policies: Override iam_role_force_detach_policies
        iam_role_max_session_duration: Override iam_role_max_session_duration
        idle_client_timeout: Override idle_client_timeout
        init_query: Override init_query
        log_group_retention_in_days: Override log_group_retention_in_days
        max_connections_percent: Override max_connections_percent
        max_idle_connections_percent: Override max_idle_connections_percent
        require_tls: Override require_tls
        session_pinning_filters: Override session_pinning_filters
        vpc_security_group_ids: Override vpc_security_group_ids
        vpc_subnet_ids: Override vpc_subnet_ids

    Returns:
        Test input data dictionary
    """
    auth_0 = {
        "auth_scheme": auth_scheme or DEFAULT_DATA["auth"][0]["auth_scheme"],
        "secret_name": secret_name or DEFAULT_DATA["auth"][0]["secret_name"],
        "client_password_auth_type": client_password_auth_type,
        "description": description,
        "iam_auth": iam_auth,
        "username": username,
    }

    if unexpected := kwargs.keys() - DEFAULT_DATA.keys():
        raise TypeError(
            f"build_input_data() got unexpected keyword argument(s): {unexpected}"
        )

    return {
        "data": DEFAULT_DATA | {"auth": auth or [auth_0]} | kwargs,
        "provision": DEFAULT_PROVISION,
    }


@pytest.fixture
def ai_input() -> AppInterfaceInput:
    """Fixture to provide the AppInterfaceInput."""
    return parse_model(AppInterfaceInput, build_input_data())
