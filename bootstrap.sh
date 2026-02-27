#!/bin/bash
set -e

echo "Creating data directories..."
mkdir -p data cache

echo "Fixing permissions..."
sudo chown -R 1000:29 data cache config || true
sudo chmod -R 775 data cache config || true

echo "Building Mopidy..."
docker compose build --no-cache

echo "Starting Mopidy..."
docker compose up -d

echo "Done."
echo "Access Mopidy at: http://$(hostname -I | awk '{print $1}'):6680"
