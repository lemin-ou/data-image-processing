
from logs import logger
from jproperties import Properties
import glob
from os import getenv, makedirs, mkdir, path
from shutil import rmtree
import load_env


def create_dir(parent, dir):
    """ create and return a directory if doesn't exist """
    directory = path.join(parent, dir)
    if not path.exists(directory):
        mkdir(directory)
        logger.info('create_dir: directory already exist %s ' % directory)
    else:
        logger.info('create_dir: created directory %s ' % directory)
    return directory


def create_dirs(dir):
    """ create and return a directory if doesn't exist """

    if not path.exists(dir):
        makedirs(dir)
        logger.info('create_dirs: directories already exist %s ' % dir)
    else:
        logger.info('create_dirs: created directories %s ' % dir)
    return dir


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


def empty_dir(dir):
    rmtree(dir)  # empty a directory
    mkdir(dir)  # create a directory


def delete_temp(batch):
    rmtree(path.join(batch, '.tmp'))


def get_root(root_path=__file__):
    isNotLocal = getenv("ENV") != 'localhost'
    config = load_config()
    file_dir = path.dirname(path.abspath(root_path))
    batchesPath = "{}/sample_data".format(path.join(file_dir, '..'))
    localRoot = batchesPath.replace("\\ ", " ")
    return config.get("imagespath") if isNotLocal else localRoot


def get_sample_dir():
    return path.join(get_root(),  "sample_image")


def get_root_output_dir():
    return path.join(get_root(),  "output")


def get_root_rejected_dir():
    return path.join(get_root(), "rejected")


def get_root_directories():
    directories = []
    lookFor = path.join(get_root(), '01', "00*")
    directories.extend(glob.glob(lookFor))
    return directories
