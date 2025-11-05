#!/bin/bash
# This script is used to update the TwitchDropsBot container
# It is used to update the bot to the latest version
cd /root/twitch

echo "Stopping TwitchDropsBot"
docker compose down

echo "Updating TwitchDropsBot"
if [ -d "./TwitchDropsBot" ]; then
    cd ./TwitchDropsBot
    git pull
    cd ..
else
    echo "TwitchDropsBot directory not found, cloning repository..."
    git clone https://github.com/Alorf/TwitchDropsBot.git TwitchDropsBot
fi


echo "Setting permissions for config.json and logs"
if [ -f "./config.json" ]; then
    chmod 666 ./config.json
    echo "config.json permissions updated"
fi

if [ ! -d "./logs" ]; then
    mkdir -p ./logs
fi
chmod -R 777 ./logs
echo "logs directory permissions updated"

echo "Building TwitchDropsBot"
docker compose build

echo "Starting TwitchDropsBot"
docker compose up -d

echo "Update complete"
