# Project Overview

External Resources module to provision and manage AWS RDS Proxy instances with app-interface.

## Tech Stack

* Terraform
* AWS provider
* Random provider
* Python 3.12
* Pydantic

## Architecture

The Terraform module creates the following AWS resources:
- `aws_db_proxy` - The main RDS proxy resource with authentication via AWS Secrets Manager
- `aws_db_proxy_default_target_group` - Connection pool configuration for the proxy
- `aws_db_proxy_target` - Targets for DB instances only (no cluster support currently)
- `aws_iam_role` and `aws_iam_role_policy` - IAM role for proxy to access Secrets Manager
- `aws_cloudwatch_log_group` - CloudWatch logging for the proxy

Key design patterns:
- Uses AWS Secrets Manager for database credentials (SECRETS auth scheme)
- Currently supports only single DB instances via `db_instance_identifier`
- IAM policy allows KMS decryption and Secrets Manager access with proper conditions
- All resources are tagged consistently using the `tags` variable
- Connection pooling settings are fully configurable

## File Structure

```
module/
├── main.tf           # Primary resource definitions
├── variables.tf      # Input variables (alphabetically ordered)
├── outputs.tf        # Module outputs (proxy_id, proxy_arn, proxy_endpoint)
└── versions.tf       # Terraform and provider version constraints

er_aws_rds_proxy/
├── config.py         # Configuration and Terraform file generation
└── input.py          # Pydantic models for input validation

hooks_lib/
└── aws_api.py        # AWS API wrapper for EC2 operations

hooks/
└── post_plan.py      # Terraform plan validation hook

tests/
├── conftest.py       # Pytest fixtures
├── test_config.py    # Tests for configuration module
├── test_input.py     # Tests for Pydantic validators
├── test_hooks_lib_aws_api.py    # Tests for AWS API wrapper
└── test_hooks_post_plan.py      # Tests for plan validation
```

## Development

Prepare your local development environment:

```bash
make dev
```

See the `Makefile` for more details.

### Update Terraform modules

To update the Terraform modules used in this project, bump the version in [versions.tf](/module/versions.tf) and update the Terraform lockfile via:

```bash
make providers-lock
```

### Development workflow

1. Make changes to the code.
1. Build the image with `make build`.
1. Run the image manually with a proper input file and credentials. See the [Debugging](#debugging) section below.
1. Please don't forget to remove (`-e ACTION=Destroy`) any development AWS resources you create, as they will incur costs.

### Running Tests

Run the Python test suite with pytest:

```bash
make test
```

The test suite includes:
- **test_hooks_lib_aws_api.py** - Tests for AWS API wrapper (100% coverage)
- **test_hooks_post_plan.py** - Tests for Terraform plan validation (82% coverage)
- **test_config.py** - Tests for configuration module
- **test_input.py** - Tests for Pydantic model validators (100% coverage for input.py)

The tests use pytest-mock to mock AWS API calls and don't require actual AWS credentials.

## Debugging

To debug and run the module locally, run the following commands:

```bash
# setup the environment
$ export VERSION=$(grep konflux.additional-tags Dockerfile | cut -f2 -d\")
$ export IMAGE=quay.io/redhat-services-prod/app-sre-tenant/er-aws-rds-proxy-main/er-aws-rds-proxy-main:$VERSION

# Get the input file from app-interface
qontract-cli --config=<CONFIG_TOML> external-resources --provisioner <AWS_ACCOUNT_NAME> --provider rds-proxy --identifier <IDENTIFIER> get-input > tmp/input.json

# Get the AWS credentials
$ qontract-cli --config=<CONFIG_TOML> external-resources --provisioner <AWS_ACCOUNT_NAME> --provider rds-proxy --identifier <IDENTIFIER> get-credentials > tmp/credentials

# Run the stack
$ docker run --rm -it \
    --mount type=bind,source=$PWD/tmp/input.json,target=/inputs/input.json \
    --mount type=bind,source=$PWD/tmp/credentials,target=/credentials \
    --mount type=bind,source=$PWD/tmp/work,target=/work \
    -e DRY_RUN=True \
    -e ACTION=Apply \
    "$IMAGE"
```
