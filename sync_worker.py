from ss import SmugSync
from utils.upload import upload_photos_in_pending


def sync():
    ss = SmugSync()
    ss.sync_structure()

if __name__ == '__main__':
    upload_photos_in_pending(with_failed=False)
    sync()
    upload_photos_in_pending(with_failed=False)
