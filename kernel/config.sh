#!/bin/bash
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

set -ex

INPUT="$1"
KERNEL_VERSION="$2"

# check that $INPUT/config-$KERNEL_VERSION exists
# if yes, do not overwrite
if [ -f "${INPUT}/config-${KERNEL_VERSION}" ]; then
    echo "config-${KERNEL_VERSION} exists in ${INPUT}, skipping..."
    exit 0
fi

pushd /linux.git

# then checkout the version you want, e.g. v4.19
git checkout "v${KERNEL_VERSION}"

make defconfig

# enable CONFIG_RANDOM_TRUST_CPU
sed -i 's/# CONFIG_RANDOM_TRUST_CPU is not set/CONFIG_RANDOM_TRUST_CPU=y/' .config

cp .config "${INPUT}/config-${KERNEL_VERSION}"
