# Discord Bot with ChatGPT Integration

This Discord bot incorporates ChatGPT for chatting and the execution of commands through natural language instructions. It also has standard Discord slash commands. Although the previous experience was somewhat akin to negotiating with a sentient bomb to deactivate itself. With open AI's release of gpt-3.5-turbo-0613 the function calling feature has resolved the reliability issues. The bot might nonetheless still be deeply biased toward Ed Sheeran when asked to play any song.

## Installation

To set up the Discord bot, follow these steps:

1. Clone the repository to your local machine.
2. If you don't want to run it in docker just install the required dependencies in a virtual environment using `pip install -r r.txt`.
3. Put the necessary API key, token, and so on (API_KEY = openai api key, TOKEN = discord bot token, GUILD_ID = discord server/guild id) into a `.env` file in the root directory.
4. Run `docker compose up --build` or run the main.py script to start the bot.

## Usage

First the bot has to be awoken by addressing it:
  "Hey pong" or "Pong can you play a song please?" or any message which includes `" pong"` or `"pong "` will awaken it.

Then pong will respond to every message in any channel until it is told to go back to sleep.

Here are the commands that the bot can execute with natural language instructions:

- sleep: Executes the sleep command, which allows the bot to go back to sleep.

- play "<name of song/video>": Executes the play command, which allows the bot to play the audio of a specific YouTube video based on its title in the voice chat.

- stop: Executes the stop command, which stops any audio that is currently playing.

Note: Since the utilization of the function calling feature there have been no more reliability issues in regards to the AI
  
## Limitations
The bot is now mainly limited by the reliability of the Discord API and openai API. If either of these are overloaded the bot might respond with the occasional prolonged silence. See [Improvements](#improvements) for potential [improvements](#improvements).


## Improvements
The bot is currently awaken and put back to sleep globaly. This has led to a number of interesting occasions where pong seemed to activate himself, so a substantial improvement would be to handle this on server by server basis.
