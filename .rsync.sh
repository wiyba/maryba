#!/usr/bin/env bash
set -e
RPI=$(arp -n | awk '/enp0s20f0u2/{print $1; exit}')
[ -z "$RPI" ] && echo "малинки нет" && exit 1
exec rsync -avz --exclude '.git' --exclude '__pycache__' --exclude '*.db' --exclude 'static/recordings' ./ root@"$RPI":/root/Projects/maryba-new/
