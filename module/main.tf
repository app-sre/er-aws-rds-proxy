locals {
  partition  = data.aws_partition.current.partition
  account_id = data.aws_caller_identity.current.account_id
}

provider "aws" {
  region = var.region

  default_tags {
    tags = var.tags
  }
}

data "aws_partition" "current" {}

data "aws_caller_identity" "current" {}

# a map like datasource indexed by the position index in auth
# that will be used to get the arn of every secret given its name.
data "aws_secretsmanager_secret" "auth_secret" {
  for_each = { for idx, auth in var.auth : idx => auth.secret_name }
  name     = each.value
}

resource "aws_db_proxy" "this" {
  dynamic "auth" {
    for_each = var.auth
    content {
      auth_scheme               = auth.value.auth_scheme
      client_password_auth_type = auth.value.client_password_auth_type
      description               = auth.value.description
      iam_auth                  = auth.value.iam_auth
      secret_arn                = data.aws_secretsmanager_secret.auth_secret[auth.key].arn
      username                  = auth.value.username
    }
  }

  debug_logging          = var.debug_logging
  engine_family          = var.engine_family
  idle_client_timeout    = var.idle_client_timeout
  name                   = var.identifier
  require_tls            = var.require_tls
  role_arn               = aws_iam_role.this.arn
  vpc_security_group_ids = var.vpc_security_group_ids
  vpc_subnet_ids         = var.vpc_subnet_ids

  tags = var.tags

  depends_on = [aws_cloudwatch_log_group.this]
}

resource "aws_db_proxy_default_target_group" "this" {
  db_proxy_name = aws_db_proxy.this.name

  connection_pool_config {
    connection_borrow_timeout    = var.connection_borrow_timeout
    init_query                   = var.init_query
    max_connections_percent      = var.max_connections_percent
    max_idle_connections_percent = var.max_idle_connections_percent
    session_pinning_filters      = var.session_pinning_filters
  }
}

resource "aws_db_proxy_target" "db_instance" {
  db_proxy_name          = aws_db_proxy.this.name
  target_group_name      = aws_db_proxy_default_target_group.this.name
  db_instance_identifier = var.db_instance_identifier
}

resource "aws_cloudwatch_log_group" "this" {
  name              = "/aws/rds/proxy/${var.identifier}"
  retention_in_days = var.log_group_retention_in_days

  tags = var.tags
}

resource "aws_iam_role" "this" {
  name = var.identifier

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "rds.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  force_detach_policies = var.iam_role_force_detach_policies
  max_session_duration  = var.iam_role_max_session_duration

  tags = var.tags
}

data "aws_iam_policy_document" "this" {
  statement {
    sid       = "DecryptSecrets"
    effect    = "Allow"
    actions   = ["kms:Decrypt"]
    resources = ["arn:${local.partition}:kms:${var.region}:${local.account_id}:key/*"]

    condition {
      test     = "StringEquals"
      variable = "kms:ViaService"
      values = [
        "secretsmanager.${var.region}.amazonaws.com"
      ]
    }
  }

  statement {
    sid     = "GetSecrets"
    effect  = "Allow"
    actions = ["secretsmanager:GetSecretValue"]

    resources = distinct([for idx, auth in var.auth : data.aws_secretsmanager_secret.auth_secret[idx].arn])
  }
}

resource "aws_iam_role_policy" "this" {
  name   = var.identifier
  policy = data.aws_iam_policy_document.this.json
  role   = aws_iam_role.this.id
}
