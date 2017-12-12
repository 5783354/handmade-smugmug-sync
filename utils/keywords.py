import gevent
from gevent import monkey

monkey.patch_all()

from gevent.queue import JoinableQueue
from unidecode import unidecode

from core.api import SmugmugAPI
from core.db import Photo
from settings import PHOTOS_PATH, logger

IGNORE_KEYWORDS_ENDSWITH = 'NIKON'


def get_keywords(photo_path):
    assert '/' in photo_path

    full_path = photo_path.strip('/')
    base_paths = [_p.strip('/') for _p in PHOTOS_PATH]
    path = None

    for p in base_paths:
        if full_path.startswith(p):
            path = full_path[len(p):]
            break
    keywords = [unidecode(_k).lower() for _k in path.split('/')[:-1] if _k]

    result = []
    for k in keywords:
        if k.endswith(IGNORE_KEYWORDS_ENDSWITH.lower()):
            continue
        else:
            result.append(k)

    assert path
    return result


def update_keywords():
    sm_api = SmugmugAPI()

    def worker():
        logger.info('[Worker started]')
        while True:
            item = q.get()
            try:
                sm_api.update_image_keywords(*item)
            finally:
                q.task_done()

    q = JoinableQueue(maxsize=100)
    for i in range(50):
        gevent.spawn(worker)

    photos = (
        Photo
            .select(Photo.local_path, Photo.ext_key)
            .where((Photo.status == 'uploaded'))
    )
    photos = list(photos)
    print("Total photos to update:", len(photos))
    cnt = 0
    for p in photos:
        cnt += 1
        print(cnt)
        keywords = get_keywords(p.local_path)
        q.put((p.ext_key, keywords))

    q.join()


if __name__ == '__main__':
    update_keywords()
