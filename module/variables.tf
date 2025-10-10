# Do not generate this variable from the model, as it is not mark
# values with None default as optional
variable "auth" {
  type = list(object({
    auth_scheme               = string
    client_password_auth_type = optional(string)
    description               = optional(string)
    iam_auth                  = optional(string)
    secret_name               = optional(string)
    username                  = optional(string)
  }))
}

variable "connection_borrow_timeout" {
  type        = number
  default     = null
  description = "Seconds to wait for connection availability"
}

variable "db_instance_identifier" {
  type        = string
  description = "Database instance identifier"
}

variable "debug_logging" {
  type        = bool
  default     = false
  description = "Enable detailed SQL statement logging"
}

variable "engine_family" {
  type        = string
  default     = "POSTGRESQL"
  description = "Database engine family (MYSQL or POSTGRESQL)"
}

variable "iam_role_force_detach_policies" {
  type        = bool
  default     = true
  description = "Force detach policies before destroying IAM role"
}

variable "iam_role_max_session_duration" {
  type        = number
  default     = 43200
  description = "Maximum session duration for IAM role (seconds)"
}

variable "identifier" {
  type        = string
  description = "Name identifier for the proxy"
}

variable "idle_client_timeout" {
  type        = number
  default     = 1800
  description = "Seconds before disconnecting idle connections"
}

variable "init_query" {
  type        = string
  default     = ""
  description = "SQL statements to run on new connections"
}

variable "log_group_retention_in_days" {
  type        = number
  default     = 30
  description = "CloudWatch log retention period (days)"
}

variable "max_connections_percent" {
  type        = number
  default     = 90
  description = "Maximum connection pool size percentage"
}

variable "max_idle_connections_percent" {
  type        = number
  default     = 50
  description = "Maximum idle connections percentage"
}

variable "output_resource_name" {
  type    = string
  default = null
}

variable "region" {
  type        = string
  description = "AWS region"
}

variable "require_tls" {
  type        = bool
  default     = true
  description = "Require TLS encryption for connections"
}

variable "session_pinning_filters" {
  type        = list(string)
  default     = []
  description = "SQL operations that trigger session pinning"
}

variable "tags" {
  type        = map(string)
  description = "Resource tags"
}

variable "vpc_security_group_ids" {
  type        = list(string)
  description = "VPC security group IDs"
}

variable "vpc_subnet_ids" {
  type        = list(string)
  description = "VPC subnet IDs"
}
