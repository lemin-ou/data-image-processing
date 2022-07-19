import numpy as np
import cv2
from numpy.linalg import norm
from PIL import Image
from PIL import GifImagePlugin
from math import floor
from pathlib import Path
from shutil import move
import logs
from logs import logger


def brightness(img, *args):
    """
    show image brightness, this value will be used later to increase or decrease image brightness
    """
    brightness_measure = 0
    if len(img.shape) == 3:
        # Colored RGB or BGR (*Do Not* use HSV images with this function)
        # create brightness with euclidean norm
        brightness_measure = np.average(norm(img, axis=2)) / np.sqrt(3)
    else:
        # Grayscale
        brightness_measure = np.average(img)
    logger.info("brightness: image brightness = {} ".format(brightness_measure))
    return img


def resize(image, width, height, *args):
    """
    resize an image to a specific dimension
    """

    is_scale_down = width < image.shape[0]

    logger.info('performing scale down....') if is_scale_down else logger.info(
        'performing scale up....')
    dim = (width, height)
    # perform the actual resizing of the image
    resized = cv2.resize(
        image, dim, interpolation=cv2.INTER_CUBIC)

    return resized


def up_scale(image, width, height, scale):
    """
    apply a Super Resolution algorithm using a specific model
    """
    if(width < image.shape[0]):
        return image  # do not upscale if width required is less than the image width hence down scale
    sr = cv2.dnn_superres.DnnSuperResImpl_create()

    fullPath = Path(__file__)

    path = "{}/EDSR/EDSR_x{}.pb".format(str(fullPath.parent), scale)

    sr.readModel(path)

    sr.setModel("edsr", scale)

    return sr.upsample(image)


def sharpness(image, *args):
    """
    sharpen image with sharpness indicator less or equal certain value
    """
    actualImage = image[0] if type(
        image) == tuple else image
    laplacian = cv2.Laplacian(actualImage, cv2.CV_64F)
    gnorm = np.sqrt(laplacian**2)
    sharpness = np.average(gnorm)
    logger.info("sharpness: detected sharpness: %s " % sharpness)
    if floor(sharpness) <= 4:
        sharpen_kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
        sharpen = cv2.filter2D(actualImage, -1, sharpen_kernel)
        return (sharpen, image[1]) if type(image) == tuple else sharpen

    return image


def denoising(image, width, height, *args):
    """
    apply the denoising algorithm
    """
    denoised = cv2.fastNlMeansDenoisingColored(
        image[0] if type(image) == tuple else image, None, 3, 3, 7, 21)
    # enhanced = cv2.detailEnhance(denoised, sigma_s=3, sigma_r=0.10)
    norm_img = np.zeros((width, height))
    norm_img = cv2.normalize(denoised, norm_img, 0, 255, cv2.NORM_MINMAX)

    return (norm_img, image[1]) if type(image) == tuple else norm_img


def gif2jpg(file_name: str):
    """
    convert gif to `num_key_frames` images with jpg format
    :param file_name: gif file name
    :return:
    """

    extension = file_name.split(".").pop()  # get the extension
    if extension.lower() != 'gif':
        return (file_name, file_name)  # just to accommodate
    logger.info("gif2jpg: transforming GIF to JPG -> location: %s" % file_name)
    with Image.open(file_name) as im:
        im.seek(0)  # grab the first frame
        image = im.convert("RGBA")
        datas = image.getdata()
        newData = []
        for item in datas:
            if item[3] == 0:  # if transparent
                # set transparent color in jpg
                newData.append((255, 255, 255))
            else:
                newData.append(tuple(item[:3]))
        image = Image.new("RGB", im.size)
        image.getdata()
        image.putdata(newData)
        file_full_path = file_name.split("/")
        name = file_full_path.pop()
        new_file_name = '{}/../.tmp/{}.JPG'.format(
            "/".join(file_full_path), name.removesuffix('.%s' % extension.upper()).removesuffix('.%s' % extension.lower()))
        image.save(new_file_name)
        logger.info('gif2jpg: gif file new path ->', new_file_name)
        return (new_file_name, file_name)


def save(location, image, parent):
    """
    save image to a specific location
    """
    extension = location.split(".").pop()  # get the extension
    if extension.lower() == 'gif':
        file_full_path = location.split("/")
        name = file_full_path.pop()
        old_path = '{}/../.tmp/{}.JPG'.format(
            parent, name.removesuffix('.%s' % extension.upper()).removesuffix('.%s' % extension.lower()))
        logger.info('gif2jpg: save the gif file to this new path ->', old_path)
        cv2.imwrite(filename=old_path,  img=image)
        move(old_path, location)
    else:
        cv2.imwrite(filename=location,  img=image)
