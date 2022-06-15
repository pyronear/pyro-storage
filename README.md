# Data curation API

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE) ![Build Status](https://github.com/pyronear/pyro-storage/workflows/api/badge.svg) [![codecov](https://codecov.io/gh/pyronear/pyro-storage/branch/main/graph/badge.svg)](https://codecov.io/gh/pyronear/pyro-storage)

The building blocks of our data curation API.



## Getting started

### Prerequisites

- Python 3.7 (or more recent)
- [pip](https://pip.pypa.io/en/stable/)

### Installation

You can clone and install the project dependencies as follows:

```shell
git clone https://github.com/pyronear/pyro-storage.git
```

## Usage

If you wish to deploy this project on a server hosted remotely, you might want to be using [Docker](https://www.docker.com/) containers. Beforehand, you will need to set a few environment variables either manually or by writing an `.env` file in the root directory of this project, like in the example below:

```
QARNOT_TOKEN=my_very_secret_token
BUCKET_NAME=my_storage_bucket_name
BUCKET_MEDIA_FOLDER=my/media/subfolder
BUCKET_ANNOT_FOLDER=my/annotations/subfolder

```

Those values will allow your API server to connect to our cloud service provider [Qarnot Computing](https://qarnot.com/), which is mandatory for your local server to be fully operational.
Then you can run the API containers using this command:

```shell
docker-compose up -d --build
```

Once completed, you will notice that you have a docker container running on the port you selected, which can process requests just like any django server.



## Documentation

The full project documentation is available [here](http://pyro-storage.herokuapp.com/redoc) for detailed specifications. The documentation was built with [ReDoc](https://redocly.github.io/redoc/).



## Contributing

Please refer to `CONTRIBUTING` if you wish to contribute to this project.



## License

Distributed under the Apache 2.0 License. See [`LICENSE`](LICENSE) for more information.