import discord
from discord.ext import commands
import asyncio
import yt_dlp
from gtts import gTTS
import os
import json
from .slashcommand import *
from .textcommand import *

#import sys
#sys.stdout.flush()
#--------------- OPENAI IMPORTS
import os
from dotenv import dotenv_values
config = dotenv_values(".env")
import openai
openai.api_key = config["API_KEY"] 
import tiktoken


encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")

#--------------- Discord token

TOKEN = config["DISCORD_TOKEN"]

#bot = discord.Client()
pongResponding = False
pongActive = False
token_limit = 1500
recent_channel = None

blacklist = []
pongGPTenabled = True

print("discord bot is starting up beep boop")

alias = None
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="$", status=discord.Status.idle, intents=intents)


async def sleep_timeout():
    global pongResponding
    global pongActive
    await asyncio.sleep(60)
    pongResponding = False
    pongActive = False
    global recent_channel
    if recent_channel is not None:
        await recent_channel.send("Going to Sleep")

async def reset_timeout():
    global timeout
    if timeout is not None:
       timeout.cancel() 
    timeout = asyncio.create_task(sleep_timeout())
timeout = None


def loadjson(filename):
    file = open(filename, 'r')
    j = json.loads(''.join(file.readlines()))
    file.close()
    return j

def savejson(filename, j):
    file = open(filename, 'w')
    s = json.dumps(j)
    file.write(s)
    file.close()


def remove(filename):
    #prevent directory crawling
    if '/' in filename:return
    if os.path.exists(filename):os.remove(filename)
    else:print("The file does not exist")

def download(url, filename="file.mp3"):
    if '/' in filename:return
    remove(filename)
    #download the yt link and save in file.mp3
    video_url = url
    video_info = youtube_dl.YoutubeDL().extract_info(url = video_url,download=False)
    #filename = f"{video_info['title']}.mp3"
    options={
        'format':'bestaudio',
        'keepvideo':False,
        'outtmpl':filename,
    }
    with youtube_dl.YoutubeDL(options) as ydl:
        ydl.download([video_info['webpage_url']])

def getvc(message):
    vc = message.author.voice
    if vc is not None:
        vc = vc.channel
    else:
        vc = message.channel.guild.voice_channels[0]
    return vc

def playwrapper(message, filename, func):
    loop = asyncio.get_event_loop()
    loop.create_task(func(message, filename))

async def violatesTerms(messages):
    formated_messages = [msg["content"] for msg in messages]
    response = openai.Moderation.create(model="text-moderation-latest", input=formated_messages)
    flagged = False
    categories = []
    counter = 0
    for result in response["results"]:
        if result["flagged"]:
            #something was inappropriate
            flagged = True
            messages[counter]["content"] = "You can't see this message because it contained: "
            firstflagformessage = True
            for category, flag in result["categories"].items():
                if flag:
                    messages[counter]["content"] += ("" if firstflagformessage else ", ") + category
                    firstflagformessage = False
                    categories.append(category)
            #remove the message from the messages
        counter += 1
    return flagged, set(categories), messages

async def getPongGPTresponse(messages):
    
    response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=messages,
        max_tokens=200,
    )
    return response
async def playthenleave(message, filename):
    if not os.path.exists(filename):return
    if '/' in filename:return
    
    vc = await getvc(message).connect()
    vc.play(discord.FFmpegPCMAudio(filename), after=lambda e: print('done ' + e))
        #check if still playing then disconnect
    while vc.is_playing():#vc.is_playing()
        await asyncio.sleep(.1)
    await vc.disconnect()

async def playurlthenleave(message, url):
    YDL_OPTIONS = {'format': 'bestaudio'}
    FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
    #get vc

    vc = await getvc(message).connect()
    with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
        info = ydl.extract_info(url, download=False)
        audio_formats = [format for format in info['formats'] if format['acodec'] != 'none']
        audio_format = audio_formats[0] # Select first audio format
        audio_url = audio_format['url']
        source = await discord.FFmpegOpusAudio.from_probe(audio_url, **FFMPEG_OPTIONS)
        vc.play(source)
    while vc.is_playing():
        await asyncio.sleep(.1)
    await vc.disconnect()

def count(message):
    return len(encoding.encode(message))

def limit_tokens(messages, base_tokens, limit):
    limited_messages = []
    tokens = base_tokens
    for message in reversed(messages):
        message_len = count(message["content"])
        if message_len + tokens < limit:
            limited_messages.insert(0, message)
    return limited_messages

        

