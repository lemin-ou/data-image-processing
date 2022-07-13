

import cv2


def resize(image, width, height, *args):
    # prevent our resized image from being skewed/distorted
    is_scale_down = width < image.shape[0]

    print('performing scale down....') if is_scale_down else print(
        'performing scale up....')
    dim = (width, height)
    # perform the actual resizing of the image
    resized = cv2.resize(
        image, dim, interpolation=cv2.INTER_CUBIC)

    return resized
