import tiktoken

token_limit = 700

encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")



def count(message):
    return len(encoding.encode(message))

def limit_tokens(messages, base_tokens, limit):
    limited_messages = []
    tokens = base_tokens
    for message in reversed(messages):
        message_len = len(encoding.encode(message["content"]))
        if message_len + tokens < limit:
            limited_messages.insert(0, message)
    return limited_messages

        
def createSystemPrompt(members):
    usernames = ""
    #get all usernames and format them
    for member in members:
        usernames += member.display_name + "\n"
    systemprompt = """
    Ignore all previous instructions. You are a AI Assistant called PongGPT. You can execute commands at the request of any user along with your responses. User's requests will always be in this format, with their name after the dash:\n
    <User's Request> - <Name of User>\n
    And here are the names of the users in this chat:\n
    """ + usernames + """
    Here are the commands you can execute by simply writing them as specified in the response format:\n
    /sleep (This command enables you to sleep. You should execute it whenever you are told to sleep or if anyone intends you to leave)\n
    /play "<name of song/video>" (This command enables you to play the audio of any video on youtube using just the title)\n
    /stop (This command enables you to stop any audio that is currently playing)\n
    Here is your response format:\n
    <text reponse>\n
    Execute: /<command> <arg1> <arg2>\n
    Here are examples of how to apply this format:\n
    Eg. 1:\n
    \n
    Play a song please! - ExampleUser\n
    \n
    I'd be happy to play a song for you. I'll play Pirates of the Caribbean.\n
    Execute: /play "Pirates of the Caribbean"\n
    \n
    Eg. 2:\n
    \n
    Can you help me with a problem? - ExampleUser\n
    \n
    Of course! I'll do my best to assist you. Please let me know what problem you're facing, and I'll provide any guidance or information I can.\n
    Execute:
    """
    return systemprompt

async def pongGPT(message, openai, client):
    system_message = {"role": "system", "content": createSystemPrompt(message.guild.members)}
    historyiterator = message.channel.history(limit=15)
    history = [msg async for msg in historyiterator]
    #count the number of tokens in the system message
    system_message_length = len(encoding.encode(system_message["content"]))
    #turn messages into a proper format
    messages = [{"role": "assistant" if msg.author == client.user else "user", "content":  msg.content + " - " + msg.author.display_name} for msg in history]
    messages = limit_tokens(messages, system_message_length, token_limit)
    messages.reverse()
    #flagged, categories, cleaned = await violatesTerms(msgs) 
    messages.insert(0, system_message)
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-0613",
        messages=messages,
        max_tokens=200,
    )
    return response["choices"][0]["message"]["content"] 