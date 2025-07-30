# S3 Lambda notification kubrick_sqs_embedding_task_producer
resource "aws_s3_bucket_notification" "bucket_notification" {
  bucket = var.bucket_name

  lambda_function {
    lambda_function_arn = var.lambda_function_arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "videos/"  # Optional: only trigger for files in videos/ folder
    filter_suffix       = ".mp4"    # Optional: only trigger for .mp4 files
  }

  depends_on = [aws_lambda_permission.s3_invoke_lambda]
}

# Lambda permission that was moved from S3 module
resource "aws_lambda_permission" "s3_invoke_lambda" {
  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = var.lambda_function_arn
  principal     = "s3.amazonaws.com"
  source_arn    = "arn:aws:s3:::${var.bucket_name}"
}
