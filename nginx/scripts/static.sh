#!/bin/sh

# Runs at nginx startup via exec_static hook
# https://github.com/arut/nginx-rtmp-module/wiki/Directives#exec_static

# Ensure that hls and recordings directories exist
mkdir -p /var/stream/hls /var/stream/recordings

# And because this script is supposed to run forever...
while true; do sleep 86400; done
