import pytest
from pydantic import ValidationError

from er_aws_rds_proxy.app_interface_input import AppInterfaceInput
from tests.conftest import build_input_data

# ruff: noqa: S105, PLR2004


def test_auth_iam_auth_defaults_to_disabled_with_secrets() -> None:
    """Test that iam_auth defaults to DISABLED when auth_scheme is SECRETS."""
    data = build_input_data()
    model = AppInterfaceInput.model_validate(data)
    assert model.data.auth[0].iam_auth == "DISABLED"


def test_auth_iam_auth_explicit_value() -> None:
    """Test that explicitly set iam_auth is not overridden."""
    data = build_input_data(iam_auth="REQUIRED")
    model = AppInterfaceInput.model_validate(data)
    assert model.data.auth[0].iam_auth == "REQUIRED"


def test_auth_secret_name_required_with_secrets() -> None:
    """Test that secret_name is required when auth_scheme is SECRETS."""
    data = build_input_data(auth=[{"auth_scheme": "SECRETS"}])
    with pytest.raises(
        ValidationError,
        match="secret_name must be set when auth_scheme is SECRETS",
    ):
        AppInterfaceInput.model_validate(data)


def test_client_password_auth_type_defaults_for_postgres() -> None:
    """Test that client_password_auth_type defaults to POSTGRES_SCRAM_SHA_256 for POSTGRES."""
    data = build_input_data()
    model = AppInterfaceInput.model_validate(data)
    assert model.data.engine_family == "POSTGRESQL"
    assert model.data.auth[0].client_password_auth_type == "POSTGRES_SCRAM_SHA_256"


def test_client_password_auth_type_explicit_value_preserved() -> None:
    """Test that explicitly set client_password_auth_type is preserved."""
    data = build_input_data(client_password_auth_type="POSTGRES_MD5")  # noqa: S106
    model = AppInterfaceInput.model_validate(data)
    assert model.data.auth[0].client_password_auth_type == "POSTGRES_MD5"


def test_multiple_auth_configs() -> None:
    """Test that validators work correctly with multiple auth configurations."""
    data = build_input_data(
        auth=[
            {"auth_scheme": "SECRETS", "secret_name": "secret-1"},
            {"auth_scheme": "SECRETS", "secret_name": "secret-2"},
        ]
    )

    model = AppInterfaceInput.model_validate(data)
    assert len(model.data.auth) == 2
    assert model.data.auth[0].iam_auth == "DISABLED"
    assert model.data.auth[0].client_password_auth_type == "POSTGRES_SCRAM_SHA_256"
    assert model.data.auth[1].iam_auth == "DISABLED"
    assert model.data.auth[1].client_password_auth_type == "POSTGRES_SCRAM_SHA_256"
