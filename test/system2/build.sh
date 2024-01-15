#!/bin/bash

set -xe

ROOT="../.."

pushd "$ROOT" || exit

make build2 rootfsbuilder -B

popd || exit

pushd app || exit

make

popd || exit
