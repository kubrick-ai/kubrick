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