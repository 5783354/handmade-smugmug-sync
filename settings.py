import logging
from logging.config import dictConfig

DEBUG = False
LOG_FILENAME = 'smugmug.log'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,

    'formatters': {
        'console': {
            'format': '[%(asctime)s][%(levelname)s] | %(message)s',
        },
        'file': {
            'format': '[%(asctime)s][%(levelname)s] %(name)s %(filename)s:%(funcName)s:%(lineno)d | %(message)s',
        },
    },

    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'console',
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'formatter': 'file',
            'when': 'D',
            'interval': 1,
            'utc': True,
            'filename': LOG_FILENAME,
            'backupCount': 15,
        },

    },
    'loggers': {
        '': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    }
}
dictConfig(LOGGING)

logger_peewee = logging.getLogger('peewee')
logger_peewee.setLevel(logging.INFO)
logger_peewee.addHandler(logging.StreamHandler())
logger = logging.getLogger('Smugmug-upload')

API_ORIGIN = 'http://api.smugmug.com'
OAUTH_ORIGIN = 'https://secure.smugmug.com'
ACCESS_TOKEN_URL = OAUTH_ORIGIN + '/services/oauth/1.0a/getAccessToken'
AUTHORIZE_URL = OAUTH_ORIGIN + '/services/oauth/1.0a/authorize'
BASE_URL = API_ORIGIN + '/api/v2'
REQUEST_TOKEN_URL = OAUTH_ORIGIN + '/services/oauth/1.0a/getRequestToken'

UPLOADING_WORKERS_COUNT = 8

PHOTOS_PATH = []

try:
    from settings_local import *
except ImportError:
    logger.waring("Local settings doesn't defined")
