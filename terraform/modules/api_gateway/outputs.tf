output "api_gateway_id" {
  description = "The ID of the API Gateway REST API"
  value       = aws_api_gateway_rest_api.api.id
}

output "api_gateway_invoke_url" {
  description = "The invoke URL for the API Gateway deployment"
  value       = "https://${aws_api_gateway_rest_api.api.id}.execute-api.${var.aws_region}.amazonaws.com/${var.stage_name}"
}

output "api_gateway_stage_name" {
  description = "The name of the API Gateway stage"
  value       = aws_api_gateway_stage.api_stage.stage_name
}

output "videos_endpoint_url" {
  description = "Full URL for the videos endpoint"
  value       = "https://${aws_api_gateway_rest_api.api.id}.execute-api.${var.aws_region}.amazonaws.com/${var.stage_name}/${var.videos_path}"
}

output "search_endpoint_url" {
  description = "Full URL for the search endpoint"
  value       = "${aws_api_gateway_stage.api_stage.invoke_url}/${var.search_path}"
}

output "generate_upload_link_endpoint_url" {
  description = "Full URL for the generate-upload-link endpoint"
  value       = "${aws_api_gateway_stage.api_stage.invoke_url}/${var.generate_upload_link_path}"
}

output "tasks_endpoint_url" {
  description = "Full URL for the tasks endpoint"
  value       = "${aws_api_gateway_stage.api_stage.invoke_url}/${var.tasks_path}"
}

output "api_gateway_execution_arn" {
  description = "The execution ARN of the API Gateway REST API"
  value       = aws_api_gateway_rest_api.api.execution_arn
}

output "api_gateway_arn" {
  description = "The ARN of the API Gateway REST API"
  value       = aws_api_gateway_rest_api.api.arn
}
