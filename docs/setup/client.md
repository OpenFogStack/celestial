---
layout: default
title: Client
parent: Setup
nav_order: 1
---

## Client

You have two options to run the client software: either with Python3 or with
Docker.
Docker is obviously a bit easier but running it directly lets you activate the
cool animation as well.

In order to use the database feature (more about that in the [Services](#services)
section), you must open a TCP port of your choice on your client, and it must be
reachable from your servers.

### Python3

To run the client with Python3, make sure you have `python3` and `pip`/`pip3` installed.
We recommend setting up a virtual environment (`venv`) for Celestial:

```sh
python3 -m venv .venv
source .venv/bin/activate
```

Install the dependencies with:

```sh
python3 -m pip install -r requirements.txt
```

Additionally, install the `VTK` and `seaborn` packages to enable the animation
(requires a somewhat up-to-date computer):

```sh
python3 -m pip install vtk
python3 -m pip install seaborn
```

Then run the client with:

```sh
python3 celestial.py [YOUR-CONFIG-FILE]
```

### Docker

To run the client from within Docker, have `docker` installed and run:

```sh
# build the container
# this builds python-igraph from source, don't worry if it takes a while
docker build -t celestial .
# run the container with your config file mapped as a volume
docker run --rm -it -v $(pwd)/[YOUR-CONFIG-FILE]:/config.toml celestial /config.toml
```

This maps your config file as a volume within the container.
If you set `animation = true` within that config file, you will probably run
into errors, so don't do it.

If you want to enable the database, e.g., on port `8000`, instruct Docker to
forward that port:

```sh
docker run --rm -it -p8000:8000 \
    -v $(pwd)/[YOUR-CONFIG-FILE]:/config.toml \
    celestial /config.toml
```
