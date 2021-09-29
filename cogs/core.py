import discord
from discord.ext import commands
import os
import time
import asyncio
from cogs import utils #pylint: disable=import-error
import sqlite3
from datetime import datetime

def setup(bot):
    bot.add_cog(Core(bot))

class Core(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        activity = discord.Game(f"Use {self.bot.command_prefix}help for more info")
        await self.bot.change_presence(activity=activity)

    @commands.Cog.listener()
    async def on_message(self, message):

        if message.content.startswith(self.bot.command_prefix) and not message.author.bot:
            #No checks here as this point is only reached if the command should be processed
            await self.bot.process_commands(message)

    @commands.command(pass_context=True, hidden=True)
    @utils.is_Owner()
    async def py(self, ctx):
        """Execute arbitrary python code
        NOTE: only enabled for approved users. Contact Ace if you would like to
        be added to the approved user list
        """

        exec(
            f'async def __ex(self, ctx): ' +
            ''.join(f'\n {l}' for l in (ctx.message.content[4:]).split('\n'))
        )

        await locals()['__ex'](self, ctx)
    @commands.command(pass_context=True)
    @commands.cooldown(3, 5, commands.BucketType.user)
    async def ping(self, ctx):
        """Calculates the ping time"""

        t_1 = time.perf_counter()
        await ctx.trigger_typing()  # tell Discord that the bot is "typing", which is a very simple request
        t_2 = time.perf_counter()
        time_delta = round((t_2-t_1)*1000)  # calculate the time needed to trigger typing
        await ctx.send(f'Pong.\nTime: {time_delta}ms')  # send a message telling the user the calculated ping time_delta