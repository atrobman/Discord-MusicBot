import discord
import youtube_dl
from discord.ext import commands
import os
import asyncio
from async_timeout import timeout
import itertools
import random
import functools
import math
from cogs import utils

def setup(bot):
    bot.add_cog(Music(bot))

class VoiceError(Exception):
    pass

class YTDLError(Exception):
    pass

class YTDLSource(discord.PCMVolumeTransformer):
    YTDL_OPTIONS = {
        'format': 'bestaudio/best',
        'extractaudio': True,
        'audioformat': 'mp3',
        'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
        'restrictfilenames': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        'quiet': True,
        'no_warnings': True,
        'default_search': 'auto',
        'source_address': '0.0.0.0',
        }

    FFMPEG_OPTIONS = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn',
    }

    ytdl = youtube_dl.YoutubeDL(YTDL_OPTIONS)

    def __init__(self, ctx: commands.Context, source: discord.FFmpegPCMAudio, *, data: dict):
        super().__init__(source, 1)

        self.requester = ctx.author
        self.channel = ctx.channel
        self.data = data

        self.uploader = data.get('uploader')
        self.uploader_url = data.get('uploader_url')
        date = data.get('upload_date')
        self.upload_date = date[6:8] + '.' + date[4:6] + '.' + date[0:4]
        self.title = data.get('title')
        self.thumbnail = data.get('thumbnail')
        self.description = data.get('description')
        self.duration = self.parse_duration(int(data.get('duration')))
        self.tags = data.get('tags')
        self.url = data.get('webpage_url')
        self.views = data.get('view_count')
        self.likes = data.get('like_count')
        self.dislikes = data.get('dislike_count')
        self.stream_url = data.get('url')

    def __str__(self):
        return '**{0.title}** by **{0.uploader}**'.format(self)

    @classmethod
    async def create_source(cls, ctx: commands.Context, search: str, *, loop: asyncio.BaseEventLoop = None):
        loop = loop or asyncio.get_event_loop()

        partial = functools.partial(cls.ytdl.extract_info, search, download=False, process=False)
        data = await loop.run_in_executor(None, partial)

        if data is None:
            raise YTDLError('Couldn\'t find anything that matches `{}`'.format(search))

        if 'entries' not in data:
            process_info = data
        else:
            process_info = None
            for entry in data['entries']:
                if entry:
                    process_info = entry
                    break

            if process_info is None:
                raise YTDLError('Couldn\'t find anything that matches `{}`'.format(search))

        webpage_url = process_info['webpage_url']
        partial = functools.partial(cls.ytdl.extract_info, webpage_url, download=False)
        processed_info = await loop.run_in_executor(None, partial)

        if processed_info is None:
            raise YTDLError('Couldn\'t fetch `{}`'.format(webpage_url))

        if 'entries' not in processed_info:
            info = processed_info
        else:
            info = None
            while info is None:
                try:
                    info = processed_info['entries'].pop(0)
                except IndexError:
                    raise YTDLError('Couldn\'t retrieve any matches for `{}`'.format(webpage_url))

        return cls(ctx, discord.FFmpegPCMAudio(info['url'], **cls.FFMPEG_OPTIONS), data=info)

    @staticmethod
    def parse_duration(duration: int):
        minutes, seconds = divmod(duration, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)

        duration = []
        if days > 0:
            duration.append('{} days'.format(days))
        if hours > 0:
            duration.append('{} hours'.format(hours))
        if minutes > 0:
            duration.append('{} minutes'.format(minutes))
        if seconds > 0:
            duration.append('{} seconds'.format(seconds))

        return ', '.join(duration)

class Song:
    __slots__ = ('source', 'requester')

    def __init__(self, source: YTDLSource):
        self.source = source
        self.requester = source.requester

    def create_embed(self):
        embed = (discord.Embed(title='Now playing',
                               description='```css\n{0.source.title}\n```'.format(self),
                               color=discord.Color.blurple())
                 .add_field(name='Duration', value=self.source.duration)
                 .add_field(name='Requested by', value=self.requester.mention)
                 .add_field(name='Uploader', value='[{0.source.uploader}]({0.source.uploader_url})'.format(self))
                 .add_field(name='URL', value='[Click]({0.source.url})'.format(self))
                 .set_thumbnail(url=self.source.thumbnail))

        return embed

class SongQueue(asyncio.Queue):
    def __getitem__(self, item):
        if isinstance(item, slice):
            return list(itertools.islice(self._queue, item.start, item.stop, item.step))
        else:
            return self._queue[item]

    def __iter__(self):
        return self._queue.__iter__()

    def __len__(self):
        return self.qsize()

    def clear(self):
        self._queue.clear()

    def shuffle(self):
        random.shuffle(self._queue)

    def remove(self, index: int):
        del self._queue[index]

