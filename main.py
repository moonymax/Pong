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
from gpt import pongGPT, afterFunctionCall
config = dotenv_values(".env")
import openai
openai.api_key = config["API_KEY"] 

GUILD_IDs = config["GUILD_ID"]
TOKEN = config["TOKEN"]
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

guilds =[]
for guildid in GUILD_IDs.split(","):
    guilds.append(discord.Object(id=guildid))


#GLOBALS
alias = {}

#@commands.has_permissions(administrator=True)
group = app_commands.Group(name="alias", description="define shortcuts for playing a youtube link in the voice chat")

tree.add_command(group, guilds=guilds)
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

@tree.command(name="play", description="Play a youtube video in voice chat", guilds=guilds)
async def play(inter, videoname: str):
    if isinstance(inter.channel, discord.DMChannel):return
    await inter.response.send_message("playing: " + videoname, ephemeral=True, delete_after=20.0)
    await playvideo(inter, videoname)

@tree.command(name="sleep", description="Put PongGPT to sleep at any time with this command", guilds=guilds)
async def sleep(inter):
    isPongAwake = False
    await client.change_presence(status=discord.Status.idle)
    await inter.response.send_message("PongGPT is going to sleep", ephemeral=True, delete_after=20.0)

@tree.command(name="stop", description="Stop any audio pong is currently playing in vc and disconnect", guilds=guilds)
async def stop(inter):
    await inter.response.send_message("stopping audio", ephemeral=True, delete_after=20.0)
    for vc in client.voice_clients:
            if vc.guild == inter.guild:
                return await vc.disconnect()

@client.event
async def on_ready():
    for guild in guilds:
        await tree.sync(guild=guild)
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
        response, function = await pongGPT(message, openai, client)
        if function is not None:
            function_call, function_arguments = function
            function_response = {}
            if function_call['name'] == "play_audio":
                await playvideo(message, function_arguments['title'])
                function_response = {
                    "success": True,
                    "playing": function_arguments['title']
                }
            elif function_call['name'] == "stop_audio":
                for vc in client.voice_clients:
                        if vc.guild == message.channel.guild:
                            await vc.disconnect()
                function_response = {
                    "success": True
                }
            elif function_call['name'] == "sleep":
                isPongAwake = False
                await client.change_presence(status=discord.Status.idle)
                function_response = {"success": True}
            response = await afterFunctionCall(message, function_call['name'], function_arguments, function_response, openai, client)
        await message.channel.send(response.replace(" - PongGPT", ""))
        respondingATM = False


client.run(TOKEN)