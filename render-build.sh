#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

# Create Storage Directory
STORAGE_DIR=/opt/render/project/.render
mkdir -p $STORAGE_DIR/chrome
cd $STORAGE_DIR/chrome

# 1. Install Chrome
echo "...Downloading Chrome"
if [[ ! -f ./opt/google/chrome/google-chrome ]]; then
  wget -q -O google-chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
  dpkg -x google-chrome.deb .
  rm google-chrome.deb
fi

# 2. Install Chromedriver (Matching Version)
echo "...Downloading Chromedriver"
# Chrome ka version check karein
CHROME_BIN=./opt/google/chrome/google-chrome
CHROME_VERSION=$($CHROME_BIN --version | awk '{print $3}')
echo "Detected Chrome Version: $CHROME_VERSION"

# Python script se latest Compatible Driver ka URL nikalein
DRIVER_URL=$(python -c "
import requests
try:
    # Google ki latest stable JSON API call
    url = 'https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json'
    data = requests.get(url).json()
    # Stable channel ka Linux64 driver uthayein
    for item in data['channels']['Stable']['downloads']['chromedriver']:
        if item['platform'] == 'linux64':
            print(item['url'])
            break
except:
    print('')
")

if [ -n "$DRIVER_URL" ]; then
    echo "Downloading Driver from: $DRIVER_URL"
    wget -q -O chromedriver.zip $DRIVER_URL
    unzip -q -o chromedriver.zip
    
    # Driver ko sahi jagah move karein
    if [ -d "chromedriver-linux64" ]; then
        mv chromedriver-linux64/chromedriver ./chromedriver
        rm -rf chromedriver-linux64
    fi
    
    chmod +x ./chromedriver
    rm chromedriver.zip
else
    echo "ERROR: Could not fetch Chromedriver URL"
fi

# Wapas project root par jayein
cd $HOME/project/src