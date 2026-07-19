import os

from dotenv import load_dotenv, find_dotenv
import discord
from discord.ext import commands
import yt_dlp
from collections import deque
import asyncio
import re

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
    
    q = get_queue(ctx.guild.id)
    result = get_song_info(query)
    if result is None:
        await ctx.send(f"Cannot find the song.")
        return
    title, url = result
    q.appendleft(result)
    
    if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
        ctx.voice_client.stop()

    await play_next(ctx)

async def play_next(ctx):
    q = get_queue(ctx.guild.id)
    #If queue is empty, do nothing
    if not q:
        ctx.send(f"""
                 No more song to play.
                 """)
        return
    
    title, url = q[0]
    source = discord.FFmpegPCMAudio(url, **FFMPEG_OPTS)

    def after_playing(error):
        if error:
            ctx.send(f"Error: {error}")
        if q and q[0] == (title, url):
            q.popleft()
        asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop)

    ctx.voice_client.play(source, after=after_playing)
    await ctx.send(f"""
                   Now playing: {title}
                   """)





@bot.command(name="queue")
async def queue(ctx, *, query):
    q = get_queue(ctx.guild.id)
    try:
        #Can be shorter
        song = get_song_info(query)
        title, url = song
        q.append((title, url))

        await ctx.send(f"""
                       Queued: {title}
                       """)
    except Exception as e:
        ctx.send(f"Error: {e}")

@bot.command(name="clear", aliases=["clear_queue", "cq"])
async def clear_queue(ctx):
    if queues[ctx.guild.id]:
        queues[ctx.guild.id].clear()

@bot.command(name="skip")    
async def skip(ctx):
    q = get_queue(ctx.guild.id)
    ctx.voice_client.stop()
    if not q:
        q.popleft()
    await play_next(ctx)



@bot.command(name="dc", aliases=["disconnect", "DC"])
async def disconnect(ctx):
    await ctx.voice_client.disconnect()

bot.run(TOKEN)

