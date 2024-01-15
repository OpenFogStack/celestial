#
# This file is part of Celestial (https://github.com/OpenFogStack/celestial).
# Copyright (c) 2021 Tobias Pfandzelter, The OpenFogStack Team.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

FROM python:3.9-alpine AS build

RUN apk add --no-cache --update \
    make cmake gcc g++ libstdc++ git libxslt-dev libxml2-dev libc-dev \
    libffi-dev zlib-dev libxml2 zlib libtool autoconf automake \
    flex bison \
    && rm -rf /var/cache/apk/*

RUN pip3 install git+https://github.com/igraph/python-igraph

FROM python:3.9-slim

COPY --from=build /usr/local/lib/python3.9/site-packages/igraph /usr/local/lib/python3.9/site-packages/igraph
COPY --from=build /usr/local/bin/igraph /usr/local/bin/igraph

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt

COPY __init__.py .
COPY celestial.py .
COPY celestial celestial
COPY proto proto

CMD [ "config.toml" ]
ENTRYPOINT [ "python3", "./celestial.py" ]
