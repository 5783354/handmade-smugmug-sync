from __future__ import absolute_import

import gevent
from gevent import monkey

monkey.patch_all(httplib=True)

from gevent.queue import JoinableQueue

import argparse
import json
import os
from mimetypes import guess_type
from os import path
from time import sleep

from core.api import SmugmugAPI
from core.db import db, Photo
from settings import (
    DEBUG,
    logger,
    UPLOADING_WORKERS_COUNT,
)
from utils.md5 import get_md5
from utils.keywords import get_keywords


def upload_photo(photo_item):
    api = SmugmugAPI()
    attempts = 5
    img_path, album_uri = photo_item

    while attempts:
        try:
            file_name = os.path.basename(img_path)
            headers = {
                'User-Agent': 'Safari',
                'X-Smug-ResponseType': 'JSON',
                'X-Smug-Version': 'v2',
                'Content-Type': guess_type(file_name)[0],
                'X-Smug-AlbumUri': album_uri,
                'X-Smug-FileName': file_name,
                'Content-Length': str(path.getsize(img_path)),
                'Content-MD5': get_md5(img_path),
                'X-Smug-Keywords': get_keywords(img_path),
            }

            if DEBUG:
                logger.debug(["Uploading:", img_path, 'to:', album_uri])

            with open(img_path, "rb") as f:
                data = f.read()

                response = api.r.post(
                    'http://upload.smugmug.com/',
                    headers=headers,
                    data=data,
                    header_auth=True)

                r = json.loads(response.content) or {}

                del data

                if r.get('stat') == 'ok':

                    logger.info('\t\tPhoto uploaded: %s', file_name)
                    field_data = {
                        "status": "uploaded",
                        "ext_key": r.get('Image').get('ImageUri'),
                        "ext_album_key": album_uri,
                    }

                    with db.atomic():
                        Photo.update(**field_data).where(
                            (Photo.local_path == img_path)).execute()

                    break

                else:
                    logger.exception(
                        "Something goes wrong while uploading image")
                    try:
                        log = "\n".join([
                            str(response.content),
                            str(headers),
                            str(response.headers),
                            str(response.status_code),
                            str(response.reason)])
                    except Exception:
                        logger.exception(
                            "Something goes wrong while uploading image")
                        log = None

                    field_data = {
                        "status": "failed",
                        "log": log
                    }

                    with db.atomic():
                        Photo.update(**field_data).where(
                            (Photo.local_path == img_path)).execute()

                    raise Exception("stat is not OK")


        except Exception:
            sleep(5)
            attempts -= 1

            field_data = {
                "status": "failed",
            }

            with db.atomic():
                Photo.update(**field_data).where(
                    (Photo.local_path == img_path)).execute()


def upload_photos_in_pending(with_failed=True):
    q_filter = ['pending']
    if with_failed:
        q_filter.append('failed')

    photos = (
        Photo
            .select(Photo.local_path, Photo.ext_album_key)
            .where((Photo.status << q_filter))
    )
    photos = list(photos)

    def worker():
        logger.info('[New worker started]')
        while True:
            item = q.get()
            try:
                upload_photo(item)
            finally:
                q.task_done()

    q = JoinableQueue(maxsize=10)
    for i in range(UPLOADING_WORKERS_COUNT):
        gevent.spawn(worker)

    for p in photos:
        q.put((p.local_path, p.ext_album_key))

    q.join()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Reupload photos after fails"
    )
    parser.add_argument(
        '-p', '--only_pending',
        help='Upload only pending photos',
        default=False,
    )

    args = parser.parse_args()

    with_failed = True

    if args.only_pending:
        with_failed = False

    upload_photos_in_pending(with_failed=with_failed)
