import hashlib
from os import makedirs
from uuid import uuid4

from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from fslc_stream.db.models import Resource


class ResourceUploadError(Exception):
    message: str

    def __init__(self, message: str):
        self.message = message


def save_resource(storage: FileStorage) -> Resource:
    rid = uuid4();

    if storage.filename is None:
        raise ResourceUploadError("The file must have a filename.")

    real_filename = secure_filename(storage.filename)

    if not (1 <= len(real_filename) <= 100):
        raise ResourceUploadError("The filename must be between 1 and 100 characters.")

    dir = f"/var/stream/resources/{rid}"
    path = f"{dir}/{real_filename}"
    makedirs(dir, exist_ok=True)
    f = open(path, "wb") 
    # simultaneously build up a hash and save the file
    hash = hashlib.sha256()
    buf = bytearray(b'\x00'*4096)
    size = 0

    while bytesread := storage.stream.readinto(buf):
        hash.update(buf)
        f.write(buf)
        size += bytesread;

    f.close()

    return Resource(
        id=rid,
        filename=real_filename,
        filesize=size,
        content_hash = hash.digest(),
    )
