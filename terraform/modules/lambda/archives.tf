# Archive data sources for Lambda Layers
resource "null_resource" "install_deps_vectordb" {
  triggers = {
    source_hash = filemd5("${local.base_path}/layers/vector_database_layer/vector_db_service.py")
    deps_hash   = filemd5("${local.base_path}/layers/vector_database_layer/pyproject.toml")
  }

  provisioner "local-exec" {
    command     = "./build-package.sh"
    working_dir = "${local.base_path}/layers/vector_database_layer"
  }
}

data "archive_file" "vectordb_layer" {
  depends_on  = [null_resource.install_deps_vectordb]
  type        = "zip"
  output_path = "${local.base_path}/layers/vector_database_layer/package.zip"
  source_dir  = "${local.base_path}/layers/vector_database_layer/python"
  excludes    = ["__pycache__", "*.pyc", "*.DS_Store"]
}

resource "null_resource" "install_deps_embed" {
  triggers = {
    source_hash = filemd5("${local.base_path}/layers/embed_service_layer/embed_service.py")
    deps_hash   = filemd5("${local.base_path}/layers/embed_service_layer/pyproject.toml")
  }

  provisioner "local-exec" {
    command     = "./build-package.sh"
    working_dir = "${local.base_path}/layers/embed_service_layer"
  }
}

data "archive_file" "embed_layer" {
  depends_on  = [null_resource.install_deps_embed]
  type        = "zip"
  output_path = "${local.base_path}/layers/embed_service_layer/package.zip"
  source_dir  = "${local.base_path}/layers/embed_service_layer/python"
  excludes    = ["__pycache__", "*.pyc", "*.DS_Store"]
}

resource "null_resource" "install_deps_config" {
  triggers = {
    source_hash = filemd5("${local.base_path}/layers/config_layer/config.py")
    deps_hash   = filemd5("${local.base_path}/layers/config_layer/pyproject.toml")
  }

  provisioner "local-exec" {
    command     = "./build-package.sh"
    working_dir = "${local.base_path}/layers/config_layer"
  }
}

data "archive_file" "config_layer" {
  depends_on  = [null_resource.install_deps_config]
  type        = "zip"
  output_path = "${local.base_path}/layers/config_layer/package.zip"
  source_dir  = "${local.base_path}/layers/config_layer/python"
  excludes    = ["__pycache__", "*.pyc", "*.DS_Store"]
}

resource "null_resource" "install_deps_utils" {
  triggers = {
    source_hash = filemd5("${local.base_path}/layers/response_utils_layer/response_utils.py")
    deps_hash   = filemd5("${local.base_path}/layers/response_utils_layer/pyproject.toml")
  }

  provisioner "local-exec" {
    command     = "./build-package.sh"
    working_dir = "${local.base_path}/layers/response_utils_layer"
  }
}

data "archive_file" "utils_layer" {
  depends_on  = [null_resource.install_deps_utils]
  type        = "zip"
  output_path = "${local.base_path}/layers/response_utils_layer/package.zip"
  source_dir  = "${local.base_path}/layers/response_utils_layer/python"
  excludes    = ["__pycache__", "*.pyc", "*.DS_Store"]
}

# Archive data sources for Lambda Functions
resource "null_resource" "install_deps_db_bootstrap" {
  triggers = {
    source_hash = filemd5("${local.base_path}/db_bootstrap/lambda_function.py")
    schema_hash = filemd5("${local.base_path}/db_bootstrap/schema.sql")
    deps_hash   = filemd5("${local.base_path}/db_bootstrap/pyproject.toml")
  }

  provisioner "local-exec" {
    command     = "./build-package.sh"
    working_dir = "${local.base_path}/db_bootstrap"
  }
}

data "archive_file" "db_bootstrap" {
  depends_on  = [null_resource.install_deps_db_bootstrap]
  type        = "zip"
  output_path = "${local.base_path}/db_bootstrap/package.zip"
  source_dir  = "${local.base_path}/db_bootstrap/package"
  excludes    = ["__pycache__", "*.pyc", "*.DS_Store"]
}

resource "null_resource" "install_deps_api_search_handler" {
  triggers = {
    lambda_hash     = filemd5("${local.base_path}/api_search_handler/lambda_function.py")
    controller_hash = filemd5("${local.base_path}/api_search_handler/search_controller.py")
    errors_hash     = filemd5("${local.base_path}/api_search_handler/search_errors.py")
    deps_hash       = filemd5("${local.base_path}/api_search_handler/pyproject.toml")
  }

  provisioner "local-exec" {
    command     = "./build-package.sh"
    working_dir = "${local.base_path}/api_search_handler"
  }
}

data "archive_file" "api_search_handler" {
  depends_on  = [null_resource.install_deps_api_search_handler]
  type        = "zip"
  output_path = "${local.base_path}/api_search_handler/package.zip"
  source_dir  = "${local.base_path}/api_search_handler/package"
  excludes    = ["__pycache__", "*.pyc", "*.DS_Store"]
}

