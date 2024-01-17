#!/bin/bash

set -xe

echo "Running satgen script..."

ROOT="../.."

pushd "$ROOT" || exit

source .venv/bin/activate

python3 satgen.py test/system/config.toml test/system/satgen.zip

deactivate

popd || exit
