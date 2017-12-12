#! /usr/bin/env python

import argparse
import os

from core.api import SmugmugAPI
from core.db import db, Photo
from core.db import init_db
from photos_parser import find_media_files, sync_files_with_db
from settings import logger
from utils.db_status import show_db_status
from utils.md5 import get_md5
from utils.utils import chunks


class SmugSync(object):
    def __init__(self):
        self.api = SmugmugAPI()

    def show_stat_by_md5(self):
        md5_success_count = 0
        md5_failed_count = 0
        md5_not_found = 0

        for photos_chunk in self.api.get_remote_images():
            logger.info("[INFO] Total photos in API response: %d",
                        len(photos_chunk))

            for p in photos_chunk:
                p_md5 = p.get('ArchivedMD5')

                if not p_md5:
                    md5_failed_count += 1
                    logger.info("[ERROR] ArchivedMD5 is NULL")
                    continue

                p_db = Photo.select().where(Photo.local_md5 == p_md5)

                if not p_db:
                    logger.info("[ERROR] MD5 %s not found in DB for file: %s",
                                p_md5, p.get('FileName'))
                    md5_not_found += 1
                    continue
                else:
                    p_db = p_db[0]

                if p.get('FileName') == os.path.basename(p_db.local_path):
                    p_db.ext_md5 = p_md5
                    p_db.save()
                    md5_success_count += 1
                else:
                    logger.info("[ERROR] MD5 not equal. local: %s remote: %s",
                                p_db.local_path, p.get('FileName'))

                    md5_failed_count += 1

            logger.info(
                "\n\nSuccess: %d\nFailed: %d\nNot found: %d\nTotal: %d",
                md5_success_count,
                md5_failed_count,
                md5_not_found,
                md5_failed_count + md5_not_found + md5_success_count)

    def sync_structure(self):
        media_data = find_media_files()
        self.media_data = sync_files_with_db(media_data)

        if not self.media_data.get('albums'):
            logger.info("No new photos to upload")
            return

        root_node_uri = self.api.get_root_node()

        # Create new folders
        for folder_path, files_bundle in self.media_data['albums'].items():
            folders = folder_path.strip('/').split('/')

            prev_node_uri = root_node_uri

            for cnt, f in enumerate(folders, start=1):

                if cnt == len(folders):
                    nt = 'Album'
                else:
                    nt = 'Folder'

                current_node_uri = self.api.get_or_create_node(
                    prev_node_uri, f, node_type=nt
                )

                if cnt == len(folders):
                    files_bundle['album_uri'] = current_node_uri

                prev_node_uri = current_node_uri

        # Process children albums (get uri or create)
        for folder_path, files_bundle in self.media_data['albums'].items():
            with db.atomic():
                photos_insert_to_db = []
                for f in files_bundle['files']:
                    photos_insert_to_db.append(
                        {
                            'local_path': f,
                            'local_md5': get_md5(f),
                            'status': 'pending'
                        }
                    )

                if photos_insert_to_db:
                    logger.info("\tInserting to DB: %d",
                                len(photos_insert_to_db))

                    for photos_insert_to_db_chunk in chunks(
                            photos_insert_to_db, 300):
                        Photo.insert_many(photos_insert_to_db_chunk).execute()

                for files_chunk in chunks(files_bundle['files'], 300):
                    Photo.update(
                        ext_album_key=files_bundle['album_uri']
                    ).where(
                        (Photo.local_path << files_chunk)
                    ).execute()


def info_actions(args):
    if args.db_stat:
        show_db_status()
    elif args.check_md5:
        ss = SmugSync()
        ss.show_stat_by_md5()
    elif args.init_db:
        init_db()


if __name__ == '__main__':
    main_parser = argparse.ArgumentParser(
        description="Sync your videos and photos collection with your "
                    "smugmug.com account. Helper script."
    )
    main_parser.add_argument(
        '-v', '--verbose',
        help='Verbose execution',
        action='store_false',
    )
    main_parser.add_argument(
        '-i', '--init-db',
        help='Create db table',
        action='store_true',
    )
    main_parser.add_argument(
        '-get_md5', '--check-get_md5',
        help='Show statistic by comparing MD5 checksum for local/remote images',
        action='store_true',
    )
    main_parser.add_argument(
        '-stat', '--db-stat',
        help='Show upload queue info',
        action='store_true',
    )

    args = main_parser.parse_args()
    info_actions(args)
