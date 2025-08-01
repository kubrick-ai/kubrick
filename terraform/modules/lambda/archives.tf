
resource "null_resource" "build_config_layer" {
  triggers = {
    deps_hash   = filemd5("${local.base_path}/layers/config_layer/pyproject.toml")
    source_hash = filemd5("${local.base_path}/layers/config_layer/config.py")
  }

  provisioner "local-exec" {
    command     = local.build_script
    working_dir = "${local.base_path}/layers/config_layer"
  }
}

resource "null_resource" "build_embed_layer" {
  triggers = {
    deps_hash   = filemd5("${local.base_path}/layers/embed_service_layer/pyproject.toml")
    source_hash = filemd5("${local.base_path}/layers/embed_service_layer/embed_service.py")
  }

  provisioner "local-exec" {
    command     = local.build_script
    working_dir = "${local.base_path}/layers/embed_service_layer"
  }
}

resource "null_resource" "build_response_utils_layer" {
  triggers = {
    deps_hash   = filemd5("${local.base_path}/layers/response_utils_layer/pyproject.toml")
    source_hash = filemd5("${local.base_path}/layers/response_utils_layer/response_utils.py")
  }

  provisioner "local-exec" {
    command     = local.build_script
    working_dir = "${local.base_path}/layers/response_utils_layer"
  }
}

resource "null_resource" "build_s3_utils_layer" {
  triggers = {
    deps_hash   = filemd5("${local.base_path}/layers/s3_utils_layer/pyproject.toml")
    source_hash = filemd5("${local.base_path}/layers/s3_utils_layer/s3_utils.py")
  }

  provisioner "local-exec" {
    command     = local.build_script
    working_dir = "${local.base_path}/layers/s3_utils_layer"
  }
}


resource "null_resource" "build_vector_database_layer" {
  triggers = {
    deps_hash   = filemd5("${local.base_path}/layers/vector_database_layer/pyproject.toml")
    source_hash = filemd5("${local.base_path}/layers/vector_database_layer/vector_db_service.py")
  }

  provisioner "local-exec" {
    command     = local.build_script
    working_dir = "${local.base_path}/layers/vector_database_layer"
  }
}

resource "null_resource" "build_db_bootstrap" {
  triggers = {
    deps_hash   = filemd5("${local.base_path}/db_bootstrap/pyproject.toml")
    source_hash = filemd5("${local.base_path}/db_bootstrap/lambda_function.py")
    schema_hash = filemd5("${local.base_path}/db_bootstrap/schema.sql")
  }

  provisioner "local-exec" {
    command     = local.build_script
    working_dir = "${local.base_path}/db_bootstrap"
  }
}

resource "null_resource" "build_api_fetch_tasks_handler" {
  triggers = {
    deps_hash   = filemd5("${local.base_path}/api_fetch_tasks_handler/pyproject.toml")
    source_hash = filemd5("${local.base_path}/api_fetch_tasks_handler/lambda_function.py")
  }

  provisioner "local-exec" {
    command     = local.build_script
    working_dir = "${local.base_path}/api_fetch_tasks_handler"
  }
}

resource "null_resource" "build_api_fetch_videos_handler" {
  triggers = {
    deps_hash   = filemd5("${local.base_path}/api_fetch_videos_handler/pyproject.toml")
    source_hash = filemd5("${local.base_path}/api_fetch_videos_handler/lambda_function.py")
  }

  provisioner "local-exec" {
    command     = local.build_script
    working_dir = "${local.base_path}/api_fetch_videos_handler"
  }
}

resource "null_resource" "build_api_search_handler" {
  triggers = {
    deps_hash       = filemd5("${local.base_path}/api_search_handler/pyproject.toml")
    lambda_hash     = filemd5("${local.base_path}/api_search_handler/lambda_function.py")
    controller_hash = filemd5("${local.base_path}/api_search_handler/search_controller.py")
    errors_hash     = filemd5("${local.base_path}/api_search_handler/search_errors.py")
  }

  provisioner "local-exec" {
    command     = local.build_script
    working_dir = "${local.base_path}/api_search_handler"
  }
}

resource "null_resource" "build_api_video_upload_link_handler" {
  triggers = {
    deps_hash   = filemd5("${local.base_path}/api_video_upload_link_handler/pyproject.toml")
    source_hash = filemd5("${local.base_path}/api_video_upload_link_handler/lambda_function.py")
  }

  provisioner "local-exec" {
    command     = local.build_script
    working_dir = "${local.base_path}/api_video_upload_link_handler"
  }
}

resource "null_resource" "build_s3_delete_handler" {
  triggers = {
    deps_hash   = filemd5("${local.base_path}/s3_delete_handler/pyproject.toml")
    lambda_hash = filemd5("${local.base_path}/s3_delete_handler/lambda_function.py")
    utils_hash  = filemd5("${local.base_path}/s3_delete_handler/utils.py")
  }

  provisioner "local-exec" {
    command     = local.build_script
    working_dir = "${local.base_path}/s3_delete_handler"
  }
}

resource "null_resource" "build_sqs_embedding_task_producer" {
  triggers = {
    deps_hash   = filemd5("${local.base_path}/sqs_embedding_task_producer/pyproject.toml")
    lambda_hash = filemd5("${local.base_path}/sqs_embedding_task_producer/lambda_function.py")
    utils_hash  = filemd5("${local.base_path}/sqs_embedding_task_producer/utils.py")
  }

  provisioner "local-exec" {
    command     = local.build_script
    working_dir = "${local.base_path}/sqs_embedding_task_producer"
  }
}

