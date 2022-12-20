# Data curation API

<p align="center">
  <a href="https://github.com/pyronear/pyro-storage/actions?query=workflow%3Abuilds">
    <img alt="CI Status" src="https://img.shields.io/github/actions/workflow/status/pyronear/pyro-storage/builds.yml?branch=main&label=CI&logo=github&style=flat-square">
  </a>
  <a href="http://pyronear-api.herokuapp.com/redoc">
    <img src="https://img.shields.io/github/actions/workflow/status/pyronear/pyro-storage/builds.yml?branch=main&label=docs&logo=read-the-docs&style=flat-square" alt="Documentation Status">
  </a>
  <a href="https://codecov.io/gh/pyronear/pyro-storage">
    <img src="https://img.shields.io/codecov/c/github/pyronear/pyro-storage.svg?logo=codecov&style=flat-square" alt="Test coverage percentage">
  </a>
  <a href="https://github.com/ambv/black">
    <img src="https://img.shields.io/badge/code%20style-black-000000.svg?style=flat-square" alt="black">
  </a>
  <a href="https://www.codacy.com/gh/pyronear/pyro-storage/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=pyronear/pyro-storage&amp;utm_campaign=Badge_Grade"><img src="https://app.codacy.com/project/badge/Grade/da9d595af69348b5882a6eec791a6acd"/></a>
</p>
<p align="center">
  <a href="https://pypi.org/project/pyrostorage/">
    <img src="https://img.shields.io/pypi/v/pyrostorage.svg?logo=python&logoColor=fff&style=flat-square" alt="PyPi Status">
  </a>
  <a href="https://anaconda.org/pyronear/pyrostorage">
    <img alt="Anaconda" src="https://img.shields.io/conda/vn/pyronear/pyrostorage?style=flat-square?style=flat-square&logo=Anaconda&logoColor=white&label=conda">
  </a>
  <a href="https://hub.docker.com/r/pyronear/pyro-storage">
    <img alt="Docker Image Version" src="https://img.shields.io/docker/v/pyronear/pyro-storage?style=flat-square&logo=Docker&logoColor=white&label=docker">
  </a>
  <img src="https://img.shields.io/pypi/pyversions/pyrostorage.svg?style=flat-square" alt="pyversions">
  <img src="https://img.shields.io/pypi/l/pyrostorage.svg?style=flat-square" alt="license">
</p>


The building blocks of our data curation API.

## Quick Tour

### Running/stopping the service

You can run the API containers using this command:

```shell
make run
```

You can now navigate to `http://localhost:8080/docs` to interact with the API (or do it through HTTP requests) and explore the documentation.

In order to stop the service, run:
```shell
make stop
```

### How is the database organized

The back-end core feature is to interact with the metadata tables. For the service to be useful for data curation, multiple tables/object types are introduced and described as follows:

#### Access-related tables

- Accesses: stores the hashed credentials and access level for users & devices.

#### Core data curation worklow tables

- Media: metadata of a picture and its storage bucket key.
- Annotations: metadata of an annotation file and its storage bucket key.

![UML](https://github.com/pyronear/pyro-storage/releases/download/v0.1.0/uml_diagram.png)

### What is the full data curation workflow through the API

The API has been designed to provide, for each data entry:
- timestamp
- the picture that was uploaded
- the annotation file associated with that picture

With the previously described tables, here are all the steps to upload a data entry:
- Prerequisites (ask the instance administrator): register user
- Create a media object & upload content: save the picture metadata and upload the image content.
- Create an annotation object & upload content: save the annotation metadata and upload the annotation content.

## Installation

### Prerequisites

- [Docker](https://docs.docker.com/engine/install/)
- [Docker compose](https://docs.docker.com/compose/)
- [Make](https://www.gnu.org/software/make/) (optional)

The project was designed so that everything runs with Docker orchestration (standalone virtual environment), so you won't need to install any additional libraries.

## Configuration

In order to run the project, you will need to specific some information, which can be done using a `.env` file.
This file will have to hold the following information:
- `QARNOT_TOKEN`: this will enable the back-end access to the storage service of [Qarnot Computing](https://qarnot.com/)
- `BUCKET_NAME`: the name of the storage bucket
- `BUCKET_MEDIA_FOLDER`: the folder to place media content in
- `BUCKET_ANNOT_FOLDER`: the folder to place annotations in

Optionally, the following information can be added:
- `SENTRY_DSN`: the URL of the [Sentry](https://sentry.io/) project, which monitors back-end errors and report them back.
- `SENTRY_SERVER_NAME`: the server tag to apply to events.

So your `.env` file should look like something similar to:
```
QARNOT_TOKEN=my_very_secret_token
BUCKET_NAME=my_storage_bucket_name
BUCKET_MEDIA_FOLDER=my/media/subfolder
BUCKET_ANNOT_FOLDER=my/annotations/subfolder
SENTRY_DSN='https://replace.with.you.sentry.dsn/'
SENTRY_SERVER_NAME=my_storage_bucket_name
```

The file should be placed at the root folder of your local copy of the project.

## More goodies

### Documentation

The full package documentation is available [here](https://pyronear.org/pyro-storage) for detailed specifications.

### Python client

This project is a REST-API, and you can interact with the service through HTTP requests. However, if you want to ease the integration into a Python project, take a look at our [Python client](client).


## Contributing

Any sort of contribution is greatly appreciated!

You can find a short guide in [`CONTRIBUTING`](CONTRIBUTING.md) to help grow this project!



## License

Distributed under the Apache 2.0 License. See [`LICENSE`](LICENSE) for more information.