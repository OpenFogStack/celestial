#!/bin/bash

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
