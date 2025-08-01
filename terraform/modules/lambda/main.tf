# Lambda Layers
resource "aws_lambda_layer_version" "vector_database_layer" {
  layer_name               = "vector_database_layer"
  compatible_runtimes      = ["python3.13"]
  compatible_architectures = ["x86_64"]
  filename                 = data.archive_file.vector_database_layer.output_path
  source_code_hash         = data.archive_file.vector_database_layer.output_base64sha256
  description              = "Module for interacting with the PostgreSQL vector database"
}

resource "aws_lambda_layer_version" "embed_layer" {
  layer_name               = "embed_layer"
  compatible_runtimes      = ["python3.13"]
  compatible_architectures = ["x86_64"]
  filename                 = data.archive_file.embed_layer.output_path
  source_code_hash         = data.archive_file.embed_layer.output_base64sha256
  description              = "Multi-modal embedding extraction and management module using TwelveLabs API."
}

resource "aws_lambda_layer_version" "config_layer" {
  layer_name               = "config_layer"
  compatible_runtimes      = ["python3.13"]
  compatible_architectures = ["x86_64"]
  filename                 = data.archive_file.config_layer.output_path
  source_code_hash         = data.archive_file.config_layer.output_base64sha256
  description              = "Configuration management module for secrets and database settings."
}

resource "aws_lambda_layer_version" "response_utils_layer" {
  layer_name               = "response_utils_layer"
  compatible_runtimes      = ["python3.13"]
  compatible_architectures = ["x86_64"]
  filename                 = data.archive_file.response_utils_layer.output_path
  source_code_hash         = data.archive_file.response_utils_layer.output_base64sha256
  description              = "Utility module for error handling and API response construction."
}

