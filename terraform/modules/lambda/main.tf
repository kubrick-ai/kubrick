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

# Lambdas

resource "aws_lambda_function" "kubrick_search" {
  function_name = "kubrick_search"
  role          = var.lambda_iam_role_arn

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
      PGHOST                 = var.db_host
      PGUSER                 = var.db_username
      PGPASSWORD             = var.db_password
      DEFAULT_CLIP_LENGTH    = var.clip_length
      DEFAULT_MIN_SIMILARITY = var.min_similarity
      EMBEDDING_MODEL_NAME   = var.embedding_model
      LOG_LEVEL              = "INFO"
    }
  }

  vpc_config {
    subnet_ids          = var.private_subnet_ids
    security_group_ids  = [var.lambda_sg_id]
  }

  timeout = 900 # 15 minutes timeout
}

