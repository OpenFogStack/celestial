#!/bin/bash

set -xe

echo "Running satgen script..."

ROOT="../.."

pushd "$ROOT" || exit

source .venv/bin/activate

python3 satgen.py test/system2/config.toml test/system2/satgen.zip

deactivate

popd || exit
