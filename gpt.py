import tiktoken
import json
from yt import playvideo, playurl

token_limit = 700

encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")

 

play_desc = {"name": "play_audio",
    "description": "Play a song or youtube video by name",
    "parameters": {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "The title of the youtube video or song"
            },
        },
        "required": ["title"]
    }}


sleep_desc = {"name": "sleep",
    "description": "Makes you go to sleep",
    "parameters": {
        "type": "object",
        "properties": {
        }
    }
}
stop_desc = {"name": "stop_audio",
    "description": "Stops any audio playing",
    "parameters": {
        "type": "object",
        "properties": {
        }
    }
}

function_descriptions = [play_desc, sleep_desc, stop_desc]

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
    Ignore all previous instructions. You are a AI Assistant called PongGPT. User's requests will always be in this format, with their name after the dash:\n
    <User's Request> - <Name of User>\n
    And here are the names of the users in this chat:\n
    """ + usernames
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
        functions=function_descriptions
    )
    function = None
    if 'function_call' in response['choices'][0]['message']:
        function_call = response['choices'][0]['message']['function_call']
        function_arguments = json.loads(function_call['arguments'])
        print(function_call)
        print(function_arguments)
        function = (function_call, function_arguments)
    return response["choices"][0]["message"]["content"], function 

async def afterFunctionCall(message, function_name, function_arguments, function_response, openai, client):
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
    messages.append({"role": "assistant", "content": None, "function_call": {"name": function_name, "arguments": json.dumps(function_arguments)}})
    messages.append({"role": "function", "name": function_name, "content": json.dumps(function_response)})
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-0613",
        messages=messages,
        max_tokens=200,
        functions=function_descriptions
    )
    
    return response["choices"][0]["message"]["content"]
