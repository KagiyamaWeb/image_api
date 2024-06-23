# create_bucket.sh
#!/bin/bash

BUCKET_NAME="testbucket"
MINIO_ALIAS="myminio"

if mc ls $MINIO_ALIAS/$BUCKET_NAME >/dev/null 2>&1; then
  echo "Bucket $BUCKET_NAME already exists."
else
  mc mb $MINIO_ALIAS/$BUCKET_NAME
  echo "Bucket $BUCKET_NAME created."
fi