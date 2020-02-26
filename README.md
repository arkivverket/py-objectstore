# ArkivverketObjectStorage - Simple object storage API for The National Archieves of Norway.

The goal is to abstract the details and provide a super-simple API towards various object
storage solutions.

Currently the API is implemented using Apache Libcloud and will only support a verified subset
of Libcloud.

The API is not meant for use outside the National Archieves. But for all means, go ahead. It´s open source.

## Using this with Poetry.
To add this to a Poetry project put something like this in your `pyproject.toml`

```
[tool.poetry.dependencies]
python = "^3.7"
py-objectstore = { git = "https://github.com/arkivverket/py-objectstore.git" }
```

The proceed and do ```poetry install``` as you otherwise would.

## Example usage for local file access

Say you have a folder that will act as a root for the objectstore. Say we use `/mnt/disk1`. In this folder there in another folder `data1` which contains the files we wanna access.

In order to make this work you need the following environment variables to be set. For local development I recommend looking at the python-dotenv library to make loading of env variables easy.

```
OBJECTSTORE=local
LOCAL_FOLDER=/mnt/disk1
```

So say we wanna iterate over the files and do some stuff with them:
```
#!/usr/bin/env python
from py_objectstore import ArkivverketObjectStorage
bucket = 'data1' # you might wanna get this from an environment variable.
storage = ArkivverketObjectStorage()
objects = iter(storage.list_container(bucket))

for file in objects:
    print(f'Processing {file} now')
    stream = storage.download_stream(bucket, file)
    # at this point the stream is a iterator
    for chunk in stream:
        print(f'Got chunk of ', len(chunk))
        # do fancy machine learnings here....
```

The output might look something like this:
```
./test.py                                     
Processing 1.pdf now
Got chunk of  1048760
Processing 2.pdf now
Got chunk of  1485761
...
```