class MusicManager:
    def __init__(self, bot, ctx):
        self.ctx= ctx
        self.bot = bot
        self.queue = SongQueue()
        self.current_song = None
        self.next = asyncio.Event()
        self.voice_client = None
        self.exists = True
        self.player = self.bot.loop.create_task(self.music_player_task())

    def __del__(self):
        self.player.cancel()

    async def music_player_task(self):
        while True:
            self.next.clear()
            self.current_song = None

            try:
                async with timeout(180):
                    self.current_song = await self.queue.get()
            except asyncio.TimeoutError:
                self.bot.loop.create_task(self.stop())
                self.exists = False
                return

            self.voice_client.play(self.current_song.source, after=self.play_next_song)
            await self.ctx.send(embed=self.current_song.create_embed())
            
            await self.next.wait()

    async def stop(self):
        self.queue.clear()

        if self.voice_client is not None:
            await self.voice_client.disconnect()
            self.voice_client = None
            
    def play_next_song(self, error=None):
        if error:
            raise VoiceError(str(error))
        
        self.next.set()

    def skip(self):
        if self.is_playing:
            self.voice_client.stop()

    @property
    def is_playing(self):
        return self.voice_client and self.current_song

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.players = {}

    def get_voice_state(self, ctx):
        player = self.players.get(ctx.guild.id)
        if not player or not player.exists:
            player = MusicManager(self.bot, ctx)
            self.players[ctx.guild.id] = player

        return player

    def cog_unload(self):
        for player in self.players.values():
            self.bot.loop.create_task(player.stop())

    def cog_check(self, ctx):
        if not ctx.guild:
            raise Exception("Test: please change to be more descriptive")

        return True

    async def cog_before_invoke(self, ctx):
        ctx.voice_state = self.get_voice_state(ctx)
    

    @commands.command(pass_context=True, name="join", aliases=["summon, start"])
    async def join(self, ctx):
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send('You are not connected to any voice channel.')
            return

        if ctx.voice_client:
            if ctx.voice_client.channel != ctx.author.voice.channel:
                await ctx.send('Bot is already in a voice channel.')
                return

        dest = ctx.author.voice.channel
        if ctx.voice_state.voice_client:
            await ctx.voice_state.voice_client.move_to(dest)
            return
        
        ctx.voice_state.voice_client = await dest.connect()

    @commands.command(pass_context=True, name="leave", aliases=["quit", "exit"])
    async def leave(self, ctx):

        if not ctx.voice_state.voice_client:
            await ctx.send('Not connected to a voice channel')
            return

        await ctx.voice_state.stop()
        del self.players[ctx.guild.id]

    @commands.command(pass_context=True, name="now", aliases=["np", "current", "n"])
    async def now(self, ctx):

        if ctx.voice_state.current_song:
            await ctx.send(embed=ctx.voice_state.current_song.create_embed())
        else:
            await ctx.send(f"Nothing is playing right now")

    @commands.command(pass_context=True, name="pause")
    async def pause(self, ctx):

        if ctx.voice_state.is_playing:
            if ctx.voice_state.voice_client.is_playing():
                ctx.voice_state.voice_client.pause()
                await ctx.send("Player paused")
            else:
                await ctx.send("Player already paused")
        else:
            await ctx.send("Nothing is playing right now")
    
    @commands.command(pass_context=True, name="resume", aliases=["continue", "start"])
    async def resume(self, ctx):

        if ctx.voice_state.is_playing:
            if ctx.voice_state.voice_client.is_paused():
                ctx.voice_state.voice_client.resume()
                await ctx.send("Player resumed")
            else:
                await ctx.send("Player is not paused")
        else:
            await ctx.send("Nothing is playing right now")
            
    @commands.command(pass_context=True, name="stop")
    async def stop(self, ctx):

        ctx.voice_state.queue.clear()

        if ctx.voice_state.is_playing:
            ctx.voice_state.voice_client.stop()

    @commands.command(pass_context=True, name="skip", aliases=["s", "fs"])
    async def skip(self, ctx):

        if not ctx.voice_state.is_playing:
            await ctx.send("Not playing anything right now")
            return

        ctx.voice_state.skip()

    @commands.command(pass_context=True, name="queue", aliases=["q", "list", "songs", "playlist"])
    async def queue(self, ctx, page: int = 1):

        if len(ctx.voice_state.queue) == 0:
            return await ctx.send("Queue is empty")

        items_per_page = 10
        pages = math.ceil(len(ctx.voice_state.queue) / items_per_page)

        start = (page - 1) * items_per_page
        end = start + items_per_page

        queue = ''
        for i, song in enumerate(ctx.voice_state.queue[start:end], start=start):
            queue += f'`{i + 1}.` [**{song.source.title}**]({song.source.url})\n'

        embed = (discord.Embed(description=f'**{len(ctx.voice_state.queue)} tracks:**\n\n{queue}')
                    .set_footer(text=f'Viewing page {page}/{pages}'))
        await ctx.send(embed=embed)

    @commands.command(pass_context=True, name="shuffle")
    async def shuffle(self, ctx):

        if len(ctx.voice_state.queue) == 0:
            return await ctx.send("Queue is empty")

        ctx.voice_state.queue.shuffle()

    @commands.command(pass_context=True, name="remove", aliases=["r", "d", "delete", "del", "rm", "rem"])
    async def remove(self, ctx, index: int):

        if len(ctx.voice_state.queue) == 0:
            return await ctx.send("Queue is empty")

        ctx.voice_state.queue.remove(index - 1)

    @commands.command(pass_context=True, name="play", aliases=["p", "pl"])
    async def play(self, ctx, *, search: str):
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send('You are not connected to any voice channel.')
            return

        if ctx.voice_client:
            if ctx.voice_client.channel != ctx.author.voice.channel:
                await ctx.send('Bot is already in a voice channel.')
                return

        if not ctx.voice_state.voice_client:
            await ctx.invoke(self.join)

        async with ctx.typing():
            try:
                source = await YTDLSource.create_source(ctx, search, loop=self.bot.loop)
            except YTDLError as e:
                await ctx.send('An error occurred while processing this request: {}'.format(str(e)))
            else:
                song = Song(source)
                await ctx.voice_state.queue.put(song)
                await ctx.send(f"**{source.title}** added to queue")