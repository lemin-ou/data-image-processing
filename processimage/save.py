import cv2
from shutil import move


def save(location, image, parent):
    extension = location.split(".").pop()  # get the extension
    if extension.lower() == 'gif':
        file_full_path = location.split("/")
        name = file_full_path.pop()
        old_path = '{}/../.tmp/{}.JPG'.format(
            parent, name.removesuffix('.%s' % extension.upper()).removesuffix('.%s' % extension.lower()))
        print('gif2jpg: save the gif file to this new path ->', old_path)
        cv2.imwrite(filename=old_path,  img=image)
        move(old_path, location)
    else:
        cv2.imwrite(filename=location,  img=image)
