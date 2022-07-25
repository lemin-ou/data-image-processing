from genericpath import isfile
from glob import glob
from pathlib import Path
from pydoc import pathdirs
from shutil import copy, move, rmtree
import boto3
from os import getenv, listdir, path, remove
from rarfile import RarFile
from logs import logger
import pandas as pd
from subprocess import call
from utils import create_dir, create_dirs, get_root, load_config


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
            logger.info('deleting the compressed file ....')
            remove(Path(path.join("data", fileName)).absolute().as_posix())
        logger.info("write data file path .....")
        extractedDir = dataPath.joinpath(
            Path(listdir(dataPath)[0])) if isNotLocal else Path(get_root())
        return generate_config(extractedDir)
    except Exception as e:
        logger.error("error fetching data -> %s " % e)
        raise e


def put_data(roots):
    isNotLocal = getenv("ENV") != 'localhost'
    try:
        bucketName = getenv(
            "DESTINATION_BUCKET_NAME" if isNotLocal else "SOURCE_BUCKET_NAME")
        config = load_config()
        isNotLocal = getenv("ENV") != 'localhost'

        s3 = get_service("s3", None if isNotLocal else "us-east-1")
        for dir in roots:
            fileLocation = config.get('file%spath' % dir)
            logger.info('uploading file %s ' % fileLocation)
            with open(fileLocation, "rb") as file:
                s3.upload_fileobj(file, bucketName, path.join(
                    dir, Path(fileLocation).name))

    except Exception as e:
        logger.error("error putting data to s3 -> %s " % e)
        raise e


def generate_config(extractedDir):
    logger.info("generating configuration file ....")
    with open("requirements.properties", "w") as configFile:

        try:

            extractedDir = str(extractedDir.resolve())
            withoutExtension = Path(glob(
                str(extractedDir) + "/*.xlsx")[0]).name.split(".")
        except Exception as e:
            logger.error(
                "can't find extracted directory or its data file -> %s " % e)
            raise e

        withoutExtension.pop()
        withoutExtension = ".".join(withoutExtension)
        rejected = create_dir(extractedDir, "rejected")
        output = create_dir(extractedDir, "output")

        logger.info(
            "write files paths to the configuration file .... %s" % rejected)

        # rejected files
        configFile.write("rejectexcelpath={}.xlsx\n".format(
            path.join(rejected, withoutExtension)))
        configFile.write("rejectcsvpath={}.csv\n".format(
            path.join(rejected, withoutExtension)))

        # valid files
        configFile.write("validexcelpath={}.xlsx\n".format(
            path.join(output, withoutExtension)))
        configFile.write("validcsvpath={}.csv\n".format(
            path.join(output, withoutExtension)))

        # source files and dir
        configFile.write("excelpath={}.xlsx\n".format(
            path.join(extractedDir, withoutExtension)))
        configFile.write("csvpath={}.csv\n".format(
            path.join(extractedDir, withoutExtension)))
        configFile.write("imagespath={}\n".format(extractedDir))

        # write extensions thresholds
        extensions = ["png", 'jpg', 'gif', 'bmp', 'default']
        for threshold in map(lambda x: "IMAGE_%s_THRESHOLD" % x.upper(), extensions):
            configFile.write('{}={}\n'.format(threshold, getenv(threshold)))

        contextPath = Path(getenv('JOB_CONTEXT_PATH')).absolute().as_posix()
        configPath = Path(configFile.name).absolute().as_posix()
        configFile.close()

        logger.info("move configuration file to job context .... %s " %
                    contextPath)
        if path.exists(contextPath):
            remove(contextPath)
        copy(configPath,
             contextPath)

    return extractedDir


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


def move_rejected_files(root):
    config = load_config()
    try:
        file = config.get("rejectcsvpath")
        logger.info("reading csv file....... : %s " % file)
        read_file = pd.read_csv(
            f'{file}', dtype=str, header=0, sep='@').iloc[:600]
        logger.info("iterate on NNI and picture path......")
        for i in read_file.index:
            # all photo has been moved to the output directory
            photoPortion = read_file['PhotoPath'][i].strip("/")
            outputDir = path.join(root, "output")
            rejectedDir = path.join(root, "rejected")
            src = path.join(outputDir, photoPortion)
            dest = Path(path.join(rejectedDir, photoPortion))
            # create destination directories if not exist
            create_dirs(dest.parent)
            if path.exists(dest):
                logger.info("file %s already moved to %s directory" %
                            (src, dest.parent))
            else:
                logger.info("moving %s picture to %s " %
                            (src, dest.parent))
                move(src, dest)

        logger.info(
            'all pictures were moved to picture path : %s ' % rejectedDir)
    except Exception as e:
        logger.error(
            'Error related to moving photos to rejected directory -> %s' % e)
        raise e


def move_image_to_root(root, dest):
    dest = Path(dest).absolute().as_posix()
    sub = listdir(root)
    try:
        for dir in sub:
            dirPath = Path(path.join(root, dir))
            if path.isdir(dirPath) and len(listdir(dirPath)) > 0:
                logger.info("iterating over %s " % dirPath)
                move_image_to_root(dirPath, dest)
                rmtree(dirPath)  # remove directory after it has been emptied
            elif path.isfile(dirPath) and not path.exists(path.join(dest, dirPath.name)):
                logger.info("moving %s to %s " % (dirPath, dest))
                move(dirPath, dest)
    except Exception as e:
        logger.error("Error while moving to root -> %s " % e)
        raise e


def compress_directories(root):
    logger.info("compressing directories ....:")
    for dir in [create_dir(root, 'output'), create_dir(root, 'rejected')]:
        try:
            logger.info("compressing directory %s ....." % dir)
            fileName = Path(root).name
            destinationPart = Path(dir).name
            compressedDir = create_dirs(
                path.join(root, 'compressed', destinationPart))
            fileFullPath = path.join(compressedDir, fileName)
            logger.info("save rar to this location : %s " % fileFullPath)
            resCode = call("rar a -p'{}' '{}.rar' '{}' ".format(
                getenv("SOURCE_FILE_PASSWORD"), fileFullPath, dir), shell=True)
            if type(resCode) == int and resCode != 0:
                raise Exception(
                    "compression isn't handled successfully -> %s" % resCode)
            else:
                logger.info("directory successfully compressed.")
                logger.info("write file location ....")
                with open("requirements.properties", "a") as configFile:
                    configFile.write("file{}path={}.rar\n".format(
                        destinationPart, fileFullPath))
        except Exception as e:
            logger.error(
                "Error while compressing %s directory -> %s " % (dir, e))
            raise e
# move_image_to_root(argv[1], argv[2])
