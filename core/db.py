import datetime

import peewee
from peewee import *
from playhouse.sqlite_ext import SqliteExtDatabase

db = SqliteExtDatabase('smugmug.db')


class BaseModel(Model):
    class Meta:
        database = db


class Photo(BaseModel):
    local_path = TextField(unique=True)
    local_md5 = TextField(null=True)
    status = TextField(default='pending')
    upload_time = DateTimeField(default=datetime.datetime.now)

    ext_size = IntegerField(null=True)
    ext_file_name = TextField(null=True)
    ext_md5 = TextField(null=True)
    ext_key = TextField(null=True)
    ext_album_key = TextField(null=True)
    ext_album_name = TextField(null=True)
    folder_key = TextField(null=True)
    folder_name = TextField(null=True)
    log = TextField(null=True)


def init_db():
    try:
        db.connect()
        db.create_tables([Photo])
        print("DB initialized")
    except peewee.OperationalError:
        print("DB already initialized")


if __name__ == '__main__':
    init_db()
