#!/bin/bash

set -e

echo "::group:: ===$(basename "$0")==="

sudo podman exec iso-builder su - builder -c "
  cd ~ && \
  git clone https://github.com/${GITHUB_REPOSITORY} --branch ${GITHUB_REF##*/} test-builder && \
  cd test-builder/src/source && \
  git clone https://github.com/altlinux/mkimage-profiles mkimage-profiles && \
  cp -rf mkimage/* mkimage-profiles && \
  cd mkimage-profiles
  make \
  IMAGEDIR=\"/workspace/out\" \
  BUILDLOG=\"/workspace/out/build.log\" \
  regular-gnome-atomic.iso"

echo "::endgroup::"
