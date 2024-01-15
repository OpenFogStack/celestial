#!/bin/bash

set -xe

RESULTS_DIR="out"
RESULTS_CLEAN="results.csv"

TEST_HOST_NAME="$(terraform output -json | jq -r '.host_name.value')"

mkdir -p "$RESULTS_DIR"

# empty out the results directory
rm -rf "${RESULTS_DIR:?}"/*

gcloud compute config-ssh

# make a new results file
echo "Creating new results file..."
touch "$RESULTS_CLEAN"

# iterate through /celestial/out
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

# clean up results
./cleanresults.py "$RESULTS_DIR" "$RESULTS_CLEAN"
