<div align="center">

# Watchlist Bot

Watchlist Bot is a Discord bot designed to monitor specified channels for new invite links and URLs, providing detailed information about them.

</div>

## Features
- Monitors designated channels for invite links and URLs.
- Extracts and processes invite links to provide detailed server information.
- Extracts and processes URLs to provide detailed domain and IP information.

<div align="center">

## ☕ [Support my work on Ko-Fi](https://ko-fi.com/thatsinewave)

</div>

## Setup
To use the Watchlist Bot, follow these steps:

1. Clone this repository to your local machine.
2. Install the required dependencies listed in `requirements.txt`.
3. Create a `.env` file in the root directory of the repository.
4. Set the following environment variables in the `.env` file:
   - `TOKEN`: Your Discord bot token.
   - `MONITOR_CHANNEL_ID`: The Discord channel ID where invite links will be monitored.
   - `FORUM_CHANNEL_ID`: The Discord channel ID where server invite information will be posted.
   - `URL_CHANNEL_ID`: The Discord channel ID where URLs will be monitored.
   - `URL_FORUM_CHANNEL_ID`: The Discord channel ID where URL information will be posted.
5. Run the bot using `python main.py`.

## Dependencies
- Python 3.9
- Discord.py
- Requests
- Whois
- Dotenv

<div align="center">

## [Join my Discord server](https://discord.gg/2nHHHBWNDw)

</div>

## Usage
Once the bot is running and configured correctly, it will automatically monitor the specified channels for invite links and URLs. When a new invite link or URL is detected, it will fetch detailed information and post it in the designated forum channels.

## Contributing
Contributions are welcome! If you encounter any issues or have suggestions for improvements, feel free to open an issue or submit a pull request.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
