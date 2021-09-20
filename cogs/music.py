import discord
import youtube_dl
from discord.ext import commands
import os
import asyncio

def setup(bot):
    bot.add_cog(Music(bot))

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,
        } 

        self.voice_client = None
        self.queue = []

    async def __join(self, ctx):
        if not ctx.author.voice:
            await ctx.send("You are not connected to a voice channel")
            return False

        if self.voice_client is not None:
            await self.voice_client.disconnect()

        self.voice_client = await ctx.author.voice.channel.connect()
        return True

    @commands.command(pass_context=True)
    async def join(self, ctx):
        await self.__join(ctx)

    @commands.command(pass_context=True)
    async def leave(self, ctx):
        if not ctx.author.voice:
            await ctx.send("You are not connected to a voice channel")
            return

        if self.voice_client is None:
            await ctx.send("Not currently connected to a voice channel")
            return

        await self.voice_client.disconnect()
        self.voice_client = None

        await ctx.send("Disconnected")

    @commands.command(pass_context=True)
    async def play(self, ctx, msg):
        if not await self.__join(ctx):
            return

        with youtube_dl.YoutubeDL(self.ydl_opts) as ydl:
            file = ydl.extract_info(msg, download=True)
            path = str(file['title']) + "-" + str(file['id'] + ".mp3")

        self.voice_client.play(discord.FFmpegPCMAudio(path), after=lambda x: os.remove(path))
        self.voice_client.source = discord.PCMVolumeTransformer(self.voice_client.source, 1)

        await ctx.send(f"Playing: {file['title']}")

    @commands.command(pass_context=True)
    async def pause(self, ctx):
        if not ctx.author.voice:
            await ctx.send("You are not connected to a voice channel")
            return

        if self.voice_client is None:
            await ctx.send("Not currently connected to a voice channel")
            return

        if self.voice_client.is_paused():
            await ctx.send("Already paused")
            return

        self.voice_client.pause()
        await ctx.send("Paused")

    @commands.command(pass_context=True)
    async def resume(self, ctx):
        if not ctx.author.voice:
            await ctx.send("You are not connected to a voice channel")
            return

        if self.voice_client is None:
            await ctx.send("Not currently connected to a voice channel")
            return

        if not self.voice_client.is_paused():
            await ctx.send("Not paused")
            return

        self.voice_client.resume()
        await ctx.send("Resumed")