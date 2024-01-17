#!/bin/bash

set -xe

ROOT="../.."

pushd "$ROOT" || exit

make build rootfsbuilder -B

popd || exit

pushd app || exit

make

popd || exit
