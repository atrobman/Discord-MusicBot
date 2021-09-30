import discord
from discord.ext import commands
import asyncio
import sqlite3
import os
from cogs import utils

def setup(bot):
	bot.add_cog(Help(bot))

class Help(commands.Cog):

	def __init__(self, bot):
		self.bot = bot
		self.cogs = self.bot.cogs
		self.commands = []
		self.names = []
		self.top_level_commands = []

		self.regenerate_names_list()

		self._original_help_command = self.bot.help_command
		self.bot.help_command = None

	def cog_unload(self):
		self.bot.help_command = self._original_help_command

	def regenerate_names_list(self):
		temp_commands = self.bot.commands

		sub_commands = []
		for cmd in temp_commands:
			if type(cmd) is commands.core.Group:
				sub_commands = sub_commands + list(cmd.commands)

		self.commands = list(temp_commands) + sub_commands
		self.top_level_commands = list(temp_commands)
		self.names = [cmd.qualified_name for cmd in self.commands]

		for cmd in self.commands:
			if cmd.full_parent_name != "":
				self.names = self.names + [f"{cmd.full_parent_name} {c}" for c in cmd.aliases]
			else:
				self.names = self.names + cmd.aliases

	@commands.Cog.listener()
	async def on_ready(self):
		self.regenerate_names_list()

	@commands.command(pass_context=True)
	@commands.cooldown(3, 5, commands.BucketType.user)
	async def help(self, ctx, *args):
		"""Prints this message!"""

		inp = ' '.join(args)

		if inp == '':
			#no input
			out = ""
			emb = discord.Embed(
				title="Commands for Users",
				colour=discord.Color.blurple(),
				description="Do `$help [command]` for more detailed info"
				)

			printed_cmds = []

			for name in self.cogs:
				for cmd in self.cogs[name].get_commands():
					printed_cmds.append(cmd.qualified_name)

					out = out + f"**${cmd.qualified_name}** {'' if cmd.short_doc is None else cmd.short_doc}\n"

				if out != "":
					emb.add_field(name=f"{self.cogs[name].qualified_name}", value=out, inline=False)
				out = ""

			first_pass = True

			for cmd in self.top_level_commands:

				if cmd.qualified_name not in printed_cmds:
					if first_pass:
						first_pass = False

					out = out + f"**${cmd.qualified_name}** {'' if cmd.short_doc is None else cmd.short_doc}\n"


			if not first_pass:
				emb.add_field(name="Other", value=out, inline=False)

			if type(ctx.channel) is not discord.DMChannel:
				await ctx.send("Sending help!", delete_after=10)

			await ctx.author.send(embed=emb)

		elif inp.lower() in self.names:
			cmd = discord.utils.get(self.commands, qualified_name=inp.lower())
			if not cmd: #alias
				for command in self.commands:
					if inp.lower() in command.aliases:
						cmd = command

					elif type(command) is commands.core.Group:
						cmd = discord.utils.get(command.commands, qualified_name=inp.lower())

						if not cmd:
							for c in command.commands:
								if inp.lower() in [f"{c.full_parent_name} {alias}" for alias in c.aliases]:
									cmd = c
									break

					if cmd:
						break

			emb = discord.Embed(
				title=f"{cmd.qualified_name}",
				colour=discord.Color.blurple()
				)

			emb.add_field(name="Usage", value=f"**${cmd.qualified_name}** {cmd.signature}", inline=False)
			if type(cmd) is commands.core.Group:
				s = "\n"
				emb.add_field(name="Subcommands", value=f"{s.join([c.name for c in cmd.commands])}", inline=False)
			emb.add_field(name="Description", value=f"{cmd.help}", inline=False)
			if type(ctx.channel) is not discord.DMChannel:
				await ctx.send("Sending help!", delete_after=10)
			await ctx.author.send(embed=emb)