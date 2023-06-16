# Discord Bot with ChatGPT Integration

This Discord bot incorporates ChatGPT for chatting and the execution of commands through natural language instructions. It also has standard Discord slash commands. Although the previous experience was somewhat akin to negotiating with a sentient bomb to deactivate itself. With open AI's release of gpt-3.5-turbo-0613 the adherance to the system prompt seems to have resolved the issue of it orienting its behavior on past responses rather than the system prompt. The bot is still deeply biased toward Ed Sheeran when asked to play any song.

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

- /sleep: Executes the sleep command, which allows the bot to go back to sleep.

- /play "<name of song/video>": Executes the play command, which allows the bot to play the audio of a specific YouTube video based on its title in the voice chat.

- /stop: Executes the stop command, which stops any audio that is currently playing.

Note: These commands are added to the bot by simply including them in the system prompt with a short natural language description for when they should be run and what they do. They then still have to be executed by parsing them out of the response text. While this approach is a lot simpler than OpenAI's newly released ChatGPT function calling ability, it is still less reliable and not as clean looking since every reponse includes the "Execute: /<command>" to minimize the potential for confusion in future responses.

The bot should respond in the following format:

```
<text response>
Execute: /<command> <arg1> <arg2>
```

Here is an example of a simple interaction:

User:
  
  ```
  Play a song please!
  ```

PongGPT:
  
  ```
  I'd be happy to play a song for you. I'll play Shape of you by Ed Sheeran.
  Execute: /play "Shape of you by Ed Sheeran"
  ```
  
## Limitations
The successful execution of commands depends on correct response formatting for command extraction. However, the bot's reliability is affected by occasional refusal to run commands due to being an "AI Language model" or incorrect command formatting. While there is some patch code in place to handle malformed responses to prevent some command formatting failures, relying on these solutions is not an effective or definitive approach. See [Improvements](#improvements) for potential [improvements](#improvements).

Previously, failures to format the command correctly made subsequent commands even more unreliable. The examples of its previous incorrect formatting were the only thing it oriented its new responses on. The bot now seems to have the ability to correct its behavior and recover from incorrect formatting, which is largely attributable to gpt-3.5-turbo-0613's increased ability to obey the system prompt.

## Improvements
Replacing my text parsing with the official function/API calling feature which is now available with gpt-3.5-turbo-0613 would eliminate the need for text parsing and would streamline the addition of new commands.
