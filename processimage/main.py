from math import floor
from os import path, mkdir
import imghdr
from pathlib import Path
import cv2
from .resize import resize
from .denoising import denoising
from .convert_gif import gif2jpg
from .up_scale import up_scale
from .save import save


# from measure_quality import measure_quality
from .libsvm.python.brisquequality import main as measure_quality


width = 177
height = 224
scale = 4
to_generate = 3
processors = [up_scale, resize,  measure_quality]


def apply_processors(image):
    print('processing image {} ...'.format(image))
    if path.isfile(image) and len(image) > 0 and imghdr.what(image):
        image_path, old_path = gif2jpg(image)
        # load the original input image
        try:
            tmp = cv2.imread(image_path)
            # cap = cv2.VideoCapture(image)
            # ret, tmp = cap.read()
            # cap.release()
            # print('tmp', tmp)
            for processor in processors:
                tmp = processor(tmp, width, height, scale)
            final, score = tmp
            return (final, floor(score), old_path)
        except:
            return (tmp, None, old_path)
    else:
        return (cv2.imread(image), None, image)


def _save_final(location, image, parent):
    save(location, image, parent)


def create_dir(parent, dir):
    """ create and return a directory if doesn't exist """
    directory = path.join(parent, dir)
    if not path.exists(directory):
        mkdir(directory)
    print('create_dir: created directory', directory)
    return directory


def save_image(output, desired_score=28):
    """ save the image to a specific directory depends on the image quality score """
    final, score, image_path = output
    parent = Path(image_path).parent
    image_name = image_path.split("/").pop()
    image_name = image_name.split(".")
    image_extension = image_name.pop()
    try:
        image_out_path = str(path.join(
            create_dir(parent, 'output') if score < desired_score else create_dir(parent, 'rejected'), image_name[0])) + (".%s" % image_extension)
        print("saving image to this location: %s" % image_out_path)
        _save_final(image_out_path, final, parent)
    except Exception as e:
        print("Error: could't save the image due to -> ", e)
    finally:
        return output
