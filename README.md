# External Resources RDS Proxy Module

External Resources module to provision and manage AWS RDS Proxy instances with App-Interface.

## Tech stack

* Terraform
* AWS provider
* Random provider
* Python 3.12
* Pydantic

## Development

Ensure `uv` is installed.

Prepare local development environment:

```shell
make dev
```

This will auto create a `venv`, to activate in shell:

```shell
source .venv/bin/activate
```

### Manage Terraform Providers

* update versions in [versions.tf](./module/versions.tf)
* refresh [.terraform.lock.hcl](./module/.terraform.lock.hcl) with:

  ```shell
  make providers-lock
  ```

## Debugging

* Set env variables
```shell
REPO_DIR=$(pwd)
cat > .env <<EOF
AWS_SHARED_CREDENTIALS_FILE=$REPO_DIR/tmp/credentials
INPUT_FILE=$REPO_DIR/tmp/input.json
PLAN_FILE_JSON=$REPO_DIR/module/plan.json
WORK=$REPO_DIR/tmp/work
EOF

export $(cat .env | xargs)
```

* Set provisioner (AWS account) and resource identifier:
```shell
PROVISIONER=<your aws account>
IDENTIFIER=<resource name>
```

* Export `input.json` via `qontract-cli` and place it in the current project root dir.
```shell
mkdir -p $WORK
qontract-cli --config $CONFIG external-resources --provisioner $PROVISIONER --provider rds-proxy --identifier $IDENTIFIER get-input > $INPUT_FILE
```

* Get `credentials`
```shell
qontract-cli --config $CONFIG external-resources --provisioner $PROVISIONER --provider rds-proxy --identifier $IDENTIFIER get-credentials > $AWS_SHARED_CREDENTIALS_FILE
```

### On Host

* Generate terraform config.
```shell
generate-tf-config
```

* Ensure AWS credentials set in current shell, e.g. using `rh-aws-saml-login`, then use `terraform` to verify.
```shell
cd module
rm backend.tf  # it makes reference to the central s3/dynamo lock, we don't need it to plan locally.
terraform init
terraform plan -out=plan
terraform show -json plan > $PLAN_FILE_JSON
```

* Test hooks
```shell
hooks/post_plan.py
```

### In Container

* Build image first
```shell
make build
```

* Get the input and credentials files as shown in the example

* Start container
```shell
docker run --rm -it \
    --mount type=bind,source=$PWD/tmp/input.json,target=/inputs/input.json \
    --mount type=bind,source=$PWD/tmp/credentials,target=/credentials \
    --mount type=bind,source=$PWD/tmp/work,target=/work \
    -e DRY_RUN=True \
    -e ACTION=Apply \
    "$IMAGE"
```

being `IMAGE=quay.io/redhat-services-prod/app-sre-tenant/er-aws-rds-proxy-main/er-aws-rds-proxy-main` but you may want to override things locally.
