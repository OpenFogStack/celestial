#!/bin/bash

set -xe


# figure out the amount of hosts to use
# if the --hosts flag is set, use that
# if the --hosts flag is not set, use the default of 1

NUM_HOSTS=1

while [[ $# -gt 0 ]]
do
key="$1"

case $key in
    -h|--hosts)
    NUM_HOSTS="$2"
    echo "--hosts set to $NUM_HOSTS"
    shift # past argument
    shift # past value
    ;;
    *)    # unknown option
    echo "Unknown option $1"
    exit 1
    ;;
esac
done

echo "Using $NUM_HOSTS hosts"

DIVIDER="=============================="
HOST_LOGS=()
for ((i=0;i<NUM_HOSTS;i++)); do
    HOST_LOGS+=("host$i.log")
done
COORD_LOG="coordinator.log"

for ((i=0;i<NUM_HOSTS;i++)); do
    echo -n "" > "${HOST_LOGS[$i]}"
done
echo -n "" > "$COORD_LOG"

echo "Running tests..."

echo "$DIVIDER"
echo "Running build.sh..."
echo "$DIVIDER"
./build.sh

echo "$DIVIDER"
echo "Running prepare.sh..."
echo "$DIVIDER"
./prepare.sh "$NUM_HOSTS"

gcloud compute config-ssh
INSTANCE_NAMES=()
for ((i=0;i<NUM_HOSTS;i++)); do
    INSTANCE_NAMES+=("$(tofu output -json | jq -r ".host_name.value[$i]")")
done
INSTANCE_IPS=()
for ((i=0;i<NUM_HOSTS;i++)); do
    INSTANCE_IPS+=("$(tofu output -json | jq -r ".host_ip.value[$i]")")
done

echo "$DIVIDER"
echo "Running dependencies.sh..."
echo "$DIVIDER"
# check that the file is there on the host
echo "The following commands will be run on the hosts..."
for ((i=0;i<NUM_HOSTS;i++)); do
    ssh "${INSTANCE_NAMES[$i]}" "ls -la dependencies.sh" || echo "File dependencies.sh not found on host!"
    ssh "${INSTANCE_NAMES[$i]}" "./dependencies.sh"
done
echo "Done running dependencies.sh on hosts"

echo "$DIVIDER"
echo "Running celestial.bin..."
echo "$DIVIDER"
# move files
echo "Moving files..."
for ((i=0;i<NUM_HOSTS;i++)); do
    ssh "${INSTANCE_NAMES[$i]}" "sudo mv ./validator.img /celestial/validator.img"
done

echo "Running celestial..."
for ((i=0;i<NUM_HOSTS;i++)); do
    ssh "${INSTANCE_NAMES[$i]}" sudo ./celestial.bin --debug >> ${HOST_LOGS[$i]} 2>&1 &
done

echo -n "Waiting for celestial to start."
for _ in {1..10} ; do
    echo -n "."
    sleep 1
done

echo "$DIVIDER"
echo "Running celestial coordinator on host 0..."
echo "$DIVIDER"
command="PYTHONUNBUFFERED=1 python3 celestial.py satgen.zip "
for ((i=0;i<NUM_HOSTS;i++)); do
    command+="${INSTANCE_IPS[$i]}:1969 "
done
ssh "${INSTANCE_NAMES[0]}" $command >> $COORD_LOG 2>&1 &

# run for 10 minutes
echo "Running for 10 minutes... (Start time: $(date))"
sleep 600

echo "$DIVIDER"
echo "Killing celestial coordinator..."
echo "$DIVIDER"
# necessary to get SIGTERM to work
ssh "${INSTANCE_NAMES[0]}" "sudo killall python3"

# get the results
echo "$DIVIDER"
echo "Getting results..."
echo "$DIVIDER"
./getresults.sh "$NUM_HOSTS"

echo "$DIVIDER"
echo "Analyzing results..."
echo "$DIVIDER"
mkdir -p output
python3 analyze.py

echo "$DIVIDER"
echo "Done!"
echo "$DIVIDER"

# destroy the infrastructure
echo "Destroying infrastructure..."
echo "Run the following command to destroy the infrastructure:"
echo "tofu destroy -auto-approve --var 'hosts=$NUM_HOSTS'"
# tofu destroy -auto-approve
