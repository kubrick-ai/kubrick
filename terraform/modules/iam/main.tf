resource "aws_iam_role" "lambda_s3_readonly" {
  name = "kubrick-lambda-s3-readonly-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "kubrick-lambda-s3-readonly-role"
    Environment = var.environment
    Purpose     = "Lambda S3 Read-Only Access"
  }
}

resource "aws_iam_policy" "lambda_s3_readonly" {
  name        = "kubrick-lambda-s3-readonly-policy"
  description = "Policy for Lambda functions to have read-only access to S3 bucket"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket",
          "s3:GetBucketLocation"
        ]
        Resource = [
          var.s3_bucket_arn,
          "${var.s3_bucket_arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })

  tags = {
    Name        = "kubrick-lambda-s3-readonly-policy"
    Environment = var.environment
  }
}

# Attach Read-Only Policy to Read-Only Role
resource "aws_iam_role_policy_attachment" "lambda_s3_readonly" {
  role       = aws_iam_role.lambda_s3_readonly.name
  policy_arn = aws_iam_policy.lambda_s3_readonly.arn
}

resource "aws_iam_role" "lambda_s3_full_access" {
  name = "kubrick-lambda-s3-full-access-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "kubrick-lambda-s3-full-access-role"
    Environment = var.environment
    Purpose     = "Lambda S3 Full Access"
  }
}

resource "aws_iam_policy" "lambda_s3_full_access" {
  name        = "kubrick-lambda-s3-full-access-policy"
  description = "Policy for Lambda functions to have full access to S3 bucket"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket",
          "s3:GetBucketLocation",
          "s3:GetObjectVersion",
          "s3:DeleteObjectVersion",
          "s3:ListBucketVersions"
        ]
        Resource = [
          var.s3_bucket_arn,
          "${var.s3_bucket_arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })

  tags = {
    Name        = "kubrick-lambda-s3-full-access-policy"
    Environment = var.environment
  }
}

# Attach Full Access Policy to Full Access Role
resource "aws_iam_role_policy_attachment" "lambda_s3_full_access" {
  role       = aws_iam_role.lambda_s3_full_access.name
  policy_arn = aws_iam_policy.lambda_s3_full_access.arn
}
