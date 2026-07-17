import os

from dotenv import load_dotenv, find_dotenv
import discord
from discord.ext import commands
import yt_dlp
from collections import deque
import asyncio

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

load_dotenv(find_dotenv())
TOKEN = os.getenv("TOKEN")

YDL_OPTS = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'default_search': 'ytsearch',
        }

FFMPEG_OPTS = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn'
        }

queues = {}
def get_queue(guild_id):
    if guild_id not in queues:
        queues[guild_id] = deque()
    return queues[guild_id]

def resolve_query(query):
    if re.match(r'^https?://', query):
        return query
    return f"ytsearch1:{query}"

def get_song_info(query):
    search_target = resolve_query(query)
    with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
        try:
            info = ydl.extract_info(search_target, download=False)
        except Exception as e:
            print(f"yt-dlp failed to get source: {e}")
            return
        
        if 'entries' in info:
            if not info['entries']:
                return
            info = info['entries'][0]

        return info['title'], info['url']


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}.")

@bot.command(name="join")
#NOTE: Will not abruptly rejoin upon recall but still rerun the script/or not (?)
async def join(ctx):
    if not ctx.author.voice:
        await ctx.send("You are not currently in any voice channel within this server")
        return 
    voice_channel = ctx.author.voice.channel
    if ctx.voice_client:
        await ctx.voice_client.move_to(voice_channel)
    else:
        await voice_channel.connect()

@bot.command(name="play")
async def play(ctx, *, query):
    await join(ctx)
    if not ctx.voice_client:
        return

    song_info = get_song_info(query)
    if query is None:
        await ctx.send(f"Cannot find the song.")
        return

    title, url = result
    source = discord.FFmpegPCMAudio(url, **FFMPEG_OPTS)
    voice_client.play(source)

    await ctx.send(f"""
                   Now playing: {title}
                   from: {url}
                   """)


@bot.command(name="queue")
async def queue(ctx, *, query):
    return

@bot.command(name="clear")
async def clear_queue(ctx):
    return
    


@bot.command(name="dc", aliases=["disconnect", "DC"])
async def disconnect(ctx):
    await ctx.voice_client.disconnect()

bot.run(TOKEN)