resource "null_resource" "build_sqs_embedding_task_consumer" {
  triggers = {
    deps_hash   = filemd5("${local.base_path}/sqs_embedding_task_consumer/pyproject.toml")
    source_hash = filemd5("${local.base_path}/sqs_embedding_task_consumer/lambda_function.py")
  }

  provisioner "local-exec" {
    command     = local.build_script
    working_dir = "${local.base_path}/sqs_embedding_task_consumer"
  }
}

# Lambda Layers
data "archive_file" "config_layer" {
  type        = "zip"
  output_path = "${local.base_path}/layers/config_layer/package.zip"
  source_dir  = "${local.base_path}/layers/config_layer/package"
  excludes    = ["__pycache__", "*.pyc", "*.DS_Store"]

  depends_on = [null_resource.build_config_layer]
}

data "archive_file" "embed_layer" {
  type        = "zip"
  output_path = "${local.base_path}/layers/embed_service_layer/package.zip"
  source_dir  = "${local.base_path}/layers/embed_service_layer/package"
  excludes    = ["__pycache__", "*.pyc", "*.DS_Store"]

  depends_on = [null_resource.build_embed_layer]
}

data "archive_file" "response_utils_layer" {
  type        = "zip"
  output_path = "${local.base_path}/layers/response_utils_layer/package.zip"
  source_dir  = "${local.base_path}/layers/response_utils_layer/package"
  excludes    = ["__pycache__", "*.pyc", "*.DS_Store"]

  depends_on = [null_resource.build_response_utils_layer]
}

data "archive_file" "s3_utils_layer" {
  type        = "zip"
  output_path = "${local.base_path}/layers/s3_utils_layer/package.zip"
  source_dir  = "${local.base_path}/layers/s3_utils_layer/package"
  excludes    = ["__pycache__", "*.pyc", "*.DS_Store"]

  depends_on = [null_resource.build_s3_utils_layer]
}

data "archive_file" "vector_database_layer" {
  type        = "zip"
  output_path = "${local.base_path}/layers/vector_database_layer/package.zip"
  source_dir  = "${local.base_path}/layers/vector_database_layer/package"
  excludes    = ["__pycache__", "*.pyc", "*.DS_Store"]

  depends_on = [null_resource.build_vector_database_layer]
}

# Lambda Functions
data "archive_file" "db_bootstrap" {
  type        = "zip"
  output_path = "${local.base_path}/db_bootstrap/package.zip"
  source_dir  = "${local.base_path}/db_bootstrap/package"
  excludes    = ["__pycache__", "*.pyc", "*.DS_Store"]

  depends_on = [null_resource.build_db_bootstrap]
}

data "archive_file" "api_fetch_tasks_handler" {
  type        = "zip"
  output_path = "${local.base_path}/api_fetch_tasks_handler/package.zip"
  source_dir  = "${local.base_path}/api_fetch_tasks_handler/package"
  excludes    = ["__pycache__", "*.pyc", "*.DS_Store"]

  depends_on = [null_resource.build_api_fetch_tasks_handler]
}

data "archive_file" "api_fetch_videos_handler" {
  type        = "zip"
  output_path = "${local.base_path}/api_fetch_videos_handler/package.zip"
  source_dir  = "${local.base_path}/api_fetch_videos_handler/package"
  excludes    = ["__pycache__", "*.pyc", "*.DS_Store"]

  depends_on = [null_resource.build_api_fetch_videos_handler]
}

data "archive_file" "api_search_handler" {
  type        = "zip"
  output_path = "${local.base_path}/api_search_handler/package.zip"
  source_dir  = "${local.base_path}/api_search_handler/package"
  excludes    = ["__pycache__", "*.pyc", "*.DS_Store"]

  depends_on = [null_resource.build_api_search_handler]
}

data "archive_file" "api_video_upload_link_handler" {
  type        = "zip"
  output_path = "${local.base_path}/api_video_upload_link_handler/package.zip"
  source_dir  = "${local.base_path}/api_video_upload_link_handler/package"
  excludes    = ["__pycache__", "*.pyc", "*.DS_Store"]

  depends_on = [null_resource.build_api_video_upload_link_handler]
}

data "archive_file" "s3_delete_handler" {
  type        = "zip"
  output_path = "${local.base_path}/s3_delete_handler/package.zip"
  source_dir  = "${local.base_path}/s3_delete_handler/package"
  excludes    = ["__pycache__", "*.pyc", "*.DS_Store"]

  depends_on = [null_resource.build_s3_delete_handler]
}

data "archive_file" "sqs_embedding_task_producer" {
  type        = "zip"
  output_path = "${local.base_path}/sqs_embedding_task_producer/package.zip"
  source_dir  = "${local.base_path}/sqs_embedding_task_producer/package"
  excludes    = ["__pycache__", "*.pyc", "*.DS_Store"]

  depends_on = [null_resource.build_sqs_embedding_task_producer]
}

data "archive_file" "sqs_embedding_task_consumer" {
  type        = "zip"
  output_path = "${local.base_path}/sqs_embedding_task_consumer/package.zip"
  source_dir  = "${local.base_path}/sqs_embedding_task_consumer/package"
  excludes    = ["__pycache__", "*.pyc", "*.DS_Store"]

  depends_on = [null_resource.build_sqs_embedding_task_consumer]
}

