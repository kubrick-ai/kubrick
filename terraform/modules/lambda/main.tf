# Lambda Layers
resource "aws_lambda_layer_version" "vectordb_layer" {
  layer_name               = "vectordb_layer"
  compatible_runtimes      = ["python3.13"]
  compatible_architectures = ["x86_64"]
  filename                 = "${local.base_path}/layers/vector_database_layer/package.zip"
  description              = "Module for interacting with the PostgreSQL vector database"
}

resource "aws_lambda_layer_version" "embed_layer" {
  layer_name               = "embed_layer"
  compatible_runtimes      = ["python3.13"]
  compatible_architectures = ["x86_64"]
  filename                 = "${local.base_path}/layers/embed_service_layer/package.zip"
  description              = "Multi-modal embedding extraction and management module using TwelveLabs API."
}

resource "aws_lambda_layer_version" "config_layer" {
  layer_name               = "config_layer"
  compatible_runtimes      = ["python3.13"]
  compatible_architectures = ["x86_64"]
  filename                 = "${local.base_path}/layers/config_layer/package.zip"
  description              = "Configuration management module for secrets and database settings."
}

resource "aws_lambda_layer_version" "utils_layer" {
  layer_name               = "utils_layer"
  compatible_runtimes      = ["python3.13"]
  compatible_architectures = ["x86_64"]
  filename                 = "${local.base_path}/layers/response_utils_layer/package.zip"
  description              = "Utility module for error handling, S3 presigned URL generation, and API response construction."
}

