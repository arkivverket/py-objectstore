# ArkivverketObjectStorage - Simple object storage API for The National Archieves of Norway.

The goal is to abstract the details and provide a super-simple API towards various object
storage solutions.

Currently the API is implemented using Apache Libcloud and will only support a verified subset
of Libcloud.

The API is not meant for use outside the National Archieves. But for all means, go ahead. It´s open source.

## Testing, release and build

The project uses Pytest and should have decent test coverage. It uses local storage for testing. If you wanna test against a cloud storage provider you need to do so by hand by setting the required environment variables in the .env file and run pytest. If the environment variable OBJECTSTORE isn't set the test scripts will fall back to local storage.

This project is built by Azure Pipelines. CI tasks are run on all commits in all branches. Uploads happen when we push a tag. So, to release a new version run the following

```
$ bump2version (major|minor|patch)

$ git push --tags

```

A new version then gets uploaded to the Azure Artifact Feed where it can be consumed by other projects. Note that the container registry and Pypi repos are private so outside the archives you'll need to pull via Git.

There is built in support for the following objectstores:

- Google Cloud Storage
- Azure Blob Storage
- Minio storage gateways. This is mostly S3, but with some hash verification turned off as the S3 protocol was designed by people who never bothered to read the HTTP spec.

## Pulling wheels via Poetry from the National Archives

Please see internal documentation about how to access the pypi feeds in Azure.



## Using this through git

To add this to a Poetry project put something like this in your `pyproject.toml`

```
[tool.poetry.dependencies]
python = "^3.7"
py-objectstore = { git = "https://github.com/arkivverket/py-objectstore.git" }
```

The proceed and do `poetry install` as you otherwise would.

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
