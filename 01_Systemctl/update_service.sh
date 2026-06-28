#!/bin/bash

SERVICE_NAME=telegram-homer  # Adjust service name as needed"
REPO_SERVICE_FILE="01_Systemctl/telegram-homer.service"  # Adjust path as needed
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

REPO_DIR="/home/projects/Homer-The-Orator"
cd "$REPO_DIR" || exit 1

# Check if the repo file exists
if [ ! -f "${REPO_SERVICE_FILE}" ]; then
    echo "Error: ${REPO_SERVICE_FILE} not found!"
    exit 1
fi

# Stop the service
sudo systemctl stop "${SERVICE_NAME}" 2>/dev/null

# Copy the service file from repo to systemd
sudo cp "${REPO_SERVICE_FILE}" "${SERVICE_FILE}"

# Reload systemd
sudo systemctl daemon-reload

# Enable and restart
sudo systemctl enable "${SERVICE_NAME}"
sudo systemctl restart "${SERVICE_NAME}"

# Show status
sudo systemctl status "${SERVICE_NAME}" --no-pager


# Get the journals for the bot
# sudo journalctl -u telegram-homer -f