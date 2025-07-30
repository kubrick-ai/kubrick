# S3 Lambda notification for kubrick_sqs_embedding_task_producer and kubrick_s3_delete_handler_function
resource "aws_s3_bucket_notification" "bucket_notification" {
  bucket = var.bucket_id

  lambda_function {
    lambda_function_arn = var.create_lambda_function_arn
    events              = ["s3:ObjectCreated:*"]
    # filter_prefix       = "videos/"  # Optional: only trigger for files in videos/ folder
  }

  lambda_function {
    lambda_function_arn = var.delete_lambda_function_arn
    events              = ["s3:ObjectRemoved:*"]
  }

  depends_on = [aws_lambda_permission.s3_invoke_lambda_on_create, aws_lambda_permission.s3_invoke_lambda_on_delete]
}

# Lambda permission that was moved from S3 module
resource "aws_lambda_permission" "s3_invoke_lambda_on_create" {
  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = var.create_lambda_function_name
  principal     = "s3.amazonaws.com"
  source_arn    = var.bucket_arn
}

resource "aws_lambda_permission" "s3_invoke_lambda_on_delete" {
  statement_id  = "AllowExecutionFromS3BucketOnDelete"
  action        = "lambda:InvokeFunction"
  function_name = var.delete_lambda_function_name
  principal     = "s3.amazonaws.com"
  source_arn    = var.bucket_arn
}