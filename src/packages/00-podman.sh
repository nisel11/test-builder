#!/bin/bash

set -e

echo "::group:: ===$(basename "$0")==="

sudo apt-get update
sudo apt-get install -y podman

echo "::endgroup::"