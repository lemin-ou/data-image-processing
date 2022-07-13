from PIL import Image
from PIL import GifImagePlugin


def gif2jpg(file_name: str):
    """
    convert gif to `num_key_frames` images with jpg format
    :param file_name: gif file name
    :return:
    """
    print("gif2jpg: transforming GIF to JPG -> location: %s" % file_name)
    extension = file_name.split(".").pop()  # get the extension
    if extension.lower() != 'gif':
        return (file_name, file_name)  # just to accommodate
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
        print('gif2jpg: gif file new path ->', new_file_name)
        return (new_file_name, file_name)
