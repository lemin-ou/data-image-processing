import boto3
from os import getenv, path
from rarfile import RarFile


def get_service(service, region_name):

    if getenv("ENV") == "localhost":
        print('get_service: using local configuration ...')
        session = boto3.Session(
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
    fileName = getenv("SOURCE_FILE_NAME")
    try:
        s3 = get_service("s3", "us-east-1")
        print("begin fetching data from {} object in {} bucket ....".format(
            bucketName, fileName))
        with open(path.join("data", fileName), 'wb') as data:
            s3.download_fileobj(bucketName, fileName, data)
        print("data successfully retrieved.")
        print("extracting file ....")
        rar = RarFile(path.join("data", fileName))
        dataPath = path.join("data", "extracted")
        rar.setpassword(getenv("SOURCE_FILE_PASSWORD"))
        rar.extractall(dataPath)
        print("file successfully extracted.")
        return dataPath
    except Exception as e:
        print("error fetching data -> ", e)
        raise e
