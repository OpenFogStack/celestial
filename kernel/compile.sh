#!/bin/bash

set -ex

INPUT="$1"
KERNEL_VERSION="$2"
OUTPUT="$3"

# check that $INPUT/config-$KERNEL_VERSION exists
# if not, give an error
if [ ! -f "${INPUT}/config-${KERNEL_VERSION}" ]; then
    echo "FATAL: config-${KERNEL_VERSION} does not exist in ${INPUT}"
    exit 1
fi

pushd /linux.git

# then checkout the version you want, e.g. v4.19
git checkout "v${KERNEL_VERSION}"

cp "${INPUT}/config-${KERNEL_VERSION}" .config

make vmlinux -j

cp vmlinux "${OUTPUT}/vmlinux-${KERNEL-VERSION}.bin"
