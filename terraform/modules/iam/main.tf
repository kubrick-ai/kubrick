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
          # "s3:GetObject",
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


#####
resource "aws_iam_policy" "secrets_access" {
  name        = "SecretsAccessPolicy"
  description = "Allows Lambda to retrieve secret from Secrets Manager"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect   = "Allow",
        Action   = ["secretsmanager:GetSecretValue"],
        Resource = var.secret_arn
      }
    ]
  })
}

resource "aws_iam_policy" "lambda_vpc_access" {
  name   = "lambda-vpc-access"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect   = "Allow",
        Action   = [
          "ec2:CreateNetworkInterface",
          "ec2:DescribeNetworkInterfaces",
          "ec2:DeleteNetworkInterface"
        ],
        Resource = "*"
      }
    ]
  })
}

# Once this is merged I can extract the ARN from the SQS module
# resource "aws_iam_policy" "sqs_send_message_policy" {
#   name        = "SqsSendMessageOnlyPolicy"
#   description = "Allows Lambda to send messages to a specific SQS queue"

#   policy = jsonencode({
#     Version = "2012-10-17",
#     Statement = [
#       {
#         Effect   = "Allow",
#         Action   = ["sqs:SendMessage"],
#         Resource = var.embedding_task_queue_arn
#       }
#     ]
#   })
# }

# Creates the IAM Role for each lambda
resource "aws_iam_role" "lambda_roles" {
  for_each           = local.lambda_roles
  name               = each.key
  assume_role_policy = local.lambda_assume_role_policy

  tags = {
    Name        = each.key
    Environment = var.environment
    Purpose     = each.value.purpose
  }
}

# This attaches policies to all IAM Lambda roles
resource "aws_iam_role_policy_attachment" "lambda_role_policy_attachments" {
  for_each = {
    for pair in flatten([
      for role_name, policies in local.lambda_role_policies : [
        for policy_key in policies : {
          key        = "${role_name}_${policy_key}"
          role       = role_name
          policy_arn = local.all_policy_arns[policy_key]
        }
      ]
    ]) : pair.key => {
      role       = pair.role
      policy_arn = pair.policy_arn
    }
  }

  role       = aws_iam_role.lambda_roles[each.value.role].name
  policy_arn = each.value.policy_arn
}


