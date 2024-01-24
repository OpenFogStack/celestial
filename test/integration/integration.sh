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
for i in "$@"
do
case $i in
    -no-reboot)
    REBOOT=0
    shift # past argument=value
    ;;
    *)
          # unknown option
    ;;
esac
done

set -xe

DIVIDER="=============================="
ROOT="../.."

pushd "$ROOT"
make rootfsbuilder
popd

pushd rootfs
make
popd

echo "$DIVIDER"
echo "Running preparation..."
echo "$DIVIDER"

./make_key.sh

# create cloud infrastructure
tofu init

tofu apply -auto-approve

GCP_ZONE="$(tofu output -json | jq -r '.zone.value')"
GCP_PROJECT="$(tofu output -json | jq -r '.project.value')"
TEST_HOST_NAME="$(tofu output -json | jq -r '.host_name.value')"
TEST_HOST_ID="$(tofu output -json | jq -r '.host_id.value')"

gcloud config set project "$GCP_PROJECT"

# restart the machines unless the -no-reboot flag is set
if [ "$REBOOT" -eq 1 ]; then
    gcloud compute instances stop --zone="$GCP_ZONE" "$TEST_HOST_ID"
    sleep 5
    gcloud compute instances start --zone="$GCP_ZONE" "$TEST_HOST_ID"
    sleep 5
fi

TEST_HOST_NAME="$(tofu output -json | jq -r '.host_name.value')"

gcloud compute config-ssh

until ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 "$TEST_HOST_NAME" echo
do
  echo "host instance not ready yet"
  sleep 5
  # make sure we have the right config
  gcloud compute config-ssh
done

ssh "$TEST_HOST_NAME" sudo apt-get update
ssh "$TEST_HOST_NAME" sudo apt-get install \
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

    rsync -avz "$ROOT/$f" "$TEST_HOST_NAME":
done <fileslist.txt

gcloud compute config-ssh
INSTANCE_NAME="$(tofu output -json | jq -r '.host_name.value')"

echo "$DIVIDER"
echo "Running dependencies.sh..."
echo "$DIVIDER"
# check that the file is there on the host
ssh "$INSTANCE_NAME" "ls -la dependencies.sh" || echo "File dependencies.sh not found on host!"
echo "The following commands will be run on the host..."
ssh "$INSTANCE_NAME" "./dependencies.sh"
echo "Done running dependencies.sh on host"

echo "$DIVIDER"
# move files
echo "Moving files..."
echo "$DIVIDER"
ssh "$INSTANCE_NAME" "sudo mv ./ssh.img /celestial/ssh.img"

echo "Running test..."
ssh "$INSTANCE_NAME" "sudo /usr/local/go/bin/go test"

echo "$DIVIDER"
echo "Done!"
echo "$DIVIDER"

# destroy the infrastructure
echo "Destroying infrastructure..."
echo "Run the following command to destroy the infrastructure:"
echo "tofu destroy -auto-approve"
# tofu destroy -auto-approve
