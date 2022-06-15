# API Client

![Build Status](https://github.com/pyronear/pyro-storage/workflows/client/badge.svg)  [![Docs](https://img.shields.io/badge/docs-available-blue.svg)](http://pyronear.org/pyro-storage)

Client for the [data curation API](https://github.com/pyronear/pyro-storage)


## Getting started

### Prerequisites

- Python 3.6 (or more recent)
- [pip](https://pip.pypa.io/en/stable/)

### Installation

You can clone and install the project dependencies as follows:

```bash
$git clone https://github.com/pyronear/pyro-storage.git
$pip install -e pyro-storage/client/.
```



## Usage

Import the client

```python
from pyrostorage import client
```

Create a client object by handling him the API keys

```python
API_URL = "http://pyronear-storage.herokuapp.com"
CREDENTIALS_LOGIN = "George Abitbol"
CREDENTIALS_PASSWORD = "AStrong Password"
api_client = client.Client(API_URL, CREDENTIALS_LOGIN, CREDENTIALS_PASSWORD)
```

Use it to query alerts:
```python

## Create a media
media_id = api_client.create_media().json()["id"]

## Upload an image on the media
dummy_image = "https://ec.europa.eu/jrc/sites/jrcsh/files/styles/normal-responsive/" \
                + "public/growing-risk-future-wildfires_adobestock_199370851.jpeg"
image_data = requests.get(dummy_image)
api_client.upload_media(media_id=media_id, media_data=image_data.content)

## Create an annotation
dummy_annotation = "https://raw.githubusercontent.com/anishathalye/imagenet-simple-labels/" \
					+ "master/imagenet-simple-labels.json"
annotation_id = api_client.create_annotation(media_id=media_id).json()["id"]
annot_data = requests.get(dummy_annotation)
api_client.upload_annotation(annotation_id=annotation_id, annotation_data=annot_data.content)

```


## License

Distributed under the Apache 2.0 License. See [`LICENSE`](LICENSE) for more information.



## Documentation

The full project documentation is available [here](http://pyronear.org/pyro-storage) for detailed specifications. The documentation was built with [Sphinx](https://www.sphinx-doc.org/) using a [theme](https://github.com/readthedocs/sphinx_rtd_theme) provided by [Read the Docs](https://readthedocs.org/).

