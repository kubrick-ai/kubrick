# Generate a random UUID for unique bucket naming
resource "random_id" "bucket_suffix" {
  byte_length = 8
}

# S3 Bucket with UUID-based naming
resource "aws_s3_bucket" "kubrick_video_upload_bucket" {
  bucket        = "kubrick-video-library-${random_id.bucket_suffix.hex}"
  force_destroy = true
}

# S3 Bucket Public Access Block
resource "aws_s3_bucket_public_access_block" "kubrick_video_upload_bucket" {
  bucket = aws_s3_bucket.kubrick_video_upload_bucket.id

  block_public_acls       = true
  block_public_policy     = false
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Default Encryption: Bucket Key = Enabled
resource "aws_s3_bucket_server_side_encryption_configuration" "default" {
  bucket = aws_s3_bucket.kubrick_video_upload_bucket.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }

    bucket_key_enabled = true
  }
}

# Public s3 bucket that hosts the playground frontend static files
resource "aws_s3_bucket" "kubrick_playground_bucket" {
  bucket        = "kubrick-playground-${random_id.bucket_suffix.hex}"
  force_destroy = true
}

resource "aws_s3_bucket_ownership_controls" "kubrick_playground_bucket" {
  bucket = aws_s3_bucket.kubrick_playground_bucket.id
  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}

resource "aws_s3_bucket_policy" "kubrick_playground_bucket" {
  bucket = aws_s3_bucket.kubrick_playground_bucket.id

  depends_on = [aws_s3_bucket_public_access_block.kubrick_playground_bucket]

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Sid       = "PublicReadGetObject",
        Effect    = "Allow",
        Principal = "*",
        Action    = "s3:GetObject",
        Resource  = "${aws_s3_bucket.kubrick_playground_bucket.arn}/*"
      }
    ]
  })
}

resource "aws_s3_bucket_public_access_block" "kubrick_playground_bucket" {
  bucket = aws_s3_bucket.kubrick_playground_bucket.id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

resource "aws_s3_bucket_website_configuration" "kubrick_playground_bucket" {
  bucket = aws_s3_bucket.kubrick_playground_bucket.id

  index_document {
    suffix = "index.html"
  }

  error_document {
    key = "index.html"
  }
}


resource "null_resource" "upload_static_site" {
  depends_on = [
    aws_s3_bucket_website_configuration.kubrick_playground_bucket,
    var.api_gateway_write_done
  ]

  triggers = {
    bucket_name = aws_s3_bucket.kubrick_playground_bucket.bucket
  }

  provisioner "local-exec" {
    command = <<EOT
bash -c '
set -e
cd ${path.root}/../playground
npm run build
aws s3 sync out/ s3://${self.triggers.bucket_name} --delete
'
EOT
  }
}
