#!/bin/bash
set -e

# Load environment variables
if [ -f .env.local ]; then
  export $(cat .env.local | xargs)
fi

# Deploy to S3
aws s3 sync out/ s3://$S3_BUCKET_PLAYGROUND --delete --profile $S3_PROFILE

echo "Deployed to S3 bucket: $S3_BUCKET_PLAYGROUND"
#
# aws cloudfront create-invalidation --distribution-id $CLOUDFRONT_DISTRIBUTION_ID
# echo "Created cloudfront invalidation: $S3_BUCKET_PLAYGROUND"
