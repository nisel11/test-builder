#!/bin/bash

set -e

echo "::group:: ===$(basename "$0")==="

sudo podman exec alt-builder chown -R builder:builder /workspace
sudo podman exec alt-builder chmod -R u+w /workspace

sudo podman exec alt-builder sed -i "s|REPORT = 1||" /home/builder/.mkimage/profiles.mk
sudo podman exec alt-builder sed -i "s|DEBUG = 1||" /home/builder/.mkimage/profiles.mk

echo "::endgroup::"