from math import floor
from os import path, mkdir
import imghdr
from pathlib import Path
import traceback
import cv2
from .algorithms import resize, denoising, gif2jpg, sharpness, brightness, up_scale, save
from .libsvm.python.brisquequality import main as measure_quality
from logs import logger


width = 177
height = 224
scale = 3
to_generate = 3
processors = [up_scale, resize, brightness,
              sharpness, measure_quality,  denoising]


def apply_processors(image):
    print("\n" + '-' * 100, "\n")

    logger.info('processing image {} ...'.format(image))
    if path.isfile(image) and len(image) > 0 and imghdr.what(image):
        image_path, old_path = gif2jpg(image)
        # load the original input image
        try:
            tmp = cv2.imread(image_path)
            for processor in processors:
                tmp = processor(tmp, width, height, scale)
            final, score = tmp
            return (final, floor(score), old_path)
        except Exception as e:
            logger.info(
                'Error processing image: {}, reason = {} .'.format(old_path, e))
            traceback.print_tb(e.__traceback__)
            return (tmp, None, old_path)
        finally:
            print("\n" + '-' * 100, "\n")

    else:
        logger.info('Not exactly an image skipping.')
        print("\n" + '-' * 100, "\n")
        return (cv2.imread(image), None, image)


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
    final, score, image_path = output
    pathRef = Path(image_path)
    parent = pathRef.parent
    image_name = pathRef.name.split(".")
    image_extension = image_name.pop()
    try:
        image_out_path = str(path.join(
            create_dir(parent, 'output') if score and score < desired_score else create_dir(parent, 'rejected'), ".".join(image_name))) + (".%s" % image_extension)
        logger.info("saving image to this location: %s" % image_out_path)
        _save_final(image_out_path, final, parent)
    except Exception as e:
        logger.error("Error: could't save the image due to -> %s " % e)
        raise e
