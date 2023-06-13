import asyncio
import yt_dlp
import discord

def getvc(inter):
    if type(inter) is discord.Interaction:
        vc = inter.user.voice
    else:
        vc = inter.author.voice
    if vc is not None:
        vc = vc.channel
    else:
        vc = inter.channel.guild.voice_channels[0]
    return vc



async def get_video_url_by_title(title):
    ydl_opts = {
        'default_search': 'ytsearch',
        'quiet': True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        search_results = ydl.extract_info(title, download=False)
        if 'entries' in search_results:
            video_info = search_results['entries'][0]
            video_url = video_info['webpage_url']
            return video_url

    return None


async def playvideo(message, videoname):
    loop = asyncio.get_event_loop()
    loop.create_task(play_inner(message, await get_video_url_by_title(videoname)))

async def playurl(message, url):
    loop = asyncio.get_event_loop()
    loop.create_task(play_inner(message, url))


async def play_inner(message, url):
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