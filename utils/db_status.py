from __future__ import absolute_import

from core.db import Photo, fn
from settings import logger


def show_db_status():
    photos_status = (
        Photo
            .select(Photo.status, fn.COUNT(Photo.id).alias('photos_count'))
            .group_by(Photo.status)
    )
    for s in photos_status:
        logger.info("Status: %s, count: %d", s.status, s.photos_count)


if __name__ == '__main__':
    show_db_status()
