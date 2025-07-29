locals {
  # AWS-managed policy ARNs
  managed_policy_arns = {
    s3_full_access            = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
    s3_readonly_access        = "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"
    sqs_full_access           = "arn:aws:iam::aws:policy/AmazonSQSFullAccess" # Delete this once having access to SQS
    lambda_basic_execution    = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
    lambda_sqs_execution      = "arn:aws:iam::aws:policy/service-role/AWSLambdaSQSQueueExecutionRole"
  }

  # Trust policy for Lambda roles
  lambda_assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect = "Allow",
      Principal = {
        Service = "lambda.amazonaws.com"
      },
      Action = "sts:AssumeRole"
    }]
  })

  # The IAM roles for lambdas
  lambda_roles = {
    kubrick_db_bootstrap                  = { purpose = "Initialises database schema" }
    kubrick_s3_delete_handler             = { purpose = "Handles S3 file deletions" }
    kubrick_api_search_handler            = { purpose = "Search API Lambda" }
    kubrick_api_fetch_videos_handler      = { purpose = "Fetches videos from DB" }
    kubrick_api_video_upload_link_handler = { purpose = "Generates S3 pre-signed URL" }
    kubrick_api_fetch_tasks_handler       = { purpose = "Fetches embedding tasks from DB" }
    kubrick_sqs_embedding_task_producer   = { purpose = "Sends embedding tasks to SQS" }
    kubrick_sqs_embedding_task_consumer   = { purpose = "Consumes embedding tasks from SQS" }
  }

  # IAM Roles and their policies
  lambda_role_policies = {
    kubrick_db_bootstrap                  = ["lambda_basic_execution", "secrets_access"]
    kubrick_s3_delete_handler             = ["s3_full_access", "lambda_basic_execution", "secrets_access"]
    kubrick_api_search_handler            = ["s3_readonly_access", "lambda_basic_execution", "secrets_access"]
    kubrick_api_fetch_videos_handler      = ["s3_readonly_access", "lambda_basic_execution", "secrets_access"]
    kubrick_api_video_upload_link_handler = ["s3_full_access", "lambda_basic_execution"]
    kubrick_api_fetch_tasks_handler       = ["lambda_basic_execution", "secrets_access"]
    kubrick_sqs_embedding_task_producer   = ["s3_full_access", "lambda_basic_execution", "secrets_access", "sqs_full_access"]
    kubrick_sqs_embedding_task_consumer   = ["lambda_sqs_execution", "secrets_access"]
  }

  # Merge managed + custom policy ARNs
  all_policy_arns = merge(
    local.managed_policy_arns,
    {
      secrets_access = aws_iam_policy.secrets_access.arn
    }
  )
}