resource "null_resource" "install_deps_s3_delete_handler" {
  triggers = {
    lambda_hash = filemd5("${local.base_path}/s3_delete_handler/lambda_function.py")
    utils_hash  = filemd5("${local.base_path}/s3_delete_handler/utils.py")
    deps_hash   = filemd5("${local.base_path}/s3_delete_handler/pyproject.toml")
  }

  provisioner "local-exec" {
    command     = "./build-package.sh"
    working_dir = "${local.base_path}/s3_delete_handler"
  }
}

data "archive_file" "s3_delete_handler" {
  depends_on  = [null_resource.install_deps_s3_delete_handler]
  type        = "zip"
  output_path = "${local.base_path}/s3_delete_handler/package.zip"
  source_dir  = "${local.base_path}/s3_delete_handler/package"
  excludes    = ["__pycache__", "*.pyc", "*.DS_Store"]
}

resource "null_resource" "install_deps_api_fetch_videos_handler" {
  triggers = {
    source_hash = filemd5("${local.base_path}/api_fetch_videos_handler/lambda_function.py")
    deps_hash   = filemd5("${local.base_path}/api_fetch_videos_handler/pyproject.toml")
  }

  provisioner "local-exec" {
    command     = "./build-package.sh"
    working_dir = "${local.base_path}/api_fetch_videos_handler"
  }
}

data "archive_file" "api_fetch_videos_handler" {
  depends_on  = [null_resource.install_deps_api_fetch_videos_handler]
  type        = "zip"
  output_path = "${local.base_path}/api_fetch_videos_handler/package.zip"
  source_dir  = "${local.base_path}/api_fetch_videos_handler/package"
  excludes    = ["__pycache__", "*.pyc", "*.DS_Store"]
}

resource "null_resource" "install_deps_api_video_upload_link_handler" {
  triggers = {
    source_hash = filemd5("${local.base_path}/api_video_upload_link_handler/lambda_function.py")
    deps_hash   = filemd5("${local.base_path}/api_video_upload_link_handler/pyproject.toml")
  }

  provisioner "local-exec" {
    command     = "./build-package.sh"
    working_dir = "${local.base_path}/api_video_upload_link_handler"
  }
}

data "archive_file" "api_video_upload_link_handler" {
  depends_on  = [null_resource.install_deps_api_video_upload_link_handler]
  type        = "zip"
  output_path = "${local.base_path}/api_video_upload_link_handler/package.zip"
  source_dir  = "${local.base_path}/api_video_upload_link_handler/package"
  excludes    = ["__pycache__", "*.pyc", "*.DS_Store"]
}

resource "null_resource" "install_deps_api_fetch_tasks_handler" {
  triggers = {
    source_hash = filemd5("${local.base_path}/api_fetch_tasks_handler/lambda_function.py")
    deps_hash   = filemd5("${local.base_path}/api_fetch_tasks_handler/pyproject.toml")
  }

  provisioner "local-exec" {
    command     = "./build-package.sh"
    working_dir = "${local.base_path}/api_fetch_tasks_handler"
  }
}

data "archive_file" "api_fetch_tasks_handler" {
  depends_on  = [null_resource.install_deps_api_fetch_tasks_handler]
  type        = "zip"
  output_path = "${local.base_path}/api_fetch_tasks_handler/package.zip"
  source_dir  = "${local.base_path}/api_fetch_tasks_handler/package"
  excludes    = ["__pycache__", "*.pyc", "*.DS_Store"]
}

resource "null_resource" "install_deps_sqs_embedding_task_producer" {
  triggers = {
    lambda_hash = filemd5("${local.base_path}/sqs_embedding_task_producer/lambda_function.py")
    utils_hash  = filemd5("${local.base_path}/sqs_embedding_task_producer/utils.py")
    deps_hash   = filemd5("${local.base_path}/sqs_embedding_task_producer/pyproject.toml")
  }

  provisioner "local-exec" {
    command     = "./build-package.sh"
    working_dir = "${local.base_path}/sqs_embedding_task_producer"
  }
}

data "archive_file" "sqs_embedding_task_producer" {
  depends_on  = [null_resource.install_deps_sqs_embedding_task_producer]
  type        = "zip"
  output_path = "${local.base_path}/sqs_embedding_task_producer/package.zip"
  source_dir  = "${local.base_path}/sqs_embedding_task_producer/package"
  excludes    = ["__pycache__", "*.pyc", "*.DS_Store"]
}

resource "null_resource" "install_deps_sqs_embedding_task_consumer" {
  triggers = {
    source_hash = filemd5("${local.base_path}/sqs_embedding_task_consumer/lambda_function.py")
    deps_hash   = filemd5("${local.base_path}/sqs_embedding_task_consumer/pyproject.toml")
  }

  provisioner "local-exec" {
    command     = "./build-package.sh"
    working_dir = "${local.base_path}/sqs_embedding_task_consumer"
  }
}

data "archive_file" "sqs_embedding_task_consumer" {
  depends_on  = [null_resource.install_deps_sqs_embedding_task_consumer]
  type        = "zip"
  output_path = "${local.base_path}/sqs_embedding_task_consumer/package.zip"
  source_dir  = "${local.base_path}/sqs_embedding_task_consumer/package"
  excludes    = ["__pycache__", "*.pyc", "*.DS_Store"]
}

