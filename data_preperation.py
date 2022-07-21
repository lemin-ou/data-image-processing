from glob import glob
from pathlib import Path
from cv2 import split
import boto3
from os import getenv, listdir, path
from rarfile import RarFile
from logs import logger
import pandas as pd
import traceback
from jproperties import Properties

from utils import get_root


def get_service(service, region_name):
    if getenv("ENV") == "localhost":
        logger.info('using local configuration ...')
        session = boto3.Session(profile_name="infinidata",
                                region_name=region_name) if region_name else boto3.Session(profile_name="infinidata")
        return session.client(service)
    else:
        logger.info('get credentials from ec2 instance ...')
        session = boto3.Session(
            region_name=region_name) if region_name else boto3.Session()
        credentials = session.get_credentials()
        credentials = credentials.get_frozen_credentials()
        return boto3.client(service,  aws_access_key_id=credentials.access_key, aws_secret_access_key=credentials.secret_key, aws_session_token=credentials.token)


def get_data():
    isNotLocal = getenv("ENV") != 'localhost'
    bucketName = getenv("SOURCE_BUCKET_NAME")
    fileName = getenv("SOURCE_FILE_NAME")
    try:
        isNotLocal = getenv("ENV") != 'localhost'
        if isNotLocal:
            s3 = get_service("s3", "us-east-1")
            logger.info("begin fetching data from {} object in {} bucket ....".format(
                bucketName, fileName))
            with open(path.join("data", fileName), 'wb') as data:
                s3.download_fileobj(bucketName, fileName, data)
            logger.info("data successfully retrieved.")
            logger.info("extracting file ....")
            rar = RarFile(path.join("data", fileName))
            dataPath = Path(path.join("data", "extracted"))
            rar.setpassword(getenv("SOURCE_FILE_PASSWORD"))
            rar.extractall(str(dataPath))
            logger.info("file successfully extracted.")
        logger.info("write data file path .....")
        with open("requirements.properties", "w") as configFile:
            extractedDir = ""
            try:
                extractedDir = dataPath.joinpath(
                    Path(listdir(dataPath)[0])) if isNotLocal else Path(get_root())
                extractedDir = str(extractedDir.resolve())
                withoutExtension = glob(
                    str(extractedDir) + "/*.xlsx")[0].split(".")
            except Exception as e:
                logger.error(
                    "can't find extracted directory or its data file -> %s " % e)
                raise e

            withoutExtension.pop()
            withoutExtension = ".".join(withoutExtension)

            configFile.write("excelpath={}.xlsx\n".format(
                path.join(extractedDir, withoutExtension)))
            configFile.write("csvpath={}.csv\n".format(
                path.join(extractedDir, withoutExtension)))
            configFile.write("imagespath={}\n".format(extractedDir))
        return extractedDir
    except Exception as e:
        logger.error("error fetching data -> %s " % e)
        raise e


# get path from requirements.properties file
def convert_to_csv():
    try:
        logger.info("converting to csv ....")
        config_dist = load_config()

        excelpath = config_dist.get('excelpath')
        csvpath = config_dist.get('csvpath')

        # read excel file with string type and header position

        logger.info("reading excel file.......")

        read_file = pd.read_excel(f'{excelpath}', dtype=str, header=6)

        logger.info("excel file loaded to dataframe .......")

        # generate csv file with @ seperator and utf-8 encoding

        logger.info("write dataframe as csv file.......")
        read_file.to_csv(f'{csvpath}', index=None, sep='@',
                         encoding='UTF-8', header=True)
    except Exception as e:
        logger.error("error converting to excel -> %s " % e)
        raise e


def load_config():
    logger.info("loading configuration file")
    configs = Properties()
    with open('requirements.properties', 'rb') as configfile:
        configs.load(configfile)

    logger.info("context variables loaded......")

    items = configs.items()
    config_dist = {}

    for item in items:
        config_dist[item[0]] = item[1].data

    return config_dist


def convert_to_excel():
    try:
        logger.info("converting to excel ....")
        config_dist = load_config()
        exceloutpath = config_dist.get('exceloutpath')
        csvpath = config_dist.get('csvpath')

        # read excel file with string type and header position

        logger.info("reading csv file.......")

        read_file = pd.read_csv(f'{csvpath}', dtype=str, header=0, sep='@')

        logger.info("csv file loaded to dataframe .......")

        # generate csv file with @ seperator and utf-8 encoding

        logger.info("write dataframe as excel file.......")

        read_file.to_excel(f'{exceloutpath}', encoding='UTF-8', header=True)
    except Exception as e:
        logger.error("error converting to excel -> %s " % e)
        raise e
