

import cv2


def up_scale(image, width, height, scale):
    if(width < image.shape[0]):
        return image  # do not upscale if width required is less than the image width hence down scale
    sr = cv2.dnn_superres.DnnSuperResImpl_create()

    path = "./EDSR/EDSR_x{}.pb".format(scale)

    sr.readModel(path)

    sr.setModel("edsr", scale)

    return sr.upsample(image)
