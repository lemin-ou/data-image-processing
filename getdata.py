import boto3
from os import getenv
import patoolib

session = boto3.Session(profile_name='infinidata', region_name="us-east-1")
s3 = session.client("s3")


def get_data():
    bucketName = getenv("SOURCE_BUCKET_NAME")
    fileName = getenv("SOURCE_FILE_NAME").replace("+", " ")
    print("begin fetching data from {} object in {} bucket ....".format(
        bucketName, fileName))

    try:
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
