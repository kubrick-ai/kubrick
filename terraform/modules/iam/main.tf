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

resource "aws_iam_policy" "sqs_change_message_visibility_policy" {
  name        = "SqsChangeMessageVisibilityPolicy"
  description = "Allows Lambda to change message visibility in SQS queue"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect   = "Allow",
        Action   = ["sqs:ChangeMessageVisibility"],
        Resource = var.embedding_task_queue_arn
      }
    ]
  })
}

resource "aws_iam_policy" "dynamodb_embeddings_cache_access" {
  name        = "DynamoDBEmbeddingsCacheAccess"
  description = "Allows Lambda to read/write to DynamoDB embeddings cache table"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ],
        Resource = [
          var.embeddings_cache_table_arn,
          "${var.embeddings_cache_table_arn}/index/*"
        ]
      }
    ]
  })
}

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
