#!/usr/bin/env bash
set -e
RPI=$(arp -n | awk '/enp0s20f0u2/{print $1; exit}')
[ -z "$RPI" ] && echo "малинки нет" && exit 1
TERM=xterm-256color exec ssh root@"$RPI" "$@"
