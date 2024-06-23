import os
import boto3
from botocore.exceptions import NoCredentialsError

s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    endpoint_url=os.getenv('S3_ENDPOINT_URL')
)

BUCKET_NAME = os.getenv('S3_BUCKET_NAME')

def generate_presigned_url(object_name, expiration=3600):
    """Generate a presigned URL to share an S3 object

    :param object_name: string
    :param expiration: Time in seconds for the presigned URL to remain valid
    :return: Presigned URL as string. If error, returns None.
    """
    try:
        response = s3_client.generate_presigned_url(
            'put_object',
            Params={'Bucket': BUCKET_NAME, 'Key': object_name}, 
            ExpiresIn=expiration
    )
    
    except NoCredentialsError:
        return None

    # The response contains the presigned URL
    return response

def upload_file(file_name, object_name=None):
    if object_name is None:
        object_name = file_name

    try:
        response = s3_client.upload_file(file_name, BUCKET_NAME, object_name)
    except boto3.exceptions.S3UploadFailedError as e:
        print(f"Failed to upload {file_name} to {BUCKET_NAME}/{object_name}: {e}")
        return False
    return True