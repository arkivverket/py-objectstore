import pytest
import pytest_dependency

from py_objectstore import ArkivverketObjectStorage , MakeIterIntoFile
from libcloud.storage.types import ObjectDoesNotExistError

import hashlib
import os
import tempfile
import string
import random
import uuid

try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    print("Could not load .env file. ")


# If objectstore is not set, assume we're in the CI pipeline and we
# need to populate our own environment.
if not 'OBJECTSTORE' in os.environ:
    os.environ["OBJECTSTORE"] = "local"
    os.environ["LOCAL_FOLDER"] = tempfile.mkdtemp()
    os.environ["BUCKET"] = str(uuid.uuid4())
    
    # os.mkdir(f'{os.environ["LOCAL_FOLDER"]}/{os.environ["BUCKET"]}')


# must a factor of 1024 so the file operations can assert
chunk_size = 1024
no_of_chunks = 10240
#
# Helper functions...
#

def randomString(stringLength=10):
    """Generate a random string of fixed length """
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(stringLength))


def make_random_data():
    checksum = hashlib.md5()
    content = []
    # Generate a block of random data. Should be around 10KB (will be repeated 1024 times).
    rbytes = bytes(randomString(stringLength=chunk_size), 'utf-8')

    for _ in range(0, no_of_chunks):
        checksum.update(rbytes)
        content.append(rbytes)
    print("Generated random data with checksum", checksum.hexdigest())
    return content, checksum


# Initialize stuff.

# Define global storage object that the tests use.
storage = ArkivverketObjectStorage()
bucket = os.environ["BUCKET"] # convenient.
objectname = randomString()

global object_content
global checksum

object_content = None
checksum = None
# checksum = make_random_data()




@pytest.fixture(scope="session", autouse=True)
def housekeeping():
    global object_content
    global checksum
    object_content, checksum = make_random_data()
    yield
    storage.delete(bucket, objectname)
    os.remove(objectname)
    return None
    # cleanup()

# ================ TESTS ===============

# This is how this works:
# First we create a container
# Then we test a streaming upload 
# Then we iterate over the container...
# Then we download
# Then we delete
# Then we upload the file again (non-stream)
# Then we stream a download
# Then we stream a download of a non-existent file...

# When the session ends the objects gets deleted again.

@pytest.mark.dependency(depends=[])
def test_create_container():
    print(f'Creating container {bucket}')
    c = storage.create_container(bucket)

    objs = len(list(storage.list_container(bucket)))
    print("Container contents:", objs)
    assert objs == 0
    assert c != None



@pytest.mark.dependency(depends=["test_create_container"])
def test_streaming_upload():
    list = iter(object_content)
    objects = storage.list_container(bucket)
    assert len(objects) == 0
    storage.upload_stream(container=bucket, name=objectname, iterator=list)
    objects = storage.list_container(bucket)
    assert len(objects) == 1


@pytest.mark.dependency(depends=["test_streaming_upload"])
def test_download():
    storage.download_file(bucket, objectname, objectname)
    hash = hashlib.md5()
    with open(objectname,"rb") as f:
        for chunk in f:
            hash.update(chunk)

    assert checksum.digest() == hash.digest()



    



@pytest.mark.dependency(depends=["test_download"])
def test_delete():
    objects = storage.list_container(bucket)
    assert len(objects) == 1
    storage.delete(bucket, objectname)
    objects = storage.list_container(bucket)
    print(objects)
    assert len(objects) == 0


@pytest.mark.dependency(depends=["test_delete"])
def test_upload_file():
    objects = storage.list_container(bucket)
    assert len(objects) == 0
    storage.upload_file(container=bucket, name=objectname, file=objectname)
    objects = storage.list_container(bucket)
    assert len(objects) == 1

@pytest.mark.dependency(depends=["test_upload_file"])
def test_streaming_download():
    stream = storage.download_stream(bucket, objectname)
    hash = hashlib.md5()
    for chunk in stream:
        hash.update(chunk)
    assert checksum.digest() == hash.digest()

@pytest.mark.dependency(depends=["test_upload_file"])
def test_streaming_download_invalidname():
    with pytest.raises(ObjectDoesNotExistError):
        storage.download_stream(bucket, objectname + "XXX", objectname)
        with open(objectname,"rb") as f:
            for _ in f:
                pass


@pytest.mark.dependency(depends=["test_upload_file"])
def test_list_container():
    objects = storage.list_container(bucket)
    assert len(objects) == 1


@pytest.mark.dependency(depends=["test_upload_file"])
def test_streaming_iter_download():
    stream = storage.download_stream(bucket, objectname)
    fileobject = MakeIterIntoFile(stream)
    hash = hashlib.md5()
    chunks = 0
    while True:
        chunk = fileobject.read(amount=chunk_size)

        if not chunk:
            break
        chunks = chunks + 1
        assert len(chunk) == chunk_size
        hash.update(chunk)
    position = fileobject.tell()
    assert position == chunk_size * no_of_chunks
    fileobject.close()
    assert checksum.digest() == hash.digest()
    assert chunks == no_of_chunks

@pytest.mark.dependency(depends=["test_upload_file"])
def test_get_size():
    size = storage.get_size(bucket, objectname)
    assert size == no_of_chunks * chunk_size



def test_delete_invalid_file():
    with pytest.raises(ObjectDoesNotExistError):
        storage.delete(bucket, objectname + "invalid")
