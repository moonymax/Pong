# Discord Bot with ChatGPT Integration

This Discord bot incorporates ChatGPT for chatting and the execution of commands through natural language instructions. It also has standard Discord slash commands. The bot aims to provide silly chat interactions since it is rather unreliable at executing commands. In fact every thing the bot can do with natural language instuctions, the user can do much more reliably with slash commands. The experience is somewhat akin to negotiating with a sentient bomb to deactivate itself. Only in this case you asked it to play a song, any song in fact. It choose "Shape of you" by Ed Sheeran once again and now, when asked to "please stop" the bot insits that as an "AI Language model" it does not have the ability to execute commands.

## Installation

To set up the Discord bot, follow these steps:

1. Clone the repository to your local machine.
2. If you don't want to run it in docker just install the required dependencies in a virtual environment using `pip install -r r.txt`.
3. Put the necessary API key, token, and so on (API_KEY = openai api key, TOKEN = discord bot token, GUILD_ID = discord server/guild id) into a `.env` file in the root directory.
4. Run `docker compose up --build` or run the main.py script to start the bot.

## Usage

First the bot has to be awoken by addressing it:
  "Hey pong" or "Pong can you play a song please?" or any message which includes `" pong"` or `"pong "` will awaken it.

Then pong with respond to every message until it is told to go back to sleep.

Here are the commands that the bot can execute with natural language instructions:

- /sleep: Executes the sleep command, which allows the bot to go back to sleep.

- /play "<name of song/video>": Executes the play command, which allows the bot to play the audio of a specific YouTube video based on its title in the voice chat.

- /stop: Executes the stop command, which stops any audio that is currently playing.

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
 
  The successful execution of commands depends on correct response formatting for command extraction. However, the bot's reliability is affected by occasional refusal to run commands due to being an "AI Language model" or incorrect command formatting. While there is some patch code in place to handle malformed responses to prevent some command formatting failures, relying on this solutions is not an effective or definitive approach. See [Improvements](#improvements) for Potential [Improvements](#improvements).

  It's important to note that once the bot fails to format the command correctly, subsequent requests become even more unreliable. The model tends to rely on its past behavior, orienting itself on prior responses rather than the system prompt.
  
## Improvements
  To enhance reliability, one possible approach could be splitting the process into separate requests. First, an initial request to respond to the user's input. Then, a request to determine whether the bot should execute a command. Maybe even a third request which focuses on extracting the formatted command. By implementing such an approach, the impact of the bot's previous responses could be minimized, potentially improving reliability. It's important to consider that this approach may introduce added complexity and may potentially result in significantly higher API costs, depending on the chosen model and implementation of this approach.
  
