#!/bin/bash

set -xe

RESULTS_RAW="out/"
RESULTS_CLEAN="results.csv"

TEST_HOST_NAME="$(terraform output -json | jq -r '.host_name.value')"

mkdir -p "$RESULTS_RAW"

gcloud compute config-ssh

# make a new results file
echo "Creating new results file..."
touch "$RESULTS_RAW"

# iterate through /celestial/out
OUT_FILES=$(ssh "$TEST_HOST_NAME" "ls -1 /celestial/out")

for f in $OUT_FILES; do
    echo "Processing file $f..."
    # if the file starts with err, then we skip it
    if [[ $f == err* ]]; then
        echo "Skipping file $f..."
        continue
    fi

    echo "Copying file $f..."
    scp "$TEST_HOST_NAME:/celestial/out/$f" "$RESULTS_RAW/$f.txt"
done

# clean up results
./cleanresults.py "$RESULTS_RAW" "$RESULTS_CLEAN"
