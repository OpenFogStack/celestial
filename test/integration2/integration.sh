#!/bin/bash

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
terraform init

terraform apply -auto-approve

GCP_ZONE="$(terraform output -json | jq -r '.zone.value')"
GCP_PROJECT="$(terraform output -json | jq -r '.project.value')"
TEST_HOST_NAME="$(terraform output -json | jq -r '.host_name.value')"
TEST_HOST_ID="$(terraform output -json | jq -r '.host_id.value')"

gcloud config set project "$GCP_PROJECT"

# restart the machines
gcloud compute instances stop --zone="$GCP_ZONE" "$TEST_HOST_ID"
sleep 5
gcloud compute instances start --zone="$GCP_ZONE" "$TEST_HOST_ID"
sleep 5

TEST_HOST_NAME="$(terraform output -json | jq -r '.host_name.value')"

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
INSTANCE_NAME="$(terraform output -json | jq -r '.host_name.value')"

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

# shut off dns server
# echo "Shutting off systemd-resolved..."
# ssh "$INSTANCE_NAME" "sudo systemctl stop systemd-resolved"

echo "Running test..."
ssh "$INSTANCE_NAME" "sudo /usr/local/go/bin/go test"

echo "$DIVIDER"
echo "Done!"
echo "$DIVIDER"

# destroy the infrastructure
echo "Destroying infrastructure..."
echo "Run the following command to destroy the infrastructure:"
echo "terraform destroy -auto-approve"
# terraform destroy -auto-approve
