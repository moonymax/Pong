"""
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

"""

import discord
from discord import app_commands
from discord.ext import commands
import asyncio

from dotenv import dotenv_values
import typing
from mem import loadjson, savejson
from gpt import pongGPT
config = dotenv_values(".env")
import openai
openai.api_key = config["API_KEY"] 

GUILD_ID = config["GUILD_ID"]
TOKEN = config["TOKEN"]
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

guild =discord.Object(id=GUILD_ID) 


#GLOBALS
alias = {}

#@commands.has_permissions(administrator=True)
group = app_commands.Group(name="alias", description="define shortcuts for playing a youtube link in the voice chat")

tree.add_command(group, guild=guild)
@group.command(description="List all bindings")
async def list(interaction):
    bigstring = ""
    for key in alias:
        bigstring += key + ": " + alias[key] + "\n"
    await interaction.response.send_message(bigstring, ephemeral=True, delete_after=60.0)

@group.command(description = "Bind a string to a youtube link") 
#@app_commands.choices(action=[app_commands.Choice(name="set", value="set"), app_commands.Choice(name="remove", value="remove")])
async def add(inter, name: str, link: str):
    global alias
    alias[name] = link
    savejson('alias.txt', alias)
    await inter.response.send_message("added")

@group.command(description="Unbind a string from a youtube link")
async def remove(inter, name: str):
    global alias
    del alias[name]
    savejson('alias.txt', alias)
    await inter.response.send_message("removed")

from yt import playvideo, playurl

@tree.command(name="play", description="Play a youtube video in voice chat", guild=guild)
async def play(inter, videoname: str):
    if isinstance(inter.channel, discord.DMChannel):return
    await inter.response.send_message("playing: " + videoname, ephemeral=True, delete_after=20.0)
    await playvideo(inter, videoname)

@tree.command(name="sleep", description="Put PongGPT to sleep at any time with this command", guild=guild)
async def sleep(inter):
    isPongAwake = False
    await client.change_presence(status=discord.Status.idle)
    await inter.response.send_message("PongGPT is going to sleep", ephemeral=True, delete_after=20.0)

@tree.command(name="stop", description="Stop any audio pong is currently playing in vc and disconnect", guild=guild)
async def stop(inter):
    await inter.response.send_message("stopping audio", ephemeral=True, delete_after=20.0)
    for vc in client.voice_clients:
            if vc.guild == inter.guild:
                return await vc.disconnect()

@client.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=GUILD_ID))
    await client.change_presence(status=discord.Status.idle)
    global alias
    alias = loadjson('alias.txt')
    print("Ready!")

async def sleep_timeout():
    global respondingATM
    global isPongAwake
    await asyncio.sleep(60)
    await client.change_presence(status=discord.Status.idle)
    respondingATM = False
    isPongAwake = False

async def reset_timeout():
    global timeout
    if timeout is not None:
       timeout.cancel() 
    timeout = asyncio.create_task(sleep_timeout())

timeout = None

isPongAwake = False
respondingATM = False

def findbetweenquotes(string):
    start_index = string.find('"')
    end_index = string.find('"', start_index + 1)

    if start_index != -1 and end_index != -1:
        extracted_string = string[start_index + 1:end_index]
        return extracted_string
    else:
        return None

@client.event
async def on_message(message):
    msglower = message.content.lower()
    """
    if "going" in msglower and " to " in msglower and " sleep" in msglower and message.author == client.user:
        await client.change_presence(status=discord.Status.idle)
        global pongActive
        global timeout
        global recent_channel
        pongActive = False 
        timeout.cancel()
        recent_channel = None
    """

    if message.author == client.user:return
    if isinstance(message.channel, discord.DMChannel):return

    if 'ping' == message.content.lower():
        return await message.channel.send('pong')
    
    if 'pong' == message.content.lower():
        return await message.channel.send('ping')

    msg = message.content.split(' ')
    if len(msg) <= 1:
        if msg[0].lower() in alias:
            await playurl(message, alias[msg[0].lower()])
            return
    
    
    global isPongAwake
    global respondingATM
    #if pong is being addressed then flip isPongAwake
    if " pong" in msglower or "pong " in msglower:
        isPongAwake = True
    if isPongAwake and not respondingATM:
        respondingATM = True
        await reset_timeout()
        await client.change_presence(status=discord.Status.online)
        response = await pongGPT(message, openai, client)
        lines = response.split("\n")
        cleanresponse = ""
        print(response)
        def startswithany(originalstring, strings):#
            for substr in strings:
                if originalstring.startswith(substr):
                    return True
        def stringafter(originalstring, afterthis):
            index = originalstring.find(afterthis)
            return originalstring[index + len(afterthis):]

        for i in range(len(lines)):
            if "Execute: /" in lines[i] or startswithany(lines[i], ["/sleep", "/play", "/stop"]):
                #handle the line
                if "Execute: /" in lines[i]:
                    fullcommand = stringafter(lines[i], "Execute: /")
                else:
                    fullcommand = lines[i][len("/"):]
                print(fullcommand)
                #match the command with an existing command
                command = fullcommand.split(" ")[0]
                if command == "sleep":
                    #sleep
                    isPongAwake = False
                    await client.change_presence(status=discord.Status.idle)
                elif command == "play":
                    #play a video
                    videotitle = findbetweenquotes(fullcommand)
                    await playvideo(message, videotitle)
                elif command == "stop":
                    #stop all audio
                    for vc in client.voice_clients:
                        if vc.guild == message.channel.guild:
                            await vc.disconnect()
            else:
                cleanresponse += lines[i] + "\n"
        await message.channel.send(response.replace(" - PongGPT", ""))
        respondingATM = False


client.run(TOKEN)