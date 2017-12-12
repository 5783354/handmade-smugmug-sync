import os
import re
from os import walk

from core.db import Photo
from settings import logger, PHOTOS_PATH
from utils.utils import chunks

IMG_FILTER = re.compile(r'.+\.(jpg|png|jpeg|tif|tiff|gif)$', re.IGNORECASE)
VIDEO_FILTER = re.compile(r'.+\.(mov|mp4|avi)$', re.IGNORECASE)
ALL_FILTER = re.compile('|'.join([IMG_FILTER.pattern, VIDEO_FILTER.pattern]),
                        re.IGNORECASE)


def collect_photos(path_list):
    result = {}

    for p_path in path_list:
        result[p_path] = {}
        root_path = os.path.normpath(p_path)
        parent_folder_name = os.path.basename(root_path)

        logger.info("Root folder: %s", root_path)
        logger.info("Target folder: %s", parent_folder_name)

        for (folder_path, subfolder_names, filenames) in walk(root_path):
            # Skip hidden folders
            if os.path.basename(folder_path).startswith('.'): continue

            # Decode to unicode, filter photos\videos and skip hidden files
            photos_in_current_folder = [
                (folder_path + "/" + f).decode('utf-8')
                for f in filenames if ALL_FILTER.match(f)
                                      and not f.startswith('.')
            ]

            if photos_in_current_folder and subfolder_names:
                raise Exception("Error occurred while parsing folders: "
                                "Folder can't contain images and "
                                "folders at the same place")

            if photos_in_current_folder:
                f_path = folder_path.decode('utf-8')
                if f_path in result.keys():
                    raise Exception("Folder path already exist")

                relative_p = f_path[len(p_path):]

                result[p_path][relative_p] = photos_in_current_folder

    return result


def find_media_files():
    assert PHOTOS_PATH

    raw_result = collect_photos(PHOTOS_PATH)

    result = {"albums": {}}

    total_count = 0
    for parent_folder, folders in raw_result.items():
        for folder, files in folders.items():
            if not files: continue

            logger.info("(%d)---> \t %s", len(files), folder)
            total_count += len(files)

            result["albums"][folder] = {
                'files': files
            }

            # for file in files:
            #     result["albums"][f]['files'].append(file)

    logger.info("Total images: %d", total_count)

    # raw_input("Press enter to continue...")

    return result


def sync_files_with_db(files_tree):
    photos_to_upload = {root_path: {} for root_path in files_tree.keys()}
    total_new_photos = 0

    photos = set()
    for root_path, folders in files_tree.items():
        for folder, files_bundle in folders.items():
            files = files_bundle['files']

            logger.info('Album: %s', folder)
            logger.info("\tTotal photos: %d", len(files))

            for paths_chunk in chunks(files, 300):
                _photos = (
                    Photo
                        .select(Photo.local_path)
                        .where((Photo.local_path << paths_chunk))
                )

                photos.update(set(_photos))

            db_photos = {_p.local_path for _p in photos}

            logger.info("\tPhotos exist in DB: %d", len(db_photos))

            local_photos = set(files)
            new_photos = local_photos - db_photos

            if new_photos:
                photos_to_upload[root_path][folder] = {
                    'files':list(new_photos),
                    'album_uri': None,
                }
                total_new_photos += len(new_photos)
            else:
                logger.info(
                    "All photos already exist in DB. Upload skipped\n\n")

    del files_tree

    if total_new_photos:
        logger.info("Total new photos to upload: %d", total_new_photos)

    return photos_to_upload
