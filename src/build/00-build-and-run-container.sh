#!/bin/bash

set -e

echo "::group:: ===$(basename "$0")==="

sudo podman build -t iso-builder:latest "${GITHUB_WORKSPACE}/src/source/container"
sudo podman run -d --privileged \
  --systemd=always \
  --cap-add=ALL \
  --name iso-builder \
  --tmpfs /run \
  --tmpfs /run/lock \
  -v "${GITHUB_WORKSPACE}:/workspace" \
  -v /sys/fs/cgroup:/sys/fs/cgroup:ro \
  iso-builder:latest

echo "::endgroup::"
