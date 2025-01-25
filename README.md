# Ronin Pools Telegram Bot

A Telegram bot that provides real-time data from GeckoTerminal's Ronin pools.

## Features

- Get list of top Ronin pools
- View specific pool details (liquidity, volume, price)
- Price alerts for specific pools
- Search functionality for pools
- Basic analytics and price change notifications

## Setup

1. Create and activate virtual environment:
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
.\venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your Telegram Bot Token
```

4. Run the bot:
```bash
python run.py
```

5. Deactivate virtual environment when done:
```bash
deactivate
```

## Project Structure

```
.
├── src/
│   ├── __init__.py         # Makes src a Python package
│   ├── main.py             # Bot entry point
│   ├── bot/                # Bot-related modules
│   │   ├── commands.py     # Bot command handlers
│   │   └── utils.py        # Bot utility functions
│   ├── gecko/              # GeckoTerminal integration
│   │   ├── api.py         # API client
│   │   └── models.py      # Data models
│   └── db/                 # Database operations
│       └── storage.py      # SQLite operations
├── run.py                  # Script to run the bot
├── requirements.txt        # Python dependencies
├── .env.example           # Example environment variables
└── README.md              # This file
```

## Commands

- `/start` - Start the bot and get help
- `/trending` - Get top 10 trending pools on Ronin
- `/pools` - Get list of top Ronin pools
- `/pool <symbol>` - Get specific pool details
- `/alert <symbol> <price>` - Set price alert
- `/alerts` - List your active alerts
- `/search <query>` - Search for pools

## Contributing

Feel free to open issues and pull requests for any improvements.

## License

MIT License 