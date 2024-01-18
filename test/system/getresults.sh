#!/bin/bash

set -xe

if [ $# -ne 1 ]; then
    echo "Usage: $0 <num_hosts>"
    exit 1
fi

NUM_HOSTS="$1"

RESULTS_DIR="out"
RESULTS_CLEAN="results.csv"

TEST_HOST_NAMES=()
for ((i=0;i<NUM_HOSTS;i++)); do
    TEST_HOST_NAMES+=("$(tofu output -json | jq -r ".host_name.value[$i]")")
done

mkdir -p "$RESULTS_DIR"

# empty out the results directory
rm -rf "${RESULTS_DIR:?}"/*

gcloud compute config-ssh

# make a new results file
echo "Creating new results file..."
touch "$RESULTS_CLEAN"

# iterate through /celestial/out

for ((i=0;i<NUM_HOSTS;i++)); do
    TEST_HOST_NAME="${TEST_HOST_NAMES[$i]}"
    echo "Processing host $TEST_HOST_NAME..."
    # get the files in /celestial/out
    OUT_FILES=$(ssh "$TEST_HOST_NAME" "ls -1 /celestial/out")

    for f in $OUT_FILES; do
        echo "Processing file $f..."
        # if the file ends with .err, then we skip it
        if [[ $f == *.err ]]; then
            echo "Skipping file $f..."
            continue
        fi

        echo "Copying file $f..."
        scp "$TEST_HOST_NAME:/celestial/out/$f" "$RESULTS_DIR/$f"
    done
done

# clean up results
./cleanresults.py "$RESULTS_DIR" "$RESULTS_CLEAN"
