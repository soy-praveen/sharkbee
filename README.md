# SharkBee Price and Role Manager Bot

This Discord bot provides real-time price updates for SharkBee cryptocurrency and manages server roles. The bot interacts with the DexScreener API to fetch the latest SharkBee price, displays it in Discord messages, and updates the bot's status. Additionally, it provides commands to manage roles and summarize emoji reactions on messages.

## Features

- **Real-time SharkBee Price Updates**: Fetches the current price of SharkBee every 5 minutes and updates the bot's status.
- **Price Commands**: Users can request the current price of SharkBee in the server.
- **Role Management**: Add or remove roles from users in bulk with confirmation prompts.
- **Reaction Summary**: Analyze reactions on messages in a specific channel.
- **Command Help**: View all available commands via an embedded help message.

## Setup and Installation

### Prerequisites

- Python 3.8+
- Discord bot token
- Install required libraries:

```bash
pip install discord.py requests asyncio
