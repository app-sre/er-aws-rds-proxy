output "proxy_id" {
  description = "The ID for the proxy"
  value       = aws_db_proxy.this.id
}

output "proxy_arn" {
  description = "The Amazon Resource Name (ARN) for the proxy"
  value       = aws_db_proxy.this.arn
}

output "proxy_endpoint" {
  description = "The endpoint that you can use to connect to the proxy"
  value       = aws_db_proxy.this.endpoint
}
