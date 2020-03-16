import pytest
import pytest_dependency

from py_objectstore import ArkivverketObjectStorage , MakeIterIntoFile

import hashlib
import os
import tempfile
import string
import random
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
    os.environ["BUCKET"] = "testcontainer"
    os.mkdir(f'{os.environ["LOCAL_FOLDER"]}/{os.environ["BUCKET"]}')


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
    checksum = hashlib.sha256()
    content = []
    # Generate a block of random data. Should be around 10KB (will be repeated 1024 times).
    rbytes = bytes(randomString(stringLength=chunk_size), 'utf-8')

    for i in range(0, no_of_chunks):
        checksum.update(rbytes)
        content.append(rbytes)
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
# First we test a streaming upload 
# Then we download
# Then we delete
# Then we upload the file again (non-stream)
# Then we stream a download

# When the session ends the objects gets deleted again.


@pytest.mark.dependency(depends=[])
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
    hash = hashlib.sha256()
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
    hash = hashlib.sha256()
    for chunk in stream:
        hash.update(chunk)
    assert checksum.digest() == hash.digest()

@pytest.mark.dependency(depends=["test_upload_file"])
def test_list_container():
    objects = storage.list_container(bucket)
    assert len(objects) == 1


@pytest.mark.dependency(depends=["test_upload_file"])
def test_streaming_iter_download():
    stream = storage.download_stream(bucket, objectname)
    fileobject = MakeIterIntoFile(stream)
    hash = hashlib.sha256()
    chunks = 0
    while True:
        chunk = fileobject.read(amount=chunk_size)
        if not chunk:
            break
        chunks = chunks + 1
        assert len(chunk) == chunk_size
        hash.update(chunk)
    assert checksum.digest() == hash.digest()
    assert chunks == no_of_chunks