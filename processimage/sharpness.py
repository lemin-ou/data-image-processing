import cv2 as cv
import numpy as np


def sharpness(image, *args):
    laplacian = cv.Laplacian(image, cv.CV_64F)
    gnorm = np.sqrt(laplacian**2)
    sharpness = np.average(gnorm)
    print('image sharpness', sharpness)
    return image
