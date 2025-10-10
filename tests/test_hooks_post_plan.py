from collections.abc import Iterator
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError
from external_resources_io.terraform import Action, ResourceChange

from er_aws_rds_proxy.app_interface_input import AppInterfaceInput
from hooks.post_plan import RdsProxyPlanValidator, TerraformJsonPlanParser


@pytest.fixture
def mock_terraform_plan_parser() -> MagicMock:
    """Mock TerraformJsonPlanParser for testing."""
    mock_plan = MagicMock()
    mock_plan.resource_changes = []
    parser = MagicMock(spec=TerraformJsonPlanParser)
    parser.plan = mock_plan
    return parser


@pytest.fixture
def mock_aws_api() -> Iterator[MagicMock]:
    """Mock AWSApi for testing."""
    with patch("hooks.post_plan.AWSApi") as mock:
        yield mock


def test_rds_proxy_plan_validator_validate_success(
    ai_input: AppInterfaceInput,
    mock_terraform_plan_parser: MagicMock,
    mock_aws_api: MagicMock,
) -> None:
    """Test the full validate method with valid data."""
    subnets = [
        "subnet-0a1b2c3d4e5f6a7b8",
        "subnet-0a1b2c3d4e5f6a7b9",
        "subnet-0a1b2c3d4e5f6a7c0",
    ]
    security_groups = ["sg-0a1b2c3d4e5f6a7b8"]
    mock_aws_api.return_value.get_subnets.return_value = [
        {"SubnetId": s, "VpcId": "vpc-123"} for s in subnets
    ]
    mock_aws_api.return_value.get_security_groups.return_value = [
        {"GroupId": sg, "VpcId": "vpc-123"} for sg in security_groups
    ]

    mock_terraform_plan_parser.plan.resource_changes = [
        MagicMock(
            spec=ResourceChange,
            type="aws_db_proxy",
            change=MagicMock(
                after={
                    "vpc_subnet_ids": subnets,
                    "vpc_security_group_ids": security_groups,
                },
                actions=[Action.ActionCreate],
            ),
        )
    ]

    validator = RdsProxyPlanValidator(mock_terraform_plan_parser, ai_input)
    assert validator.validate()
    assert not validator.errors


def test_rds_proxy_plan_validator_validate_failure_missing_subnet(
    ai_input: AppInterfaceInput,
    mock_terraform_plan_parser: MagicMock,
    mock_aws_api: MagicMock,
) -> None:
    """Test validation failure with a missing subnet."""
    subnets = [
        "subnet-0a1b2c3d4e5f6a7b8",
        "subnet-0a1b2c3d4e5f6a7b9",
        "subnet-0a1b2c3d4e5f6a7c0",
    ]
    security_groups = ["sg-0a1b2c3d4e5f6a7b8"]
    # Only return 2 of the 3 subnets
    mock_aws_api.return_value.get_subnets.return_value = [
        {"SubnetId": s, "VpcId": "vpc-123"} for s in subnets[:2]
    ]
    mock_aws_api.return_value.get_security_groups.return_value = [
        {"GroupId": sg, "VpcId": "vpc-123"} for sg in security_groups
    ]

    mock_terraform_plan_parser.plan.resource_changes = [
        MagicMock(
            spec=ResourceChange,
            type="aws_db_proxy",
            change=MagicMock(
                after={
                    "vpc_subnet_ids": subnets,
                    "vpc_security_group_ids": security_groups,
                },
                actions=[Action.ActionCreate],
            ),
        )
    ]

    validator = RdsProxyPlanValidator(mock_terraform_plan_parser, ai_input)
    assert not validator.validate()
    assert len(validator.errors) == 1
    assert "Subnet(s)" in validator.errors[0]
    assert "not found" in validator.errors[0]


def test_rds_proxy_plan_validator_validate_failure_subnets_different_vpcs(
    ai_input: AppInterfaceInput,
    mock_terraform_plan_parser: MagicMock,
    mock_aws_api: MagicMock,
) -> None:
    """Test validation failure with subnets in different VPCs."""
    subnets = [
        "subnet-0a1b2c3d4e5f6a7b8",
        "subnet-0a1b2c3d4e5f6a7b9",
        "subnet-0a1b2c3d4e5f6a7c0",
    ]
    security_groups = ["sg-0a1b2c3d4e5f6a7b8"]
    # Return subnets in different VPCs
    mock_aws_api.return_value.get_subnets.return_value = [
        {"SubnetId": subnets[0], "VpcId": "vpc-123"},
        {"SubnetId": subnets[1], "VpcId": "vpc-456"},
        {"SubnetId": subnets[2], "VpcId": "vpc-789"},
    ]
    mock_aws_api.return_value.get_security_groups.return_value = [
        {"GroupId": sg, "VpcId": "vpc-123"} for sg in security_groups
    ]

    mock_terraform_plan_parser.plan.resource_changes = [
        MagicMock(
            spec=ResourceChange,
            type="aws_db_proxy",
            change=MagicMock(
                after={
                    "vpc_subnet_ids": subnets,
                    "vpc_security_group_ids": security_groups,
                },
                actions=[Action.ActionCreate],
            ),
        )
    ]

    validator = RdsProxyPlanValidator(mock_terraform_plan_parser, ai_input)
    assert not validator.validate()
    assert len(validator.errors) >= 1
    assert any(
        "All subnets must belong to the same VPC" in error for error in validator.errors
    )


