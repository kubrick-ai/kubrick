resource "aws_api_gateway_rest_api" "api" {
  name = var.api_name
  binary_media_types = [
    "multipart/form-data",
  ]
}

resource "aws_api_gateway_request_validator" "search_validator" {
  name                        = "search-request-validator"
  rest_api_id                 = aws_api_gateway_rest_api.api.id
  validate_request_body       = true
  validate_request_parameters = false
}

resource "aws_api_gateway_resource" "videos" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_rest_api.api.root_resource_id
  path_part   = var.videos_path
}


resource "aws_api_gateway_method" "options_videos" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_resource.videos.id
  http_method   = "OPTIONS"
  authorization = "NONE"
  api_key_required = false
}

resource "aws_api_gateway_method" "get_videos" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_resource.videos.id
  http_method   = "GET"
  authorization = "NONE"
  api_key_required = false
}

resource "aws_api_gateway_resource" "search" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_rest_api.api.root_resource_id
  path_part   = var.search_path
}

resource "aws_api_gateway_resource" "generate_upload_link" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_rest_api.api.root_resource_id
  path_part   = var.generate_upload_link_path
}

resource "aws_api_gateway_resource" "tasks" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_rest_api.api.root_resource_id
  path_part   = var.tasks_path
}


resource "aws_api_gateway_method" "options_search" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_resource.search.id
  http_method   = "OPTIONS"
  authorization = "NONE"
  api_key_required = false
}

resource "aws_api_gateway_method" "post_search" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_resource.search.id
  http_method   = "POST"
  authorization = "NONE"
  api_key_required = false
  request_validator_id = aws_api_gateway_request_validator.search_validator.id

  request_parameters = {
    "method.request.header.Content-Type" = true
    "method.request.header.Accept"       = true
  }

    request_models = {
    "multipart/form-data" = "Empty"
  }
}

resource "aws_api_gateway_method" "options_generate_upload_link" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_resource.generate_upload_link.id
  http_method   = "OPTIONS"
  authorization = "NONE"
  api_key_required = false
}

resource "aws_api_gateway_method" "get_generate_upload_link" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_resource.generate_upload_link.id
  http_method   = "GET"
  authorization = "NONE"
  api_key_required = false

  request_parameters = {
    "method.request.querystring.filename" = true
  }
}

resource "aws_api_gateway_method" "options_tasks" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_resource.tasks.id
  http_method   = "OPTIONS"
  authorization = "NONE"
  api_key_required = false
}

resource "aws_api_gateway_method" "get_tasks" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_resource.tasks.id
  http_method   = "GET"
  authorization = "NONE"
  api_key_required = false
}

# Lambda Integrations
resource "aws_api_gateway_integration" "get_videos_lambda" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.videos.id
  http_method = aws_api_gateway_method.get_videos.http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = var.fetch_videos_lambda_invoke_arn
}

resource "aws_api_gateway_integration" "post_search_lambda" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.search.id
  http_method = aws_api_gateway_method.post_search.http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = var.search_lambda_invoke_arn
}

resource "aws_api_gateway_integration" "get_generate_upload_link_lambda" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.generate_upload_link.id
  http_method = aws_api_gateway_method.get_generate_upload_link.http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = var.upload_link_lambda_invoke_arn

  request_parameters = {
    "integration.request.querystring.filename" = "method.request.querystring.filename"
  }
}

resource "aws_api_gateway_integration" "get_tasks_lambda" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.tasks.id
  http_method = aws_api_gateway_method.get_tasks.http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = var.fetch_tasks_lambda_invoke_arn
}

# CORS Integrations for OPTIONS methods
resource "aws_api_gateway_integration" "options_videos_cors" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.videos.id
  http_method = aws_api_gateway_method.options_videos.http_method

  type = "MOCK"
  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_integration" "options_search_cors" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.search.id
  http_method = aws_api_gateway_method.options_search.http_method

  type = "MOCK"
  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_integration" "options_generate_upload_link_cors" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.generate_upload_link.id
  http_method = aws_api_gateway_method.options_generate_upload_link.http_method

  type = "MOCK"
  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_integration" "options_tasks_cors" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.tasks.id
  http_method = aws_api_gateway_method.options_tasks.http_method

  type = "MOCK"
  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

# Method Responses
resource "aws_api_gateway_method_response" "get_videos_200" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.videos.id
  http_method = aws_api_gateway_method.get_videos.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }
}

resource "aws_api_gateway_method_response" "post_search_200" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.search.id
  http_method = aws_api_gateway_method.post_search.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }
}

resource "aws_api_gateway_method_response" "options_videos_200" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.videos.id
  http_method = aws_api_gateway_method.options_videos.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = true
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
  }
}

resource "aws_api_gateway_method_response" "options_search_200" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.search.id
  http_method = aws_api_gateway_method.options_search.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = true
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
  }
}

resource "aws_api_gateway_method_response" "get_generate_upload_link_200" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.generate_upload_link.id
  http_method = aws_api_gateway_method.get_generate_upload_link.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }
}

resource "aws_api_gateway_method_response" "options_generate_upload_link_200" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.generate_upload_link.id
  http_method = aws_api_gateway_method.options_generate_upload_link.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = true
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
  }
}

