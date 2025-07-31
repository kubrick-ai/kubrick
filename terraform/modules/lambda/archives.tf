locals {
  lambda_configs = {
    # Lambda Layers
    config_layer = {
      path = "layers/config_layer"
      sources = {
        source_hash = "config.py"
      }
      source_dir = "package"
    }
    embed_layer = {
      path = "layers/embed_service_layer"
      sources = {
        source_hash = "embed_service.py"
      }
      source_dir = "package"
    }
    response_utils_layer = {
      path = "layers/response_utils_layer"
      sources = {
        source_hash = "response_utils.py"
      }
      source_dir = "package"
    }
    vector_database_layer = {
      path = "layers/vector_database_layer"
      sources = {
        source_hash = "vector_db_service.py"
      }
      source_dir = "package"
    }

    # Lambda Functions
    db_bootstrap = {
      path = "db_bootstrap"
      sources = {
        source_hash = "lambda_function.py"
        schema_hash = "schema.sql"
      }
      source_dir = "package"
    }
    api_fetch_tasks_handler = {
      path = "api_fetch_tasks_handler"
      sources = {
        source_hash = "lambda_function.py"
      }
      source_dir = "package"
    }
    api_fetch_videos_handler = {
      path = "api_fetch_videos_handler"
      sources = {
        source_hash = "lambda_function.py"
      }
      source_dir = "package"
    }
    api_search_handler = {
      path = "api_search_handler"
      sources = {
        lambda_hash     = "lambda_function.py"
        controller_hash = "search_controller.py"
        errors_hash     = "search_errors.py"
      }
      source_dir = "package"
    }
    api_video_upload_link_handler = {
      path = "api_video_upload_link_handler"
      sources = {
        source_hash = "lambda_function.py"
      }
      source_dir = "package"
    }
    s3_delete_handler = {
      path = "s3_delete_handler"
      sources = {
        lambda_hash = "lambda_function.py"
        utils_hash  = "utils.py"
      }
      source_dir = "package"
    }
    sqs_embedding_task_producer = {
      path = "sqs_embedding_task_producer"
      sources = {
        lambda_hash = "lambda_function.py"
        utils_hash  = "utils.py"
      }
      source_dir = "package"
    }
    sqs_embedding_task_consumer = {
      path = "sqs_embedding_task_consumer"
      sources = {
        source_hash = "lambda_function.py"
      }
      source_dir = "package"
    }
  }
}

resource "null_resource" "build_package" {
  for_each = local.lambda_configs

  triggers = merge(
    { deps_hash = filemd5("${local.base_path}/${each.value.path}/pyproject.toml") },
    {
      for key, file in each.value.sources :
      key => filemd5("${local.base_path}/${each.value.path}/${file}")
    }
  )

  provisioner "local-exec" {
    command     = "./build-package.sh"
    working_dir = "${local.base_path}/${each.value.path}"
  }
}

data "archive_file" "packages" {
  for_each = local.lambda_configs

  type        = "zip"
  output_path = "${local.base_path}/${each.value.path}/package.zip"
  source_dir  = "${local.base_path}/${each.value.path}/${each.value.source_dir}"
  excludes    = ["__pycache__", "*.pyc", "*.DS_Store"]
}

