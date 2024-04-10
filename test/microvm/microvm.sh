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

# the -no-reboot flag is used to prevent the instance from rebooting
REBOOT=1

# the other argument is the host: ip address or gcloud
TEST_HOST=""

for i in "$@"
do
case $i in
    -no-reboot)
    REBOOT=0
    shift # past argument=value
    ;;
    -host=*)
    TEST_HOST="${i#*=}"
    shift # past argument=value
    ;;
    *)
          # unknown option
    ;;
esac
done

# check that the host is set
if [ -z "$TEST_HOST" ]; then
    echo "No host set!"
    echo "Please set the host with -host=... or use -host=gcloud to use terraform"
    exit 1
fi

set -xe

DIVIDER="=============================="
ROOT="../.."

pushd "$ROOT"
make rootfsbuilder
popd

pushd rootfs
make -B
popd

echo "$DIVIDER"
echo "Running preparation..."
echo "$DIVIDER"

./make_key.sh

# make the infrastructure if we use gcloud
if [ "$TEST_HOST" == "gcloud" ]; then
    tofu init
    tofu apply -auto-approve

    GCP_ZONE="$(tofu output -json | jq -r '.zone.value')"
    GCP_PROJECT="$(tofu output -json | jq -r '.project.value')"
    GCR_INSTANCE_FULL="$(tofu output -json | jq -r '.host_name.value')"
    GCP_INSTANCE="$(tofu output -json | jq -r '.host_id.value')"

    gcloud config set project "$GCP_PROJECT"
    SSH_ADDRESS="$GCR_INSTANCE_FULL"
else
    SSH_ADDRESS="$TEST_HOST"
fi

if [ "$REBOOT" -eq 1 ]; then
    if [ "$TEST_HOST" == "gcloud" ]; then
        # restart the machines
        gcloud compute instances stop --zone="$GCP_ZONE" "$GCP_INSTANCE"
        sleep 1
        gcloud compute instances start --zone="$GCP_ZONE" "$GCP_INSTANCE"

        gcloud compute config-ssh
    else
        # at least reboot the machine
        ssh "$SSH_ADDRESS" sudo reboot now || true
    fi
fi

until ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 "$SSH_ADDRESS" echo
do
    echo "host instance not ready yet"
    sleep 5
    if [ "$TEST_HOST" == "gcloud" ]; then
        # make sure we have the right config
        gcloud compute config-ssh
    fi
done

ssh "$SSH_ADDRESS" sudo apt-get update
ssh "$SSH_ADDRESS" sudo apt-get install \
    --no-install-recommends \
    --no-install-suggests \
    -y rsync

# copy the necessary files
while read -r f; do
    # check if the file or directory exists
    if [ ! -e "$ROOT/$f" ]; then
        echo "File or directory $f does not exist!"
        exit 1
    fi

    rsync -avz "$ROOT/$f" "$SSH_ADDRESS":
done <fileslist.txt

echo "$DIVIDER"
echo "Running dependencies.sh..."
echo "$DIVIDER"
# check that the file is there on the host
ssh "$SSH_ADDRESS" "ls -la dependencies.sh" || echo "File dependencies.sh not found on host!"
echo "The following commands will be run on the host..."
ssh "$SSH_ADDRESS" "./dependencies.sh"
echo "Done running dependencies.sh on host"

echo "$DIVIDER"
echo "Running run_microvm.sh..."
echo "$DIVIDER"
ssh "$SSH_ADDRESS" "sudo ./run_microvm.sh"

echo "$DIVIDER"
echo "Done!"
echo "$DIVIDER"

# destroy the infrastructure if using gcloud
if [ "$TEST_HOST" == "gcloud" ]; then
    echo "Destroying infrastructure..."
    echo "Run the following command to destroy the infrastructure:"
    echo "tofu destroy -auto-approve"
    # tofu destroy -auto-approve
fi
