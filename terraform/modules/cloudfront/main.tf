# resource "aws_cloudfront_origin_access_control" "oac" {
#   name                               = "cloudfront-oac"
#   description                        = "OAC for CloudFront access to S3"
#   origin_access_control_origin_type  = "s3"
#   signing_behavior                   = "always"
#   signing_protocol                   = "sigv4"
# }

resource "aws_cloudfront_distribution" "kubrick_playground" {
  enabled             = true
  default_root_object = "index.html"

  origin {
    domain_name = var.kubrick_playground_bucket_website_endpoint
    origin_id   = "s3-static-website"

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "http-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  default_cache_behavior {
    target_origin_id       = "s3-static-website"
    viewer_protocol_policy = "redirect-to-https"

    allowed_methods = ["GET", "HEAD"]
    cached_methods  = ["GET", "HEAD"]

    forwarded_values {
      query_string = true

      cookies {
        forward = "none"
      }
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  custom_error_response {
    error_code         = 404
    response_code      = 200
    response_page_path = "/index.html"
  }

  custom_error_response {
    error_code         = 403
    response_code      = 200
    response_page_path = "/index.html"
  }
}

