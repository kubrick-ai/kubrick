# S3 Lambda  notification kubrick_sqs_embedding_task_producer
resource "aws_s3_bucket_notification" "bucket_notification" {
  bucket = aws_s3_bucket.kubrick_video_upload_bucket.id

  lambda_function {
    lambda_function_arn = var.kubrick_sqs_embedding_task_producer_arn # Pass this from main.tf
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "videos/"  # Optional: only trigger for files in videos/ folder
    filter_suffix       = ".mp4"    # Optional: only trigger for .mp4 files
  }

  depends_on = [aws_lambda_permission.s3_invoke_lambda]
}