from distutils.file_util import move_file
from math import floor
from os import path, mkdir, system
import imghdr
from pathlib import Path
from shutil import move
import traceback
import cv2
import numpy as np

from utils import create_dirs
from .algorithms import resize, denoising, gif2jpg, sharpness, brightness, up_scale, save
from .libsvm.python.brisquequality import main as measure_quality
from logs import logger


width = 177
height = 236
scale = 3
to_generate = 3
processors = [resize]


def apply_processors(image, parent):
    print("\n" + '-' * 100, "\n")

    logger.info('processing image {} ...'.format(image))
    if path.isfile(image) and len(image) > 0 and imghdr.what(image):
        # load the original input image
        try:
            image_path, old_path = gif2jpg(image, parent)
            tmp = cv2.imread(image_path)
            for processor in processors:
                tmp = processor(tmp, width, height, scale)
   
            final, score = tmp if type(image) == tuple else (tmp, 10) # when no score is provided give a default one
            return (final, floor(score), old_path)
        except Exception as e:
            logger.info(
                'Error processing image: {}, reason = {} .'.format(old_path, e))
            raise e
        finally:
            print("\n" + '-' * 100, "\n")

    else:
        logger.info('Not exactly an image skipping.')
        print("\n" + '-' * 100, "\n")
        return (cv2.imread(image), 1000, image)


def _save_final(location, image, parent):
    save(location, image, parent)


def create_dir(parent, dir):
    """ create and return a directory if doesn't exist """
    directory = path.join(parent, dir)
    if not path.exists(directory):
        mkdir(directory)
    logger.info('create_dir: created directory %s ' % directory)
    return directory


def save_image(output, desired_score):
    """ save the image to a specific directory depends on the image quality score """
    final, score, image_path, root = output
    pathRef = Path(image_path)
    parent = pathRef.parent
    rootPath = Path(root)
    image_name = pathRef.name.split(".")
    image_extension = image_name.pop()
    outputPath = create_dir(
        root, 'output') if type(score) == int and score < desired_score else create_dir(root, 'rejected')
    joinedPath = Path(outputPath).joinpath(parent.relative_to(rootPath))
    create_dirs(joinedPath)

    try:
        image_out_path = str(path.join(
            joinedPath, ".".join(image_name))) + (".%s" % image_extension)
        logger.info("saving image to this location: %s" %
                    image_out_path)
        if isinstance(final, np.ndarray):
            _save_final(image_out_path, final, root)
        else:
            print('finalOuw:', final)
            move(image_path.strip("."),
                 joinedPath.absolute().as_posix())

    except Exception as e:
        logger.error("Error: could't save the image due to -> %s " % e)
        raise e