def test_rds_proxy_plan_validator_validate_failure_missing_security_group(
    ai_input: AppInterfaceInput,
    mock_terraform_plan_parser: MagicMock,
    mock_aws_api: MagicMock,
) -> None:
    """Test validation failure with a missing security group."""
    subnets = [
        "subnet-0a1b2c3d4e5f6a7b8",
        "subnet-0a1b2c3d4e5f6a7b9",
        "subnet-0a1b2c3d4e5f6a7c0",
    ]
    security_groups = ["sg-0a1b2c3d4e5f6a7b8", "sg-0a1b2c3d4e5f6a7b9"]
    mock_aws_api.return_value.get_subnets.return_value = [
        {"SubnetId": s, "VpcId": "vpc-123"} for s in subnets
    ]
    # Only return 1 of the 2 security groups
    mock_aws_api.return_value.get_security_groups.return_value = [
        {"GroupId": security_groups[0], "VpcId": "vpc-123"}
    ]

    mock_terraform_plan_parser.plan.resource_changes = [
        MagicMock(
            spec=ResourceChange,
            type="aws_db_proxy",
            change=MagicMock(
                after={
                    "vpc_subnet_ids": subnets,
                    "vpc_security_group_ids": security_groups,
                },
                actions=[Action.ActionCreate],
            ),
        )
    ]

    validator = RdsProxyPlanValidator(mock_terraform_plan_parser, ai_input)
    assert not validator.validate()
    assert len(validator.errors) == 1
    assert "Security group(s)" in validator.errors[0]
    assert "not found" in validator.errors[0]


def test_rds_proxy_plan_validator_validate_failure_security_group_wrong_vpc(
    ai_input: AppInterfaceInput,
    mock_terraform_plan_parser: MagicMock,
    mock_aws_api: MagicMock,
) -> None:
    """Test validation failure with security group in wrong VPC."""
    subnets = [
        "subnet-0a1b2c3d4e5f6a7b8",
        "subnet-0a1b2c3d4e5f6a7b9",
        "subnet-0a1b2c3d4e5f6a7c0",
    ]
    security_groups = ["sg-0a1b2c3d4e5f6a7b8"]
    mock_aws_api.return_value.get_subnets.return_value = [
        {"SubnetId": s, "VpcId": "vpc-123"} for s in subnets
    ]
    mock_aws_api.return_value.get_security_groups.return_value = [
        {"GroupId": sg, "VpcId": "vpc-456"} for sg in security_groups
    ]  # Wrong VPC

    mock_terraform_plan_parser.plan.resource_changes = [
        MagicMock(
            spec=ResourceChange,
            type="aws_db_proxy",
            change=MagicMock(
                after={
                    "vpc_subnet_ids": subnets,
                    "vpc_security_group_ids": security_groups,
                },
                actions=[Action.ActionCreate],
            ),
        )
    ]

    validator = RdsProxyPlanValidator(mock_terraform_plan_parser, ai_input)
    assert not validator.validate()
    assert len(validator.errors) == 1
    assert (
        f"Security group {security_groups[0]} does not belong to the same VPC as the subnets"
        in validator.errors[0]
    )


def test_rds_proxy_plan_validator_no_changes(
    ai_input: AppInterfaceInput,
    mock_terraform_plan_parser: MagicMock,
    mock_aws_api: MagicMock,  # noqa: ARG001
) -> None:
    """Test validation when there are no resource changes."""
    mock_terraform_plan_parser.plan.resource_changes = []

    validator = RdsProxyPlanValidator(mock_terraform_plan_parser, ai_input)
    assert validator.validate()
    assert not validator.errors


def test_rds_proxy_plan_validator_non_create_action(
    ai_input: AppInterfaceInput,
    mock_terraform_plan_parser: MagicMock,
    mock_aws_api: MagicMock,  # noqa: ARG001
) -> None:
    """Test validation with non-create actions (update/delete)."""
    subnets = ["subnet-1", "subnet-2"]
    security_groups = ["sg-1"]

    mock_terraform_plan_parser.plan.resource_changes = [
        MagicMock(
            spec=ResourceChange,
            type="aws_db_proxy",
            change=MagicMock(
                after={
                    "vpc_subnet_ids": subnets,
                    "vpc_security_group_ids": security_groups,
                },
                actions=[Action.ActionUpdate],  # Not a create action
            ),
        )
    ]

    validator = RdsProxyPlanValidator(mock_terraform_plan_parser, ai_input)
    assert validator.validate()
    assert not validator.errors


