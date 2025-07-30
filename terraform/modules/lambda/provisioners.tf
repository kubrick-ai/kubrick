# Build automation for Lambda layers
resource "null_resource" "layer_build_vectordb" {
  triggers = {
    source_hash    = filemd5("${local.base_path}/layers/vector_database_layer/vector_db_service.py")
    deps_hash      = filemd5("${local.base_path}/layers/vector_database_layer/pyproject.toml")
    package_exists = fileexists("${local.base_path}/layers/vector_database_layer/package.zip")
  }

  provisioner "local-exec" {
    command     = "./build-package.sh"
    working_dir = "${local.base_path}/layers/vector_database_layer"
  }
}

resource "null_resource" "layer_build_embed" {
  triggers = {
    source_hash    = filemd5("${local.base_path}/layers/embed_service_layer/embed_service.py")
    deps_hash      = filemd5("${local.base_path}/layers/embed_service_layer/pyproject.toml")
    package_exists = fileexists("${local.base_path}/layers/embed_service_layer/package.zip")
  }

  provisioner "local-exec" {
    command     = "./build-package.sh"
    working_dir = "${local.base_path}/layers/embed_service_layer"
  }
}

resource "null_resource" "layer_build_config" {
  triggers = {
    source_hash    = filemd5("${local.base_path}/layers/config_layer/config.py")
    deps_hash      = filemd5("${local.base_path}/layers/config_layer/pyproject.toml")
    package_exists = fileexists("${local.base_path}/layers/config_layer/package.zip")
  }

  provisioner "local-exec" {
    command     = "./build-package.sh"
    working_dir = "${local.base_path}/layers/config_layer"
  }
}

resource "null_resource" "layer_build_utils" {
  triggers = {
    source_hash    = filemd5("${local.base_path}/layers/response_utils_layer/response_utils.py")
    deps_hash      = filemd5("${local.base_path}/layers/response_utils_layer/pyproject.toml")
    package_exists = fileexists("${local.base_path}/layers/response_utils_layer/package.zip")
  }

  provisioner "local-exec" {
    command     = "./build-package.sh"
    working_dir = "${local.base_path}/layers/response_utils_layer"
  }
}

# Build automation for Lambda functions
resource "null_resource" "lambda_build_db_bootstrap" {
  triggers = {
    source_hash    = filemd5("${local.base_path}/db_bootstrap/lambda_function.py")
    config_hash    = filemd5("${local.base_path}/db_bootstrap/config.json")
    deps_hash      = filemd5("${local.base_path}/db_bootstrap/pyproject.toml")
    schema_hash    = filemd5("${local.base_path}/db_bootstrap/schema.sql")
    package_exists = fileexists("${local.base_path}/db_bootstrap/package.zip")
  }

  provisioner "local-exec" {
    command     = "./build-package.sh"
    working_dir = "${local.base_path}/db_bootstrap"
  }
}

resource "null_resource" "lambda_build_api_search_handler" {
  triggers = {
    source_hash     = filemd5("${local.base_path}/api_search_handler/lambda_function.py")
    controller_hash = filemd5("${local.base_path}/api_search_handler/search_controller.py")
    errors_hash     = filemd5("${local.base_path}/api_search_handler/search_errors.py")
    config_hash     = filemd5("${local.base_path}/api_search_handler/config.json")
    deps_hash       = filemd5("${local.base_path}/api_search_handler/pyproject.toml")
    package_exists  = fileexists("${local.base_path}/api_search_handler/package.zip")
  }

  provisioner "local-exec" {
    command     = "./build-package.sh"
    working_dir = "${local.base_path}/api_search_handler"
  }
}

resource "null_resource" "lambda_build_s3_delete_handler" {
  triggers = {
    source_hash    = filemd5("${local.base_path}/s3_delete_handler/lambda_function.py")
    utils_hash     = filemd5("${local.base_path}/s3_delete_handler/utils.py")
    config_hash    = filemd5("${local.base_path}/s3_delete_handler/config.json")
    deps_hash      = filemd5("${local.base_path}/s3_delete_handler/pyproject.toml")
    package_exists = fileexists("${local.base_path}/s3_delete_handler/package.zip")
  }

  provisioner "local-exec" {
    command     = "./build-package.sh"
    working_dir = "${local.base_path}/s3_delete_handler"
  }
}

resource "null_resource" "lambda_build_api_fetch_videos_handler" {
  triggers = {
    source_hash    = filemd5("${local.base_path}/api_fetch_videos_handler/lambda_function.py")
    config_hash    = filemd5("${local.base_path}/api_fetch_videos_handler/config.json")
    deps_hash      = filemd5("${local.base_path}/api_fetch_videos_handler/pyproject.toml")
    package_exists = fileexists("${local.base_path}/api_fetch_videos_handler/package.zip")
  }

  provisioner "local-exec" {
    command     = "./build-package.sh"
    working_dir = "${local.base_path}/api_fetch_videos_handler"
  }
}

resource "null_resource" "lambda_build_api_video_upload_link_handler" {
  triggers = {
    source_hash    = filemd5("${local.base_path}/api_video_upload_link_handler/lambda_function.py")
    deps_hash      = filemd5("${local.base_path}/api_video_upload_link_handler/pyproject.toml")
    package_exists = fileexists("${local.base_path}/api_video_upload_link_handler/package.zip")
  }

  provisioner "local-exec" {
    command     = "./build-package.sh"
    working_dir = "${local.base_path}/api_video_upload_link_handler"
  }
}

resource "null_resource" "lambda_build_api_fetch_tasks_handler" {
  triggers = {
    source_hash    = filemd5("${local.base_path}/api_fetch_tasks_handler/lambda_function.py")
    config_hash    = filemd5("${local.base_path}/api_fetch_tasks_handler/config.json")
    deps_hash      = filemd5("${local.base_path}/api_fetch_tasks_handler/pyproject.toml")
    package_exists = fileexists("${local.base_path}/api_fetch_tasks_handler/package.zip")
  }

  provisioner "local-exec" {
    command     = "./build-package.sh"
    working_dir = "${local.base_path}/api_fetch_tasks_handler"
  }
}

resource "null_resource" "lambda_build_sqs_embedding_task_producer" {
  triggers = {
    source_hash    = filemd5("${local.base_path}/sqs_embedding_task_producer/lambda_function.py")
    utils_hash     = filemd5("${local.base_path}/sqs_embedding_task_producer/utils.py")
    config_hash    = filemd5("${local.base_path}/sqs_embedding_task_producer/config.json")
    deps_hash      = filemd5("${local.base_path}/sqs_embedding_task_producer/pyproject.toml")
    package_exists = fileexists("${local.base_path}/sqs_embedding_task_producer/package.zip")
  }

  provisioner "local-exec" {
    command     = "./build-package.sh"
    working_dir = "${local.base_path}/sqs_embedding_task_producer"
  }
}

resource "null_resource" "lambda_build_sqs_embedding_task_consumer" {
  triggers = {
    source_hash    = filemd5("${local.base_path}/sqs_embedding_task_consumer/lambda_function.py")
    config_hash    = filemd5("${local.base_path}/sqs_embedding_task_consumer/config.json")
    deps_hash      = filemd5("${local.base_path}/sqs_embedding_task_consumer/pyproject.toml")
    package_exists = fileexists("${local.base_path}/sqs_embedding_task_consumer/package.zip")
  }

  provisioner "local-exec" {
    command     = "./build-package.sh"
    working_dir = "${local.base_path}/sqs_embedding_task_consumer"
  }
}