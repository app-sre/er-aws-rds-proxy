CONTAINER_ENGINE ?= $(shell which podman >/dev/null 2>&1 && echo podman || echo docker)
CONTAINER_ENGINE_OPTIONS ?=
CONTAINER_NAME ?= er-aws-rds-proxy

.PHONY: format
format:
	uv run ruff check
	uv run ruff format
	terraform fmt module

.PHONY: image_tests
image_tests:
	# hooks and hooks_lib must be copied
	[ -d "hooks" ]
	[ -d "hooks_lib" ]

	# sources must be copied
	[ -d "$$TERRAFORM_MODULE_SRC_DIR" ]

	# test the terrform providers are downloaded
	[ -d "$$TF_PLUGIN_CACHE_DIR/registry.terraform.io/hashicorp/aws" ]

	# test all files in ./hooks are executable
	[ -z "$(shell for f in hooks/*; do [ ! -x "$$f" ] && [ "$$f" != "hooks/__init__.py" ] && echo not-executable; done)" ]


.PHONY: code_tests
code_tests:
	uv run ruff check --no-fix
	uv run ruff format --check
	terraform fmt -check=true "$$TERRAFORM_MODULE_SRC_DIR"
	uv run mypy
	uv run pytest -vv --cov=er_aws_rds_proxy --cov=hooks --cov=hooks_lib --cov-report=term-missing --cov-report xml

in_container_test: image_tests code_tests

.PHONY: test
test:
	$(CONTAINER_ENGINE) build $(CONTAINER_ENGINE_OPTIONS) --progress plain --target test -t $(CONTAINER_NAME):test .

.PHONY: build
build:
	$(CONTAINER_ENGINE) build $(CONTAINER_ENGINE_OPTIONS) --progress plain --target prod -t $(CONTAINER_NAME):prod .

.PHONY: dev
dev:
	uv sync

.PHONY: generate-variables-tf
generate-variables-tf:
	uv run external-resources-io tf generate-variables-tf er_aws_rds_proxy.app_interface_input.AppInterfaceInput --output module/variables.tf

.PHONY: providers-lock
providers-lock:
	rm -f module/.terraform.lock.hcl
	terraform -chdir=module providers lock -platform=linux_amd64 -platform=linux_arm64 -platform=darwin_amd64 -platform=darwin_arm64
