#!/bin/bash

set -e

echo "::group:: ===$(basename "$0")==="

sudo podman pull ghcr.io/nisel11/alt-builder:latest
sudo podman run -d --privileged \
  --systemd=always \
  --cap-add=ALL \
  --name alt-builder \
  --tmpfs /run \
  --tmpfs /run/lock \
  -v "${GITHUB_WORKSPACE}:/workspace" \
  -v /sys/fs/cgroup:/sys/fs/cgroup:ro \
  ghcr.io/nisel11/alt-builder:latest

echo "::endgroup::"