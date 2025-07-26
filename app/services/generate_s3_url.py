import boto3

s3_client = boto3.client("s3")


def generate_presigned_url(bucket_name, object_key, expiration=3600):
    """
    Generate a presigned URL to share an S3 object

    :param bucket_name: str
    :param object_key: str
    :param expiration: Time in seconds for the presigned URL to remain valid
    :return: Presigned URL as string
    """
    try:
        response = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket_name, "Key": object_key},
            ExpiresIn=expiration,
        )
    except Exception as e:
        print(f"Error generating URL: {e}")
        return None
    return response
