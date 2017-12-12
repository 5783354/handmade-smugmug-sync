from __future__ import absolute_import

import os

from core.db import Photo, db
from settings import logger
from utils.utils import chunks


def clean_hidden_files_from_db():
    photos_in_db = Photo.select(Photo.local_path)

    logger.info("Total photos in DB: %d", photos_in_db.count())

    hidden_files_to_remove = []

    for p in photos_in_db:
        file_name = os.path.basename(p.local_path)
        if file_name.startswith('.'):
            logger.info("Hidden file found: %s", file_name)

            hidden_files_to_remove.append(p.local_path)

    logger.info("Total hidden files count: %d", len(hidden_files_to_remove))

    if hidden_files_to_remove:
        with db.atomic():
            for files_chunk in chunks(hidden_files_to_remove, 300):
                _removed_cnt = Photo.delete().where(
                    (Photo.local_path << files_chunk)
                ).execute()

                logger.info("Removed: %d", _removed_cnt)


if __name__ == '__main__':
    clean_hidden_files_from_db()
