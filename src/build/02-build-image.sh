#!/bin/bash

set -e

echo "::group:: ===$(basename "$0")==="

# Параметр $1 – имя образа (например, live-rescue.iso)
sudo podman exec alt-builder su - builder -c "
  cd ~ && \
  git clone https://github.com/${GITHUB_REPOSITORY} --branch ${GITHUB_REF##*/} mkimage-profiles && \
  cd mkimage-profiles && \
  make \
  IMAGEDIR=\"/workspace/out\" \
  BUILDLOG=\"/workspace/out/build.log\" \
  ${1}"

echo "::endgroup::"