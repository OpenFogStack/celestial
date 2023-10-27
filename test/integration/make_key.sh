#!/bin/sh

KEYFILE="id_ed255119"

# check if file exists
if [ -f "$KEYFILE" ]; then
    echo "File $KEYFILE exists..."
    exit 0
fi

ssh-keygen -t ed25519 -f "$KEYFILE" -N ""
mv "$KEYFILE.pub" ./rootfs/