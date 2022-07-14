import boto3
from os import getenv
import patoolib
from botocore.config import Config


def get_service(service, region_name):
    config = Config(
        region_name=region_name,
        credential_source="Ec2InstanceMetadata"
    )
    profile = "infinidata" if getenv("ENV") == "localhost" else "ec2user"
    print('get_service: using local configuration ...')
    if region_name:
        session = boto3.Session(profile_name=profile,  region_name=region_name)
    else:
        session = boto3.Session(profile_name=profile)

    return session.client(service)


def get_data():
    bucketName = getenv("SOURCE_BUCKET_NAME")
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
