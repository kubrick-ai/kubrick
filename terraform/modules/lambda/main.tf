# Lambda Layers
resource "aws_lambda_layer_version" "vectordb_layer" {
  layer_name              = "vectordb_layer"
  compatible_runtimes     = ["python3.13"]
  compatible_architectures = ["x86_64"]
  filename                = "${path.module}/VectorDBServiceLayer.zip"
  description             = "Module for interacting with the PostgreSQL vector database"
}

resource "aws_lambda_layer_version" "embed_layer" {
  layer_name              = "embed_layer"
  compatible_runtimes     = ["python3.13"]
  compatible_architectures = ["x86_64"]
  filename                = "${path.module}/EmbedLayer.zip"
  description             = "Multi-modal embedding extraction and management module using TwelveLabs API."
}

resource "aws_lambda_layer_version" "config_layer" {
  layer_name              = "config_layer"
  compatible_runtimes     = ["python3.13"]
  compatible_architectures = ["x86_64"]
  filename                = "${path.module}/ConfigLayer.zip"
  description             = "Configuration management module for secrets and database settings."
}

resource "aws_lambda_layer_version" "utils_layer" {
  layer_name              = "utils_layer"
  compatible_runtimes     = ["python3.13"]
  compatible_architectures = ["x86_64"]
  filename                = "${path.module}/ResponseUtilsLayer.zip"
  description             = "Utility module for error handling, S3 presigned URL generation, and API response construction."
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
    protocol    = "-1"  # all protocols
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Lambdas
# kubrick_api_search_handler
resource "aws_lambda_function" "kubrick_api_search_handler" {
  function_name = "kubrick_api_search_handler"
  role          = var.lambda_iam_api_search_handler_role_arn
  runtime       = "python3.13"
  handler       = "lambda_function.lambda_handler"
  filename      = "${path.module}/KubrickSearch.zip" # This is just a placeholder, I don't know the zip's name

  layers = [
    aws_lambda_layer_version.vectordb_layer.arn,
    aws_lambda_layer_version.embed_layer.arn,
    aws_lambda_layer_version.config_layer.arn,
    aws_lambda_layer_version.utils_layer.arn,
  ]

  environment {
    variables = {
      DB_HOST                 = var.db_host
      DB_PASSWORD             = var.db_password
      DEFAULT_CLIP_LENGTH     = var.clip_length
      DEFAULT_MIN_SIMILARITY  = var.min_similarity
      DEFAULT_PAGE_LIMIT      = var.page_limit
      EMBEDDING_MODEL_NAME    = var.embedding_model
      LOG_LEVEL               = "INFO"
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
  filename      = "${path.module}/DeleteHandler.zip" # This is just a placeholder, I don't know the zip's name

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
  filename      = "${path.module}/FetchVideosHandler.zip" # This is just a placeholder, I don't know the zip's name

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
  filename      = "${path.module}/UploadHandler.zip" # This is just a placeholder, I don't know the zip's name

  layers = [
    aws_lambda_layer_version.utils_layer.arn,
  ]

  environment {
    variables = {
      PRESIGNED_URL_EXPIRATION = 900                 # This is a magic number, could prob go to locals
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
  filename      = "${path.module}/FetchTasksHandler.zip" # This is just a placeholder, I don't know the zip's name

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
  filename      = "${path.module}/TaskProducer.zip" # This is just a placeholder, I don't know the zip's name

  layers = [
    aws_lambda_layer_version.vectordb_layer.arn,
    aws_lambda_layer_version.embed_layer.arn,
    aws_lambda_layer_version.config_layer.arn,
  ]

  environment {
    variables = {
      PGHOST                 = var.db_host
      DEFAULT_CLIP_LENGTH    = var.clip_length
      EMBEDDING_MODEL_NAME   = var.embedding_model
      QUEUE_URL              = var.queue_url
    }
  }

  vpc_config {
    subnet_ids         = var.private_subnet_ids
    security_group_ids = [aws_security_group.lambda_private_egress_all_sg.id]
  }

  timeout = 900 # 15 minutes timeout
}

# kubrick_sqs_embedding_task_consumer sadasdsa
resource "aws_lambda_function" "kubrick_sqs_embedding_task_consumer" {
  function_name = "kubrick_sqs_embedding_task_consumer"
  role          = var.lambda_iam_sqs_embedding_task_consumer_role_arn
  runtime       = "python3.13"
  handler       = "lambda_function.lambda_handler"
  filename      = "${path.module}/TaskConsumer.zip" # This is just a placeholder, I don't know the zip's name

  layers = [
    aws_lambda_layer_version.vectordb_layer.arn,
    aws_lambda_layer_version.embed_layer.arn,
    aws_lambda_layer_version.config_layer.arn,
  ]

  # In our AWS one we have twelvelabs api key here, I think it needs to be taken out
  environment {
    variables = {
      DB_HOST                 = var.db_host
      DB_PASSWORD             = var.db_password
    }
  }

  vpc_config {
    subnet_ids         = var.private_subnet_ids
    security_group_ids = [aws_security_group.lambda_private_egress_all_sg.id]
  }

  timeout = 900 # 15 minutes timeout
}