import boto3
from os import getenv
import patoolib


def get_service(service, region_name):

    if getenv("ENV") == "localhost":
        print('get_service: using local configuration ...')
        session = boto3.Session(profile_name="infinidata",
                                region_name=region_name) if region_name else boto3.Session(profile_name="infinidata")
        return session.client(service)
    else:
        print('get_service: get credentials from ec2 instance ...')
        session = boto3.Session(
            region_name=region_name) if region_name else boto3.Session()
        credentials = session.get_credentials()
        credentials = credentials.get_frozen_credentials()
        return boto3.client(service,  aws_access_key_id=credentials.access_key, aws_secret_access_key=credentials.secret_key, aws_session_token=credentials.token)


def get_data():
    bucketName = getenv("SOURCE_BUCKET_NAME")
    print('dx', getenv("ENV"))
    fileName = getenv("SOURCE_FILE_NAME").replace("+", " ")
    print("begin fetching data from {} object in {} bucket ....".format(
        bucketName, fileName))
    try:
        s3 = get_service("s3", "us-east-1")
        with open(fileName, 'wb') as data:
            s3.download_fileobj(bucketName, fileName, data)
        print("data successfully retrieved.")
        print("extracting file ....")
        patoolib.extract_archive(fileName, outdir=".")
        print("file successfully extracted.")
    except Exception as e:
        print("error fetching data -> ", e)
        raise e


get_data()
