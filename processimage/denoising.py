

import cv2


def denoising(image, *args):
    enhanced = cv2.detailEnhance(image, sigma_s=6, sigma_r=0.10)
    denoised = cv2.fastNlMeansDenoisingColored(enhanced, None, 4, 4, 7, 21)

    return denoised
