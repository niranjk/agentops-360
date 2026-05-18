#!/bin/bash
# Vultr Production Instance Initialization Script - AgentOps-360

echo "🚀 Updating Vultr System Packages..."
sudo apt update && sudo apt upgrade -y

echo "📦 Installing Python3 and Pip dependencies..."
sudo apt install python3-pip python3-venv git -y

echo "⚡ Installing 'uv' package manager for instant builds..."
curl -LsSf https://astral.sh | sh
source $HOME/.local/bin/env

echo "🔄 Cloning project repository and launching app container..."
# (You will run 'uv run streamlit run app.py --server.port 80' once live)
echo "✅ System preparation complete. Ready for secure live hosting."