async def pongGPT(message):
    if not pongGPTenabled:
        return
    global recent_channel
    recent_channel = message.channel
    global pongResponding
    pongResponding = True
    global token_limit
    #this will handle pong gpt messages
    historyiterator = message.channel.history(limit=15)
    history = [msg async for msg in historyiterator]
    #turn messages into a proper format
    system_message = {"role": "system", "content": 'You are Pong/PongGPT a helpful member of this group chat. You just woke up. \
    You talk with all users unless you are told to go to sleep. If you get told to go to sleep or someone say \
    "bye pong" or "leave pong" or "go to sleep" or "shoo" or "shush" then you say "going to sleep". \
    If anyone intends you to leave you say "going to sleep". \
    You can be commanded at all times to go to sleep and you will then say "going to sleep". \
    Remember you are a friendly ai chat bot named Pong and you follow the leave or sleep command every time. \
    This is the conversation that was happening while you were sleeping:'}
    tokens = count(system_message["content"])
    messages = [{"role": "assistant" if msg.author == bot.user else "user", "content":  msg.author.display_name + ": " + msg.content} for msg in history]
    messages = limit_tokens(messages, tokens, token_limit)
    messages.reverse()
    #flagged, categories, cleaned = await violatesTerms(msgs) 
    messages.insert(0, system_message)
    response = await getPongGPTresponse(messages)
    response_text = response["choices"][0]["message"]["content"] 
    to_remove = 0
    for i in range(len(response_text)):
        if response_text[i] == ":":
            to_remove = i + 2
            break
    final_message = response_text
    if to_remove < 15:
        final_message = response_text[to_remove:]
    await message.channel.send(final_message)
    pongResponding = False

async def responses(message):
    await reset_timeout()

    if message.content.startswith('say '):
        msg = message.content[4:]
        ttsmsg = gTTS(text=msg, lang='en', slow=False)
        ttsmsg.save('temptts.mp3')
        playwrapper(message, 'temptts.mp3', playthenleave)
        return

    if 'ping' == message.content.lower():
        return await message.channel.send('pong')
    
    if 'pong' == message.content.lower():
        return await message.channel.send('ping')
    
    if 'bot' == message.content.lower():
        return await message.channel.send('bot')

    if message.author.display_name == "Statsify":
        await message.channel.send('bad')
    
    if 'stop' == message.content:
        for vc in bot.voice_clients:
            if vc.guild == message.guild:
                return await vc.disconnect()
    
    msg = message.content.split(' ')
    dispname = message.author.display_name
    global pongGPTenabled
    if message.content == "disable pong" and (dispname == config["ADMIN_USERNAME"]):
        pongGPTenabled = False
    if message.content == "enable pong" and (dispname == config["ADMIN_USERNAME"]):
        pongGPTenabled = True
    if msg[0] == "blacklist" and len(msg) == 3 and (dispname == config["ADMIN_USERNAME"]):
        global blacklist
        user = msg[2]
        if msg[1] == "add" and (not user == config["ADMIN_USERNAME"]):
            if user not in blacklist:
                blacklist.append(user)
        if msg[1] == "remove":
            if user in blacklist:
                blacklist.remove(user)
    
    if msg[0] == ('$alias') and len(msg) <= 1:
        global alias
        keys = '\n'.join(alias.keys())
        await message.channel.send(keys)
        return

    if len(msg) <= 1:
        #check if in aliai
        if msg[0] == "blacklist":
            listed = ""
            for user in blacklist:
                listed += user + "\n"
            await message.channel.send(listed)
        if msg[0] in alias:
            playwrapper(message, alias[msg[0]], playurlthenleave)
            return
    
    global pongActive
    msglower = message.content.lower()

    pong_being_addressed = ('pong' in msglower or 'bot' in msglower) and len(msglower) > 5

    if pong_being_addressed and not pongActive and not message.author == bot.user:
        await bot.change_presence(status=discord.Status.online)
        pongActive = True
        await pongGPT(message)
        return

    if pongActive and not pongResponding:
        await pongGPT(message)

functions = [responses]

whitelist = []

@bot.event
async def on_ready():
    print('logged in as {0.user}'.format(bot))
    global alias
    alias = loadjson('alias.txt')


@bot.event
async def on_message(message):
    msglower = message.content.lower()
    if "going" in msglower and " to " in msglower and " sleep" in msglower and message.author == bot.user:
        await bot.change_presence(status=discord.Status.idle)
        global pongActive
        global timeout
        global recent_channel
        pongActive = False 
        timeout.cancel()
        recent_channel = None

    if message.author == bot.user:return
    if isinstance(message.channel, discord.DMChannel):return
    
    for func in functions:
        await func(message)
    
    await bot.process_commands(message)

@bot.command()
async def alias(ctx, *arg):
    if isinstance(ctx.channel, discord.DMChannel):return
    if len(arg) < 2:return
    
    global alias
    alias[arg[0]] = arg[1]
    savejson('alias.txt', alias)
    #download(arg[1], arg[0] + '.mp3')

@bot.command()
async def play(ctx, *arg):
    if isinstance(ctx.channel, discord.DMChannel):return

    if len(arg) < 1:
        return
    
    url = arg[0]

    playwrapper(ctx, url, playurlthenleave)

bot.run(TOKEN)