resource "aws_lambda_layer_version" "s3_utils_layer" {
  layer_name               = "s3_utils_layer"
  compatible_runtimes      = ["python3.13"]
  compatible_architectures = ["x86_64"]
  filename                 = data.archive_file.s3_utils_layer.output_path
  source_code_hash         = data.archive_file.s3_utils_layer.output_base64sha256
  description              = "Utility module for S3 operations, including presigned URL generation."
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
  function_name    = "kubrick_db_bootstrap"
  role             = var.lambda_iam_db_bootstrap_role_arn
  runtime          = "python3.13"
  handler          = "lambda_function.lambda_handler"
  filename         = data.archive_file.db_bootstrap.output_path
  source_code_hash = data.archive_file.db_bootstrap.output_base64sha256

  layers = [
    aws_lambda_layer_version.config_layer.arn,
  ]

  environment {
    variables = {
      DB_HOST     = var.db_host
      SECRET_NAME = var.secrets_manager_name
      LOG_LEVEL   = "INFO"
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
        --region ${var.aws_region} \
        --profile ${var.aws_profile} \
        --function-name ${aws_lambda_function.kubrick_db_bootstrap.function_name} \
        output.json

      cat output.json
    EOT

  }
}

# kubrick_api_search_handler
resource "aws_lambda_function" "kubrick_api_search_handler" {
  function_name    = "kubrick_api_search_handler"
  role             = var.lambda_iam_api_search_handler_role_arn
  runtime          = "python3.13"
  handler          = "lambda_function.lambda_handler"
  filename         = data.archive_file.api_search_handler.output_path
  source_code_hash = data.archive_file.api_search_handler.output_base64sha256

  layers = [
    aws_lambda_layer_version.vector_database_layer.arn,
    aws_lambda_layer_version.embed_layer.arn,
    aws_lambda_layer_version.config_layer.arn,
    aws_lambda_layer_version.response_utils_layer.arn,
    aws_lambda_layer_version.s3_utils_layer.arn,
  ]

  environment {
    variables = {
      DB_HOST                     = var.db_host
      DB_PASSWORD                 = var.db_password
      DEFAULT_CLIP_LENGTH         = var.clip_length
      DEFAULT_MIN_SIMILARITY      = var.min_similarity
      DEFAULT_PAGE_LIMIT          = var.page_limit
      EMBEDDING_MODEL_NAME        = var.embedding_model
      QUERY_MEDIA_FILE_SIZE_LIMIT = var.query_media_file_size_limit
      SECRET_NAME                 = var.secrets_manager_name
      LOG_LEVEL                   = "INFO"
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
  function_name    = "kubrick_s3_delete_handler"
  role             = var.lambda_iam_s3_delete_handler_role_arn
  runtime          = "python3.13"
  handler          = "lambda_function.lambda_handler"
  filename         = data.archive_file.s3_delete_handler.output_path
  source_code_hash = data.archive_file.s3_delete_handler.output_base64sha256

  layers = [
    aws_lambda_layer_version.vector_database_layer.arn,
    aws_lambda_layer_version.config_layer.arn,
  ]

  environment {
    variables = {
      DB_HOST     = var.db_host
      SECRET_NAME = var.secrets_manager_name
      LOG_LEVEL   = "INFO"
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
  function_name    = "kubrick_api_fetch_videos_handler"
  role             = var.lambda_iam_api_fetch_videos_handler_role_arn
  runtime          = "python3.13"
  handler          = "lambda_function.lambda_handler"
  filename         = data.archive_file.api_fetch_videos_handler.output_path
  source_code_hash = data.archive_file.api_fetch_videos_handler.output_base64sha256

  layers = [
    aws_lambda_layer_version.vector_database_layer.arn,
    aws_lambda_layer_version.config_layer.arn,
    aws_lambda_layer_version.response_utils_layer.arn,
    aws_lambda_layer_version.s3_utils_layer.arn,
  ]

  environment {
    variables = {
      DB_HOST              = var.db_host
      PRESIGNED_URL_EXPIRY = var.presigned_url_expiry
      SECRET_NAME          = var.secrets_manager_name
      LOG_LEVEL            = "INFO"
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
  function_name    = "kubrick_api_video_upload_link_handler"
  role             = var.lambda_iam_api_video_upload_link_handler_role_arn
  runtime          = "python3.13"
  handler          = "lambda_function.lambda_handler"
  filename         = data.archive_file.api_video_upload_link_handler.output_path
  source_code_hash = data.archive_file.api_video_upload_link_handler.output_base64sha256

  layers = [
    aws_lambda_layer_version.response_utils_layer.arn,
    aws_lambda_layer_version.s3_utils_layer.arn
  ]

  environment {
    variables = {
      PRESIGNED_URL_TTL = var.presigned_url_ttl
      S3_BUCKET_NAME    = var.s3_bucket_name
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
  function_name    = "kubrick_api_fetch_tasks_handler"
  role             = var.lambda_iam_api_fetch_tasks_handler_role_arn
  runtime          = "python3.13"
  handler          = "lambda_function.lambda_handler"
  filename         = data.archive_file.api_fetch_tasks_handler.output_path
  source_code_hash = data.archive_file.api_fetch_tasks_handler.output_base64sha256

  layers = [
    aws_lambda_layer_version.vector_database_layer.arn,
    aws_lambda_layer_version.config_layer.arn,
    aws_lambda_layer_version.response_utils_layer.arn,
  ]

  environment {
    variables = {
      DB_HOST            = var.db_host
      DEFAULT_TASK_LIMIT = var.default_task_limit
      MAX_TASK_LIMIT     = var.max_task_limit
      DEFAULT_TASK_PAGE  = var.default_task_page
      SECRET_NAME        = var.secrets_manager_name
      LOG_LEVEL          = "INFO"
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
  function_name    = "kubrick_sqs_embedding_task_producer"
  role             = var.lambda_iam_sqs_embedding_task_producer_role_arn
  runtime          = "python3.13"
  handler          = "lambda_function.lambda_handler"
  filename         = data.archive_file.sqs_embedding_task_producer.output_path
  source_code_hash = data.archive_file.sqs_embedding_task_producer.output_base64sha256

  layers = [
    aws_lambda_layer_version.vector_database_layer.arn,
    aws_lambda_layer_version.embed_layer.arn,
    aws_lambda_layer_version.config_layer.arn,
    aws_lambda_layer_version.s3_utils_layer.arn,
  ]

  environment {
    variables = {
      DB_HOST                = var.db_host
      DEFAULT_CLIP_LENGTH    = var.clip_length
      EMBEDDING_MODEL_NAME   = var.embedding_model
      QUEUE_URL              = var.queue_url
      PRESIGNED_URL_TTL      = var.presigned_url_ttl
      FILE_CHECK_RETRIES     = var.file_check_retries
      FILE_CHECK_DELAY_SEC   = var.file_check_delay_sec
      VIDEO_EMBEDDING_SCOPES = jsonencode(var.video_embedding_scopes)
      SECRET_NAME            = var.secrets_manager_name
      LOG_LEVEL              = "INFO"
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
  function_name    = "kubrick_sqs_embedding_task_consumer"
  role             = var.lambda_iam_sqs_embedding_task_consumer_role_arn
  runtime          = "python3.13"
  handler          = "lambda_function.lambda_handler"
  filename         = data.archive_file.sqs_embedding_task_consumer.output_path
  source_code_hash = data.archive_file.sqs_embedding_task_consumer.output_base64sha256

  layers = [
    aws_lambda_layer_version.vector_database_layer.arn,
    aws_lambda_layer_version.embed_layer.arn,
    aws_lambda_layer_version.config_layer.arn,
  ]

  # In our AWS one we have twelvelabs api key here, I think it needs to be taken out
  environment {
    variables = {
      DB_HOST     = var.db_host
      DB_PASSWORD = var.db_password
      SECRET_NAME = var.secrets_manager_name
      LOG_LEVEL   = "INFO"
    }
  }

  vpc_config {
    subnet_ids         = var.private_subnet_ids
    security_group_ids = [aws_security_group.lambda_private_egress_all_sg.id]
  }

  timeout = 30 # 15 minutes timeout

}

# trigger for the task consumer
resource "aws_lambda_event_source_mapping" "sqs_embedding_task_consumer_trigger" {
  event_source_arn = var.queue_arn
  function_name    = aws_lambda_function.kubrick_sqs_embedding_task_consumer.arn
  batch_size       = 10

  function_response_types = ["ReportBatchItemFailures"]
}
