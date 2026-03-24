#!/usr/bin/env nix-shell
#!nix-shell -i bash -p mediamtx ffmpeg
exec mediamtx .mediamtx.yml
