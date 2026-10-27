FROM quay.io/redhat-services-prod/app-sre-tenant/er-base-terraform-main/er-base-terraform-main:0.6.0-25@sha256:073f924e01936c5abd228d1c5a6412271d8ed4b4c4e41f8eb0fac5571550d83e AS base
# keep in sync with pyproject.toml
LABEL konflux.additional-tags="0.3.0"
COPY LICENSE /licenses/
ENV TERRAFORM_MODULE_SRC_DIR="./module"

FROM base AS builder
COPY --from=ghcr.io/astral-sh/uv:0.13.6@sha256:af22a52f5eafef3d78e551599d405c02df61919d18028f0cea8eda93bc9986d0 /uv /bin/uv

# Terraform code
COPY ${TERRAFORM_MODULE_SRC_DIR} ${TERRAFORM_MODULE_SRC_DIR}
RUN terraform-provider-sync

COPY pyproject.toml uv.lock ./
# Test lock file is up to date
RUN uv lock --locked
# Install dependencies
RUN uv sync --frozen --no-group dev --no-install-project

# the source code
COPY README.md ./
COPY er_aws_rds_proxy ./er_aws_rds_proxy
COPY hooks ./hooks
COPY hooks_lib ./hooks_lib
# Sync the project
RUN uv sync --frozen --no-group dev

FROM builder AS test
# install test dependencies
RUN uv sync --frozen

COPY Makefile ./
COPY tests ./tests

RUN make in_container_test

FROM base AS prod
# get terraform providers
COPY --from=builder ${TF_PLUGIN_CACHE_DIR} ${TF_PLUGIN_CACHE_DIR}
# get our app with the dependencies
COPY --from=builder ${APP_ROOT} ${APP_ROOT}
