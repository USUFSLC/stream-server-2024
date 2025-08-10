#!/bin/sh

# Runs after stream is finished recording
# https://github.com/arut/nginx-rtmp-module/wiki/Directives#exec_static

set -e

path="$1"
basename="$(basename $path)"
# just extract the uuid
uuid="${basename:0:36}"
# where we will be saving to
outdir="/var/stream/recordings/$uuid"

# make sure the output directory exists
mkdir -p "$outdir"

mv $path "$outdir/$uuid.flv"

# Output with same coding to the more common mp4 format
/usr/local/bin/ffmpeg -y -i "$outdir/$uuid.flv" "$outdir/$uuid.mp4"

curl -X POST http://fslc-stream:5000/api/rtmp/done \
	-H 'Content-Type: application/x-www-form-urlencoded' \
	-d "name=${basename%.*}"
