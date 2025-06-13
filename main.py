import discord
from discord.ext import commands
import youtube_dl

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

ytdl_format_options = {
    'format': 'bestaudio/best',
    'quiet': True,
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if 'entries' in data:
            data = data['entries'][0]
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

@bot.event
async def on_ready():
    print(f'Bot connected as {bot.user}')

@bot.command()
async def join(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        await channel.connect()
    else:
        await ctx.send("You are not in a voice channel!")

@bot.command()
async def play(ctx, url):
    async with ctx.typing():
        player = await YTDLSource.from_url(url, loop=bot.loop, stream=True)
        ctx.voice_client.play(player, after=lambda e: print(f'Player error: {e}') if e else None)
    await ctx.send(f'Now playing: {player.title}')

@bot.command()
async def pause(ctx):
    ctx.voice_client.pause()
    await ctx.send("Playback paused.")

@bot.command()
async def resume(ctx):
    ctx.voice_client.resume()
    await ctx.send("Playback resumed.")

@bot.command()
async def skip(ctx):
    ctx.voice_client.stop()
    await ctx.send("Playback skipped.")

@bot.command()
async def leave(ctx):
    await ctx.voice_client.disconnect()
    await ctx.send("Disconnected from the voice channel.")

bot.run('YOUR_DISCORD_BOT_TOKEN')