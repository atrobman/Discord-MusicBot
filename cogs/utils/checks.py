from discord.ext import commands

def is_Owner():
    """Check to see if user is registered as the Bot owner"""
    def predicate(ctx):
        return ctx.message.author.id in [192739355264024586]
    return commands.check(predicate)

class AdvMemberConverter(commands.MemberConverter):
    """
    Augmented version of the ': discord.Member' converter syntax. Instead of throwing an error if the converter failed, it returns None.
    This is done to avoid having to handle conversion errors in on_command_erorr due to the ease at which the issue could be handled in-command
    """
    async def convert(self, ctx, argument):
        member = None
        try:
            member = await super().convert(ctx, argument)
        except:
            pass

        return member

class AdvUserConverter(commands.UserConverter):
    """
    Augmented version of the ': discord.User' converter syntax. Instead of throwing an error if the converter failed, it returns None.
    This is done to avoid having to handle conversion errors in on_command_erorr due to the ease at which the issue could be handled in-command
    """
    async def convert(self, ctx, argument):
        user = None
        try:
            user = await super().convert(ctx, argument)
        except:
            pass

        return user

class AdvTextChannelConverter(commands.TextChannelConverter):
    """
    Augmented version of the ': discord.TextChannel' converter syntax. Instead of throwing an error it the converter failed, it returns None.
    This is done to avoid having to handle conversion errors in on_command_error due to the ease at which the issue could be handled in command
    """
    async def convert(self, ctx, argument):
        textChannel = None
        try:
            textChannel = await super().convert(ctx, argument)
        except:
            pass

        return textChannel

class AdvRoleConverter(commands.RoleConverter):
    """
    Augmented version of the ': discord.Role' converter syntax. Instead of throwing an error it the converter failed, it returns None.
    This is done to avoid having to handle conversion errors in on_command_error due to the ease at which the issue could be handled in command
    """
    async def convert(self, ctx, argument):
        role = None
        try:
            role = await super().convert(ctx, argument)
        except:
            pass

        return role