#!/bin/bash

set -xe

DIVIDER="=============================="
HOST_LOG="host.log"
COORD_LOG="coordinator.log"

echo -n "" > "$HOST_LOG"
echo -n "" > "$COORD_LOG"
# tail -f "$HOST_LOG" >& >(sed 's/^/host: /') &
# HOST_TAIL_PID=$!
# tail -f "$COORD_LOG" >& >(sed 's/^/coordinator: /') &
# COORD_TAIL_PID=$!

echo "Running tests..."

echo "$DIVIDER"
echo "Running build.sh..."
echo "$DIVIDER"
./build.sh

echo "$DIVIDER"
echo "Running satgen.sh..."
echo "$DIVIDER"
./satgen.sh

echo "$DIVIDER"
echo "Running prepare.sh..."
echo "$DIVIDER"
./prepare.sh

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
echo "Running celestial2.bin..."
echo "$DIVIDER"
# move files
echo "Moving files..."
ssh "$INSTANCE_NAME" "sudo mv ./validator.img /celestial/validator.img"

# shut off dns server
echo "Shutting off systemd-resolved..."
ssh "$INSTANCE_NAME" "sudo systemctl stop systemd-resolved"

echo "Running celestial..."
ssh "$INSTANCE_NAME" sudo ./celestial2.bin --debug >> $HOST_LOG 2>&1 &
CELESTIAL_PID=$!

echo -n "Waiting for celestial to start."
for _ in {1..10} ; do
    echo -n "."
    sleep 1
done

echo "$DIVIDER"
echo "Running celestial coordinator..."
echo "$DIVIDER"
ssh "$INSTANCE_NAME" PYTHONUNBUFFERED=1 python3 celestial2.py satgen.zip "127.0.0.1:1969" >> $COORD_LOG 2>&1 &
COORDINATOR_PID=$!

# run for 10 minutes
echo "Running for 10 minutes... (Start time: $(date))"
sleep 600

echo "$DIVIDER"
echo "Killing celestial coordinator..."
echo "$DIVIDER"
# necessary to get SIGTERM to work
ssh "$INSTANCE_NAME" "sudo killall python3"
# kill "$COORDINATOR_PID"

echo "$DIVIDER"
echo "Killing celestial..."
echo "$DIVIDER"
# kill "$CELESTIAL_PID"
ssh "$INSTANCE_NAME" "sudo systemctl restart systemd-resolved"


# get the results
echo "$DIVIDER"
echo "Getting results..."
echo "$DIVIDER"
./getresults.sh

echo "$DIVIDER"
echo "Analyzing results..."
echo "$DIVIDER"
mkdir -p output
python3 analyze.py

echo "$DIVIDER"
echo "Done!"
echo "$DIVIDER"

kill "$COORDINATOR_PID"
kill "$CELESTIAL_PID"

# destroy the infrastructure
echo "Destroying infrastructure..."
echo "Run the following command to destroy the infrastructure:"
echo "terraform destroy -auto-approve"
# terraform destroy -auto-approve