# Security Group
resource "aws_security_group" "lambda_private_egress_all_sg" {
  name        = "kubrick_api_search_handler_sg"
  description = "Security group for kubrick_api_search_handler Lambda"
  vpc_id      = var.vpc_id

  # Allows all traffic leaving the lambda (outbound traffic)
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1" # all protocols
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Lambdas

# kubrick_db_bootstrap
resource "aws_lambda_function" "kubrick_db_bootstrap" {
  function_name = "kubrick_db_bootstrap"
  role          = var.lambda_iam_db_bootstrap_role_arn
  runtime       = "python3.13"
  handler       = "lambda_function.lambda_handler"
  filename      = "${local.base_path}/db_bootstrap/package.zip"

  layers = [
    aws_lambda_layer_version.config_layer.arn,
  ]

  environment {
    variables = {
      DB_HOST = var.db_host
    }
  }

  vpc_config {
    subnet_ids         = var.private_subnet_ids
    security_group_ids = [aws_security_group.lambda_private_egress_all_sg.id]
  }

  timeout = 300 # 5 minutes timeout
}

resource "null_resource" "invoke_db_bootstrap" {
  depends_on = [
    aws_lambda_function.kubrick_db_bootstrap,
  ]

  provisioner "local-exec" {
    command = <<EOT
      echo "Invoking db_bootstrap lambda..."
      aws lambda invoke \
        --function-name ${aws_lambda_function.kubrick_db_bootstrap.function_name} \
        output.json

      cat output.json
    EOT

  }
}

# kubrick_api_search_handler
resource "aws_lambda_function" "kubrick_api_search_handler" {
  function_name = "kubrick_api_search_handler"
  role          = var.lambda_iam_api_search_handler_role_arn
  runtime       = "python3.13"
  handler       = "lambda_function.lambda_handler"
  filename      = "${local.base_path}/api_search_handler/package.zip"

  layers = [
    aws_lambda_layer_version.vectordb_layer.arn,
    aws_lambda_layer_version.embed_layer.arn,
    aws_lambda_layer_version.config_layer.arn,
    aws_lambda_layer_version.utils_layer.arn,
  ]

  environment {
    variables = {
      DB_HOST                = var.db_host
      DB_PASSWORD            = var.db_password
      DEFAULT_CLIP_LENGTH    = var.clip_length
      DEFAULT_MIN_SIMILARITY = var.min_similarity
      DEFAULT_PAGE_LIMIT     = var.page_limit
      EMBEDDING_MODEL_NAME   = var.embedding_model
      LOG_LEVEL              = "INFO"
    }
  }

  vpc_config {
    subnet_ids         = var.private_subnet_ids
    security_group_ids = [aws_security_group.lambda_private_egress_all_sg.id]
  }

  timeout = 900 # 15 minutes timeout
}

# kubrick_s3_delete_handler
resource "aws_lambda_function" "kubrick_s3_delete_handler" {
  function_name = "kubrick_s3_delete_handler"
  role          = var.lambda_iam_s3_delete_handler_role_arn
  runtime       = "python3.13"
  handler       = "lambda_function.lambda_handler"
  filename      = "${local.base_path}/s3_delete_handler/package.zip"

  layers = [
    aws_lambda_layer_version.vectordb_layer.arn,
    aws_lambda_layer_version.config_layer.arn,
  ]

  environment {
    variables = {
      DB_HOST = var.db_host
    }
  }

  vpc_config {
    subnet_ids         = var.private_subnet_ids
    security_group_ids = [aws_security_group.lambda_private_egress_all_sg.id]
  }

  timeout = 900 # 15 minutes timeout
}

# kubrick_api_fetch_videos_handler
resource "aws_lambda_function" "kubrick_api_fetch_videos_handler" {
  function_name = "kubrick_api_fetch_videos_handler"
  role          = var.lambda_iam_api_fetch_videos_handler_role_arn
  runtime       = "python3.13"
  handler       = "lambda_function.lambda_handler"
  filename      = "${local.base_path}/api_fetch_videos_handler/package.zip"

  layers = [
    aws_lambda_layer_version.vectordb_layer.arn,
    aws_lambda_layer_version.config_layer.arn,
    aws_lambda_layer_version.utils_layer.arn,
  ]

  environment {
    variables = {
      DB_HOST   = var.db_host
      LOG_LEVEL = "INFO"
    }
  }

  vpc_config {
    subnet_ids         = var.private_subnet_ids
    security_group_ids = [aws_security_group.lambda_private_egress_all_sg.id]
  }

  timeout = 900 # 15 minutes timeout
}

# kubrick_api_video_upload_link_handler
resource "aws_lambda_function" "kubrick_api_video_upload_link_handler" {
  function_name = "kubrick_api_video_upload_link_handler"
  role          = var.lambda_iam_api_video_upload_link_handler_role_arn
  runtime       = "python3.13"
  handler       = "lambda_function.lambda_handler"
  filename      = "${local.base_path}/api_video_upload_link_handler/package.zip"

  layers = [
    aws_lambda_layer_version.utils_layer.arn,
  ]

  environment {
    variables = {
      PRESIGNED_URL_EXPIRATION = 900 # This is a magic number, could prob go to locals
      S3_BUCKET_NAME           = var.s3_bucket_name
    }
  }

  vpc_config {
    subnet_ids         = var.private_subnet_ids
    security_group_ids = [aws_security_group.lambda_private_egress_all_sg.id]
  }

  timeout = 900 # 15 minutes timeout
}

# kubrick_api_fetch_tasks_handler
resource "aws_lambda_function" "kubrick_api_fetch_tasks_handler" {
  function_name = "kubrick_api_fetch_tasks_handler"
  role          = var.lambda_iam_api_fetch_tasks_handler_role_arn
  runtime       = "python3.13"
  handler       = "lambda_function.lambda_handler"
  filename      = "${local.base_path}/api_fetch_tasks_handler/package.zip"

  layers = [
    aws_lambda_layer_version.vectordb_layer.arn,
    aws_lambda_layer_version.config_layer.arn,
    aws_lambda_layer_version.utils_layer.arn,
  ]

  environment {
    variables = {
      DB_HOST = var.db_host
    }
  }

  vpc_config {
    subnet_ids         = var.private_subnet_ids
    security_group_ids = [aws_security_group.lambda_private_egress_all_sg.id]
  }

  timeout = 900 # 15 minutes timeout
}

# kubrick_sqs_embedding_task_producer
resource "aws_lambda_function" "kubrick_sqs_embedding_task_producer" {
  function_name = "kubrick_sqs_embedding_task_producer"
  role          = var.lambda_iam_sqs_embedding_task_producer_role_arn
  runtime       = "python3.13"
  handler       = "lambda_function.lambda_handler"
  filename      = "${local.base_path}/sqs_embedding_task_producer/package.zip"

  layers = [
    aws_lambda_layer_version.vectordb_layer.arn,
    aws_lambda_layer_version.embed_layer.arn,
    aws_lambda_layer_version.config_layer.arn,
  ]

  environment {
    variables = {
      # TODO: PGHOST is not consistent
      DB_HOST              = var.db_host
      DEFAULT_CLIP_LENGTH  = var.clip_length
      EMBEDDING_MODEL_NAME = var.embedding_model
      QUEUE_URL            = var.queue_url
    }
  }

  vpc_config {
    subnet_ids         = var.private_subnet_ids
    security_group_ids = [aws_security_group.lambda_private_egress_all_sg.id]
  }

  timeout = 900 # 15 minutes timeout
}

# kubrick_sqs_embedding_task_consumer
resource "aws_lambda_function" "kubrick_sqs_embedding_task_consumer" {
  function_name = "kubrick_sqs_embedding_task_consumer"
  role          = var.lambda_iam_sqs_embedding_task_consumer_role_arn
  runtime       = "python3.13"
  handler       = "lambda_function.lambda_handler"
  filename      = "${local.base_path}/sqs_embedding_task_consumer/package.zip"

  layers = [
    aws_lambda_layer_version.vectordb_layer.arn,
    aws_lambda_layer_version.embed_layer.arn,
    aws_lambda_layer_version.config_layer.arn,
  ]

  # In our AWS one we have twelvelabs api key here, I think it needs to be taken out
  environment {
    variables = {
      DB_HOST     = var.db_host
      DB_PASSWORD = var.db_password
    }
  }

  

  vpc_config {
    subnet_ids         = var.private_subnet_ids
    security_group_ids = [aws_security_group.lambda_private_egress_all_sg.id]
  }

  timeout = 900 # 15 minutes timeout
}

# trigger for the task consumer
resource "aws_lambda_event_source_mapping" "sqs_embedding_task_consumer_trigger" {
  event_source_arn = var.queue_arn
  function_name    = aws_lambda_function.kubrick_sqs_embedding_task_consumer.arn
  batch_size       = 10
  
  function_response_types = ["ReportBatchItemFailures"]
}