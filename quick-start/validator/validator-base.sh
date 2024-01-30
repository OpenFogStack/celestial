#!/bin/sh

#
# This file is part of Celestial (https://github.com/OpenFogStack/celestial).
# Copyright (c) 2024 Tobias Pfandzelter, The OpenFogStack Team.
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

# Our base script installs all the necessary dependencies for the validation
# script. This is actually only Python 3 and a few Python 3 packages.

# Add git, curl, and python3 to the root filesystem.
# git and curl are needed for pip.
apk add git curl python3 py3-pip

# Add the python3 dependencies: request and ping3
python3 -m pip install ping3 requests