resource "aws_api_gateway_method_response" "get_tasks_200" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.tasks.id
  http_method = aws_api_gateway_method.get_tasks.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }
}

resource "aws_api_gateway_method_response" "options_tasks_200" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.tasks.id
  http_method = aws_api_gateway_method.options_tasks.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = true
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
  }
}

resource "aws_api_gateway_integration_response" "options_videos_cors" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.videos.id
  http_method = aws_api_gateway_method.options_videos.http_method
  status_code = aws_api_gateway_method_response.options_videos_200.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,OPTIONS'"
  }

  depends_on = [aws_api_gateway_integration.options_videos_cors]
}

resource "aws_api_gateway_integration_response" "options_search_cors" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.search.id
  http_method = aws_api_gateway_method.options_search.http_method
  status_code = aws_api_gateway_method_response.options_search_200.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,Accept,Accept-Encoding'"
    "method.response.header.Access-Control-Allow-Methods" = "'POST,OPTIONS'"
  }

  depends_on = [aws_api_gateway_integration.options_search_cors]
}

resource "aws_api_gateway_integration_response" "options_generate_upload_link_cors" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.generate_upload_link.id
  http_method = aws_api_gateway_method.options_generate_upload_link.http_method
  status_code = aws_api_gateway_method_response.options_generate_upload_link_200.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,OPTIONS'"
  }

  depends_on = [aws_api_gateway_integration.options_generate_upload_link_cors]
}

resource "aws_api_gateway_integration_response" "options_tasks_cors" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.tasks.id
  http_method = aws_api_gateway_method.options_tasks.http_method
  status_code = aws_api_gateway_method_response.options_tasks_200.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,OPTIONS'"
  }

  depends_on = [aws_api_gateway_integration.options_tasks_cors]
}

resource "aws_lambda_permission" "allow_api_gateway_fetch_videos" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = var.fetch_videos_lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "allow_api_gateway_search" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = var.search_lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "allow_api_gateway_upload_link" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = var.upload_link_lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "allow_api_gateway_fetch_tasks" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = var.fetch_tasks_lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.api.execution_arn}/*/*"
}

resource "aws_api_gateway_deployment" "api_deployment" {
  rest_api_id = aws_api_gateway_rest_api.api.id

  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_resource.videos.id,
      aws_api_gateway_resource.search.id,
      aws_api_gateway_resource.generate_upload_link.id,
      aws_api_gateway_resource.tasks.id,
      aws_api_gateway_method.get_videos.id,
      aws_api_gateway_method.post_search.id,
      aws_api_gateway_method.get_generate_upload_link.id,
      aws_api_gateway_method.get_tasks.id,
      aws_api_gateway_method.options_videos.id,
      aws_api_gateway_method.options_search.id,
      aws_api_gateway_method.options_generate_upload_link.id,
      aws_api_gateway_method.options_tasks.id,
      aws_api_gateway_integration.get_videos_lambda.id,
      aws_api_gateway_integration.post_search_lambda.id,
      aws_api_gateway_integration.get_generate_upload_link_lambda.id,
      aws_api_gateway_integration.get_tasks_lambda.id,
    ]))
  }

  lifecycle {
    create_before_destroy = true
  }

  depends_on = [
    aws_api_gateway_method.get_videos,
    aws_api_gateway_method.post_search,
    aws_api_gateway_method.get_generate_upload_link,
    aws_api_gateway_method.get_tasks,
    aws_api_gateway_method.options_videos,
    aws_api_gateway_method.options_search,
    aws_api_gateway_method.options_generate_upload_link,
    aws_api_gateway_method.options_tasks,
    aws_api_gateway_integration.get_videos_lambda,
    aws_api_gateway_integration.post_search_lambda,
    aws_api_gateway_integration.get_generate_upload_link_lambda,
    aws_api_gateway_integration.get_tasks_lambda,
    aws_api_gateway_integration.options_videos_cors,
    aws_api_gateway_integration.options_search_cors,
    aws_api_gateway_integration.options_generate_upload_link_cors,
    aws_api_gateway_integration.options_tasks_cors,
  ]
}

resource "aws_api_gateway_stage" "api_stage" {
  deployment_id = aws_api_gateway_deployment.api_deployment.id
  rest_api_id   = aws_api_gateway_rest_api.api.id
  stage_name    = var.stage_name
}

# Working version without npm install
# resource "null_resource" "write_api_url_to_env" {
#   triggers = {
#     api_url = local.api_gateway_url
#   }

#   provisioner "local-exec" {
#     command = <<EOT
# echo "NEXT_PUBLIC_API_BASE=${self.triggers.api_url}" > ${path.root}/../playground/.env
# EOT
#   }

#   depends_on = [aws_api_gateway_stage.api_stage]
# }

resource "null_resource" "write_api_url_to_env" {
  triggers = {
    api_url = local.api_gateway_url
  }

  provisioner "local-exec" {
    command = <<EOT
bash -c '
set -e
echo "NEXT_PUBLIC_API_BASE=${self.triggers.api_url}" > ${path.root}/../playground/.env
cd ${path.root}/../playground
npm install
npm run build
'
EOT
  }

  depends_on = [aws_api_gateway_stage.api_stage]
}
