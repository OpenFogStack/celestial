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

set -xe

# check that one argument is set
if [ $# -ne 1 ]; then
    echo "Usage: $0 <hosts>"
    exit 1
fi

# check that the argument is a number
if ! [ "$1" -eq "$1" ] 2>/dev/null; then
    echo "Argument must be a number"
    exit 1
fi

# check that the argument is greater than 0
if [ "$1" -lt 1 ]; then
    echo "Argument must be greater than 0"
    exit 1
fi

HOSTS="$1"

ROOT="../.."

# create cloud infrastructure
tofu init

tofu apply -auto-approve --var "hosts=$HOSTS"

GCP_ZONE="$(tofu output -json | jq -r '.zone.value')"
GCP_PROJECT="$(tofu output -json | jq -r '.project.value')"

TEST_HOST_IDS=()
for ((i=0;i<HOSTS;i++)); do
    TEST_HOST_IDS+=("$(tofu output -json | jq -r ".host_id.value[$i]")")
done

gcloud config set project "$GCP_PROJECT"

# restart the machines
for ((i=0;i<HOSTS;i++)); do
    gcloud compute instances stop --zone="$GCP_ZONE" "${TEST_HOST_IDS[$i]}" &
done
wait
sleep 5

for ((i=0;i<HOSTS;i++)); do
    gcloud compute instances start --zone="$GCP_ZONE" "${TEST_HOST_IDS[$i]}" &
done
wait

TEST_HOST_NAMES=()
for ((i=0;i<HOSTS;i++)); do
    TEST_HOST_NAMES+=("$(tofu output -json | jq -r ".host_name.value[$i]")")
done

gcloud compute config-ssh

for ((i=0;i<HOSTS;i++)); do
    (TEST_HOST_NAME="${TEST_HOST_NAMES[$i]}"
    # wait until the host is ready
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
    ) &
done
wait
