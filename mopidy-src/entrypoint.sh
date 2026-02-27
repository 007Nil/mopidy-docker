#!/bin/sh
set -e

echo "Waiting 2 seconds for volumes..."
sleep 2

echo "Running initial local scan..."
mopidy --config /config/mopidy.conf local scan || true

echo "Starting Mopidy server..."
exec mopidy --config /config/mopidy.conf

