from bottoken import BOT_TOKEN
import asyncio
import discord
from discord.ext import commands
import os
import time
import asyncio
from cogs import utils
import sqlite3
import traceback

class CustomBot(commands.Bot):

    def __init__ (self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_custom = True
        self.db = None
        self.cursor = None

cmd_prefix = '$'
dbPath = './data.db'
db = sqlite3.connect(dbPath)
cursor = db.cursor()
intents = discord.Intents.default()
intents.members = True
intents.presences = True
bot = CustomBot(command_prefix=cmd_prefix, intents=intents)
bot.db = db
bot.cursor = cursor

@bot.event
async def on_ready():
    '''Startup code'''

    utils.log('Logged in as')
    utils.log(bot.user.name)
    utils.log(bot.user.id)
    utils.log('------')

@bot.event
async def on_message(message):
    pass #need to un-define the built-in on_message so it does not process

@bot.event
async def on_command_error(ctx, error):
    #Manual Error Processing

    if type(error) is commands.errors.CommandOnCooldown: #Command Cooldown is thrown as an exception. Handled here as it is universally handled
        await ctx.send(f"**{ctx.author.display_name}**, please cool down (**{error.retry_after:.0f}** seconds left)", delete_after=error.retry_after)
        return
    elif type(error) is commands.errors.CommandNotFound: #If command is not found, do nothing
        return
    elif type(error) is commands.errors.MissingPermissions: #If user is missing permissions to perform an action, send a message (only if verbose)
        return
    elif type(error) is commands.errors.NoPrivateMessage:
        await ctx.send(str(error))
        return
    elif type(error) is commands.errors.MissingRequiredArgument:
        await ctx.send(str(error))
    else:
        raise error

@bot.command(pass_context=True, hidden=True)
@utils.is_Owner()
async def adminquit(ctx):
    """Shuts down the bot"""
    await ctx.channel.send('Shutting down')

    for extension in os.listdir("cogs"): #unload all the cogs
        if extension.endswith('.py') and not extension.startswith('_'):
            try:
                bot.unload_extension("cogs." + extension[:-3])
            except (commands.errors.ExtensionNotLoaded):
                pass

    await bot.close()

@bot.command(pass_context=True, hidden=True)
@utils.is_Owner()
async def load(ctx, extension_name : str):
    """Loads an extension"""
    try:
        bot.load_extension(extension_name)
    except (AttributeError, ImportError) as e:
        await ctx.channel.send("```py\n{}: {}\n```".format(type(e).__name__, str(e)))
        return
    await ctx.channel.send("{} loaded.".format(extension_name))

@bot.command(pass_context=True, hidden=True)
@utils.is_Owner()
async def unload(ctx, extension_name : str):
    """Unloads an extension"""
    bot.unload_extension(extension_name)
    await ctx.channel.send("{} unloaded.".format(extension_name))

@bot.command(pass_context=True, hidden=True)
@utils.is_Owner()
async def reload(ctx):
    """Reloads all extensions"""

    for extension in os.listdir("cogs"):
        if extension.endswith('.py') and not extension.startswith('_'):
            try:
                bot.unload_extension("cogs." + extension[:-3])
            except commands.errors.ExtensionNotLoaded as e:
                raise e

            except Exception as e:
                utils.log('Failed to unload extension {}\n{}: {}'.format(extension, type(e).__name__, e))
                raise e

            try:
                bot.load_extension("cogs." + extension[:-3])
            except Exception as e:
                utils.log('Failed to load extension {}\n{}: {}'.format(extension, type(e).__name__, e))
                raise e
    
if __name__ == "__main__":

    bot.cursor.execute("""CREATE TABLE IF NOT EXISTS perms (RoleID int, Perms int)""")

    for extension in os.listdir("./cogs"):
        if extension.endswith('.py') and not extension.startswith('_'):
            try:
                bot.load_extension("cogs." + extension[:-3])
            except Exception as e:
                utils.log('Failed to load extension {}\n{}: {}'.format(extension, type(e).__name__, e))
                raise e

bot.max_messages=25000
bot.run(BOT_TOKEN)
utils.log("Bot has shut down")
utils.log("-----------------------------------------------------------------------")