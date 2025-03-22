#!/bin/bash

set -e

echo "::group:: ===$(basename "$0")==="

sudo podman exec iso-builder chown -R builder:builder /workspace
sudo podman exec iso-builder chmod -R u+w /workspace

echo "::endgroup::"
