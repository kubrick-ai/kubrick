# Generate a random UUID for unique bucket naming
resource "random_id" "bucket_suffix" {
  byte_length = 8
}

# S3 Bucket with UUID-based naming
resource "aws_s3_bucket" "kubrick_video_upload_bucket" {
  bucket = "kubrick-video-library-${random_id.bucket_suffix.hex}"
  force_destroy = true
}

# S3 Bucket Public Access Block
resource "aws_s3_bucket_public_access_block" "kubrick_video_upload_bucket" {
  bucket = aws_s3_bucket.kubrick_video_upload_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}



# resource "aws_s3_object" "upload_videos" {
#   for_each = fileset("${path.module}/videos", "**")
#   bucket   = aws_s3_bucket.kubrick_video_upload_bucket.id
#   key      = each.key
#   source   = "${path.module}/videos/${each.value}"
#   etag     = filemd5("${path.module}/videos/${each.value}")
  
#   # Set content type based on file extension
#   content_type = lookup({
#     "mp4"  = "video/mp4"
#     "webm" = "video/webm"
#     "avi"  = "video/x-msvideo"
#     "mov"  = "video/quicktime"
#   }, lower(split(".", each.value)[length(split(".", each.value)) - 1]), "application/octet-stream")
# }
