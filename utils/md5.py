import hashlib

from core.db import Photo
from settings import logger


def get_md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def add_md5_for_photos(photos):
    for p in photos:
        p_md5 = get_md5(p.local_path)
        p.local_md5 = p_md5
        p.save()
        logger.info('%s --> %s', p.local_path, p_md5)


def get_photos_without_md5():
    photos = Photo.select().where(Photo.local_md5 == None)
    logger.info("Total photos without MD5: %d", len(photos))
    return photos


if __name__ == '__main__':
    photos = get_photos_without_md5()
    add_md5_for_photos(photos)