def test_rds_proxy_plan_validator_rds_proxy_instance_updates(
    ai_input: AppInterfaceInput,
    mock_terraform_plan_parser: MagicMock,
    mock_aws_api: MagicMock,  # noqa: ARG001
) -> None:
    """Test the rds_proxy_instance_updates property."""
    mock_terraform_plan_parser.plan.resource_changes = [
        MagicMock(
            spec=ResourceChange,
            type="aws_db_proxy",
            change=MagicMock(
                after={"vpc_subnet_ids": [], "vpc_security_group_ids": []},
                actions=[Action.ActionCreate],
            ),
        ),
        MagicMock(
            spec=ResourceChange,
            type="aws_db_proxy",
            change=MagicMock(
                after={"vpc_subnet_ids": [], "vpc_security_group_ids": []},
                actions=[Action.ActionUpdate],
            ),
        ),
        MagicMock(
            spec=ResourceChange,
            type="aws_db_proxy_default_target_group",
            change=MagicMock(
                after={},
                actions=[Action.ActionCreate],
            ),
        ),
    ]

    validator = RdsProxyPlanValidator(mock_terraform_plan_parser, ai_input)
    updates = validator.rds_proxy_instance_updates

    # Should only include aws_db_proxy resources with ActionCreate
    assert len(updates) == 1
    assert updates[0].type == "aws_db_proxy"
    assert updates[0].change is not None
    assert Action.ActionCreate in updates[0].change.actions


def test_rds_proxy_plan_validator_validate_failure_malformed_subnet_id(
    ai_input: AppInterfaceInput,
    mock_terraform_plan_parser: MagicMock,
    mock_aws_api: MagicMock,
) -> None:
    """Test validation failure with malformed subnet ID."""
    subnets = ["subnet-invalid123"]
    security_groups = ["sg-0a1b2c3d4e5f6a7b8"]

    # Simulate ClientError for malformed subnet ID
    mock_aws_api.return_value.get_subnets.side_effect = ClientError(
        error_response={
            "Error": {
                "Code": "InvalidSubnetID.Malformed",
                "Message": 'Invalid id: "subnet-invalid123"',
            }
        },
        operation_name="DescribeSubnets",
    )

    mock_terraform_plan_parser.plan.resource_changes = [
        MagicMock(
            spec=ResourceChange,
            type="aws_db_proxy",
            change=MagicMock(
                after={
                    "vpc_subnet_ids": subnets,
                    "vpc_security_group_ids": security_groups,
                },
                actions=[Action.ActionCreate],
            ),
        )
    ]

    validator = RdsProxyPlanValidator(mock_terraform_plan_parser, ai_input)
    assert not validator.validate()
    assert len(validator.errors) == 1
    assert "Error validating subnets" in validator.errors[0]


def test_rds_proxy_plan_validator_validate_failure_malformed_security_group_id(
    ai_input: AppInterfaceInput,
    mock_terraform_plan_parser: MagicMock,
    mock_aws_api: MagicMock,
) -> None:
    """Test validation failure with malformed security group ID."""
    subnets = [
        "subnet-0a1b2c3d4e5f6a7b8",
        "subnet-0a1b2c3d4e5f6a7b9",
        "subnet-0a1b2c3d4e5f6a7c0",
    ]
    security_groups = ["sg-1a25f23d9ca77bb24"]  # Malformed ID

    mock_aws_api.return_value.get_subnets.return_value = [
        {"SubnetId": s, "VpcId": "vpc-123"} for s in subnets
    ]

    # Simulate ClientError for malformed security group ID
    mock_aws_api.return_value.get_security_groups.side_effect = ClientError(
        error_response={
            "Error": {
                "Code": "InvalidGroupId.Malformed",
                "Message": 'Invalid id: "sg-1a25f23d9ca77bb24"',
            }
        },
        operation_name="DescribeSecurityGroups",
    )

    mock_terraform_plan_parser.plan.resource_changes = [
        MagicMock(
            spec=ResourceChange,
            type="aws_db_proxy",
            change=MagicMock(
                after={
                    "vpc_subnet_ids": subnets,
                    "vpc_security_group_ids": security_groups,
                },
                actions=[Action.ActionCreate],
            ),
        )
    ]

    validator = RdsProxyPlanValidator(mock_terraform_plan_parser, ai_input)
    assert not validator.validate()
    assert len(validator.errors) == 1
    assert "Error validating security groups" in validator.errors[0]
