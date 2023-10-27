#!/bin/sh

set -xe

ROOT="../.."

# create cloud infrastructure
terraform init

terraform apply -auto-approve

GCP_ZONE="$(terraform output -json | jq -r '.zone.value')"
GCP_PROJECT="$(terraform output -json | jq -r '.project.value')"
# TEST_HOST_IP="$(terraform output -json | jq -r '.host_ip.value')"
# TEST_HOST_NAME="$(terraform output -json | jq -r '.host_name.value')"
TEST_HOST_ID="$(terraform output -json | jq -r '.host_id.value')"

gcloud config set project "$GCP_PROJECT"

# restart the machines
gcloud compute instances stop --zone="$GCP_ZONE" "$TEST_HOST_ID"
sleep 5
gcloud compute instances start --zone="$GCP_ZONE" "$TEST_HOST_ID"
sleep 5

terraform apply -auto-approve
# GCP_ZONE="$(terraform output -json | jq -r '.zone.value')"
# GCP_PROJECT="$(terraform output -json | jq -r '.project.value')"
# TEST_HOST_IP="$(terraform output -json | jq -r '.host_ip.value')"
TEST_HOST_NAME="$(terraform output -json | jq -r '.host_name.value')"
# TEST_HOST_ID="$(terraform output -json | jq -r '.host_id.value')"

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
